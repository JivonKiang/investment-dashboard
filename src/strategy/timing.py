"""技术指标择时策略"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TimingStrategy:
    """大盘择时策略"""

    MIN_EQUITY_PCT = 0.30
    MAX_EQUITY_PCT = 0.70
    NEUTRAL_EQUITY_PCT = 0.50

    def generate_signal(
        self,
        current_price: float,
        ma20: float,
        volume: float,
        volume_ma20: float,
        rsi: float = 50,
        macd_hist: float = 0,
    ) -> Dict:
        bullish_signals = 0
        bearish_signals = 0
        reasons = []

        if current_price > ma20:
            bullish_signals += 1
            reasons.append(f"价格({current_price:.0f})在20日均线上方({ma20:.0f})")
        else:
            bearish_signals += 1
            reasons.append(f"价格({current_price:.0f})在20日均线下方({ma20:.0f})")

        if volume > volume_ma20:
            bullish_signals += 1
            reasons.append(f"成交量放量({volume:.0f} > {volume_ma20:.0f})")
        else:
            bearish_signals += 1
            reasons.append(f"成交量萎缩({volume:.0f} < {volume_ma20:.0f})")

        if rsi < 30:
            bullish_signals += 1
            reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi > 70:
            bearish_signals += 1
            reasons.append(f"RSI超买({rsi:.1f})")

        if macd_hist > 0:
            bullish_signals += 1
            reasons.append("MACD柱状图为正")
        elif macd_hist < 0:
            bearish_signals += 1
            reasons.append("MACD柱状图为负")

        total = bullish_signals + bearish_signals
        if total == 0:
            direction = "neutral"
            strength = 0.5
        elif bullish_signals > bearish_signals:
            direction = "bullish"
            strength = bullish_signals / total
        elif bearish_signals > bullish_signals:
            direction = "bearish"
            strength = bearish_signals / total
        else:
            direction = "neutral"
            strength = 0.5

        return {
            "direction": direction,
            "strength": round(strength, 2),
            "reason": "; ".join(reasons),
        }

    def calculate_position(self, direction: str, current_equity_pct: float) -> float:
        if direction == "bullish":
            target = min(self.MAX_EQUITY_PCT, current_equity_pct + 0.10)
        elif direction == "bearish":
            target = max(self.MIN_EQUITY_PCT, current_equity_pct - 0.10)
        else:
            target = self.NEUTRAL_EQUITY_PCT
        return round(target, 2)
