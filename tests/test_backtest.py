import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest.engine import BacktestEngine
from backtest.report import BacktestReport
import pandas as pd
import numpy as np
import tempfile


class TestBacktestEngine(unittest.TestCase):
    def test_backtest_basic(self):
        engine = BacktestEngine(initial_cash=600000)
        dates = pd.date_range("2024-01-01", periods=252, freq="B")
        np.random.seed(42)
        prices = 3000 + np.cumsum(np.random.randn(252) * 20)
        df = pd.DataFrame({"close": prices}, index=dates)
        df["open"] = df["close"].shift(1).fillna(df["close"])
        df["high"] = df["close"] * 1.01
        df["low"] = df["close"] * 0.99
        df["volume"] = 5000

        results = engine.run(df, strategy="ma_cross")
        self.assertIn("annual_return", results)
        self.assertIn("max_drawdown", results)
        self.assertIn("sharpe_ratio", results)
        self.assertIn("win_rate", results)


class TestBacktestReport(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = BacktestReport(tmpdir)
            results = {
                "annual_return": 0.12,
                "max_drawdown": -0.08,
                "sharpe_ratio": 1.5,
                "win_rate": 0.68,
                "profit_loss_ratio": 2.0,
                "total_trades": 24,
            }
            report.save_results(results)
            loaded = report.load_results()
            self.assertEqual(loaded["annual_return"], 0.12)
            self.assertIn("last_updated", loaded)

    def test_format_summary(self):
        report = BacktestReport()
        summary = report.format_summary({
            "annual_return": 0.12, "max_drawdown": -0.08,
            "sharpe_ratio": 1.5, "win_rate": 0.68,
            "profit_loss_ratio": 2.0, "total_trades": 24
        })
        self.assertIn("年化收益率", summary)


if __name__ == "__main__":
    unittest.main()
