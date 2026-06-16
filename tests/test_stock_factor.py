import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy.stock_factor import MultiFactorStrategy


class TestMultiFactorStrategy(unittest.TestCase):
    def test_calculate_composite_score(self):
        strategy = MultiFactorStrategy()
        factors = {
            "pe": 15.0, "pb": 1.2, "roe": 0.20,
            "revenue_growth": 0.15, "momentum_3m": 0.08, "volatility": 0.20,
        }
        score = strategy.calculate_composite_score(factors)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_rank_stocks(self):
        strategy = MultiFactorStrategy()
        mock_stocks = [
            {"code": "600519", "name": "贵州茅台", "pe": 25, "pb": 8, "roe": 0.30, "revenue_growth": 0.15, "momentum_3m": 0.05, "volatility": 0.25},
            {"code": "000858", "name": "五粮液", "pe": 20, "pb": 5, "roe": 0.25, "revenue_growth": 0.12, "momentum_3m": 0.08, "volatility": 0.22},
            {"code": "601318", "name": "中国平安", "pe": 8, "pb": 1.0, "roe": 0.15, "revenue_growth": 0.10, "momentum_3m": 0.03, "volatility": 0.18},
        ]
        ranked = strategy.rank_stocks(mock_stocks, top_n=2)
        self.assertEqual(len(ranked), 2)
        self.assertIn("composite_score", ranked[0])


if __name__ == "__main__":
    unittest.main()
