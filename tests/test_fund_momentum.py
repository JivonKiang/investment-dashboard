import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy.fund_momentum import FundMomentumStrategy


class TestFundMomentumStrategy(unittest.TestCase):
    def test_calculate_momentum_score(self):
        strategy = FundMomentumStrategy()
        score = strategy.calculate_momentum_score(
            return_3m=0.05, return_6m=0.10, return_12m=0.15
        )
        self.assertAlmostEqual(score, 0.085, places=4)

    def test_generate_signals(self):
        strategy = FundMomentumStrategy()
        mock_data = {
            "hs300": {"return_3m": 0.03, "return_6m": 0.08, "return_12m": 0.12, "pe_percentile": 40},
            "zz500": {"return_3m": 0.06, "return_6m": 0.15, "return_12m": 0.20, "pe_percentile": 30},
            "nasdaq100": {"return_3m": 0.10, "return_6m": 0.18, "return_12m": 0.25, "pe_percentile": 60},
            "sp500": {"return_3m": 0.04, "return_6m": 0.09, "return_12m": 0.14, "pe_percentile": 50},
            "gold": {"return_3m": 0.02, "return_6m": 0.05, "return_12m": 0.08, "pe_percentile": 45},
            "bond": {"return_3m": 0.01, "return_6m": 0.03, "return_12m": 0.05, "pe_percentile": 20},
        }
        signals = strategy.generate_signals(mock_data)
        self.assertIsInstance(signals, list)
        self.assertGreater(len(signals), 0)
        top_signal = signals[0]
        self.assertIn("action", top_signal)
        self.assertIn("weight", top_signal)


if __name__ == "__main__":
    unittest.main()
