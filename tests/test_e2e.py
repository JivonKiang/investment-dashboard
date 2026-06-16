"""端到端测试 - 验证完整流程"""
import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.cache import DataCache
from src.strategy.fund_momentum import FundMomentumStrategy
from src.strategy.stock_factor import MultiFactorStrategy
from src.strategy.timing import TimingStrategy
from src.strategy.sentiment import SentimentAnalyzer
from src.backtest.engine import BacktestEngine
from src.backtest.report import BacktestReport
from src.report.html_generator import DashboardGenerator
from src.report.email_generator import EmailGenerator
import tempfile


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_full_pipeline(self):
        """测试完整流程：策略分析 → 回测 → 面板生成 → 邮件生成"""
        # 1. 策略分析
        momentum = FundMomentumStrategy()
        fund_data = {
            "hs300": {"return_3m": 0.05, "return_6m": 0.10, "return_12m": 0.15, "pe_percentile": 40},
            "zz500": {"return_3m": 0.06, "return_6m": 0.12, "return_12m": 0.18, "pe_percentile": 35},
            "nasdaq100": {"return_3m": 0.08, "return_6m": 0.15, "return_12m": 0.22, "pe_percentile": 55},
            "sp500": {"return_3m": 0.03, "return_6m": 0.07, "return_12m": 0.12, "pe_percentile": 50},
            "gold": {"return_3m": 0.02, "return_6m": 0.04, "return_12m": 0.08, "pe_percentile": 45},
            "bond": {"return_3m": 0.01, "return_6m": 0.02, "return_12m": 0.04, "pe_percentile": 20},
        }
        fund_signals = momentum.generate_signals(fund_data)
        self.assertGreater(len(fund_signals), 0)

        # 2. 择时
        timing = TimingStrategy()
        timing_signal = timing.generate_signal(3200, 3100, 5000, 4500)
        self.assertEqual(timing_signal["direction"], "bullish")

        # 3. 情绪
        sentiment = SentimentAnalyzer()
        sentiment_result = sentiment.calculate_score({
            "north_flow": 50, "margin_change": 0.01, "vix": 18,
            "volume_ratio": 1.1, "new_accounts": 200000
        })
        self.assertIn("score", sentiment_result)

        # 4. 回测
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2024-01-01", periods=252, freq="B")
        np.random.seed(42)
        prices = 3000 + np.cumsum(np.random.randn(252) * 20)
        df = pd.DataFrame({"close": prices}, index=dates)
        df["open"] = df["close"].shift(1).fillna(df["close"])
        df["high"] = df["close"] * 1.01
        df["low"] = df["close"] * 0.99
        df["volume"] = 5000

        engine = BacktestEngine(initial_cash=600000)
        backtest_results = engine.run(df, strategy="ma_cross")
        self.assertIn("annual_return", backtest_results)

        # 5. 保存回测结果
        report = BacktestReport(self.tmpdir)
        report.save_results(backtest_results)
        loaded = report.load_results()
        self.assertEqual(loaded["annual_return"], backtest_results["annual_return"])

        # 6. 生成面板
        dashboard_gen = DashboardGenerator()
        html = dashboard_gen.generate({
            "date": "2026-06-16",
            "total_assets": 600000,
            "daily_pnl": 2340,
            "daily_pnl_pct": 0.0039,
            "updated_at": "2026-06-16 14:30:00",
            "signals": [
                {"action": "buy", "name": "沪深300", "amount": 120000, "channel": "alipay",
                 "channel_label": "支付宝", "reason": "动量排名第1", "win_rate": 0.68, "momentum_score": 0.085}
            ],
            "backtest": backtest_results,
            "sentiment": sentiment_result,
            "allocation_labels": ["A股指数", "海外指数", "黄金", "债券", "货币", "个股"],
            "allocation_values": [25, 10, 10, 30, 5, 20],
        })
        self.assertIn("投资面板", html)
        self.assertIn("沪深300", html)

        # 7. 生成邮件
        email_gen = EmailGenerator()
        email = email_gen.generate({
            "date": "2026-06-16",
            "conclusion": "今日建议加仓",
            "signals": [],
            "backtest": backtest_results,
        })
        self.assertIn("投资面板", email["subject"])
        self.assertIn("今日结论", email["html"])


if __name__ == "__main__":
    unittest.main()
