import unittest
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from strategy.timing import TimingStrategy
from strategy.sentiment import SentimentAnalyzer


class TestTimingStrategy(unittest.TestCase):
    def test_ma_cross_signal_bullish(self):
        strategy = TimingStrategy()
        signal = strategy.generate_signal(
            current_price=3200, ma20=3100, volume=5000, volume_ma20=4500
        )
        self.assertEqual(signal["direction"], "bullish")

    def test_ma_cross_signal_bearish(self):
        strategy = TimingStrategy()
        signal = strategy.generate_signal(
            current_price=3000, ma20=3100, volume=4000, volume_ma20=4500
        )
        self.assertEqual(signal["direction"], "bearish")

    def test_position_sizing(self):
        strategy = TimingStrategy()
        position = strategy.calculate_position(
            direction="bullish", current_equity_pct=0.50
        )
        self.assertGreater(position, 0.50)
        self.assertLessEqual(position, 0.70)


class TestSentimentAnalyzer(unittest.TestCase):
    def test_calculate_score(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.calculate_score({
            "north_flow": 50, "margin_change": 0.01, "vix": 18,
            "volume_ratio": 1.1, "new_accounts": 200000
        })
        self.assertIn("score", result)
        self.assertIn("level", result)
        self.assertIn("suggestion", result)
        self.assertGreater(result["score"], 0)
        self.assertLessEqual(result["score"], 100)


if __name__ == "__main__":
    unittest.main()
