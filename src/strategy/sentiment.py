"""市场情绪分析模块"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """市场情绪分析器"""

    EXTREME_FEAR = 20
    FEAR = 40
    NEUTRAL_HIGH = 60
    GREED = 80

    WEIGHTS = {
        "north_flow": 0.30,
        "margin_change": 0.25,
        "vix": 0.20,
        "volume_ratio": 0.15,
        "new_accounts": 0.10,
    }

    def calculate_score(self, indicators: Dict[str, float]) -> Dict:
        scores = {}

        north = indicators.get("north_flow", 0)
        if north > 100:
            scores["north_flow"] = 80
        elif north > 50:
            scores["north_flow"] = 65
        elif north > 0:
            scores["north_flow"] = 55
        elif north > -50:
            scores["north_flow"] = 40
        else:
            scores["north_flow"] = 20

        margin = indicators.get("margin_change", 0)
        if margin > 0.03:
            scores["margin_change"] = 75
        elif margin > 0:
            scores["margin_change"] = 60
        elif margin > -0.02:
            scores["margin_change"] = 45
        else:
            scores["margin_change"] = 25

        vix = indicators.get("vix", 20)
        if vix < 15:
            scores["vix"] = 80
        elif vix < 20:
            scores["vix"] = 65
        elif vix < 30:
            scores["vix"] = 45
        else:
            scores["vix"] = 20

        vol_ratio = indicators.get("volume_ratio", 1.0)
        if vol_ratio > 1.5:
            scores["volume_ratio"] = 70
        elif vol_ratio > 1.0:
            scores["volume_ratio"] = 55
        elif vol_ratio > 0.7:
            scores["volume_ratio"] = 40
        else:
            scores["volume_ratio"] = 25

        new_acc = indicators.get("new_accounts", 150000)
        if new_acc > 300000:
            scores["new_accounts"] = 75
        elif new_acc > 200000:
            scores["new_accounts"] = 60
        elif new_acc > 100000:
            scores["new_accounts"] = 45
        else:
            scores["new_accounts"] = 25

        total_score = sum(
            self.WEIGHTS.get(k, 0) * v for k, v in scores.items()
        )

        if total_score <= self.EXTREME_FEAR:
            level = "极度恐慌"
            suggestion = "市场极度恐慌，建议逆向加仓"
        elif total_score <= self.FEAR:
            level = "偏悲观"
            suggestion = "市场偏悲观，维持当前仓位"
        elif total_score <= self.NEUTRAL_HIGH:
            level = "中性"
            suggestion = "市场情绪中性，正常操作"
        elif total_score <= self.GREED:
            level = "偏乐观"
            suggestion = "市场偏乐观，适度减仓"
        else:
            level = "极度贪婪"
            suggestion = "市场极度贪婪，建议减仓"

        return {
            "score": round(total_score, 1),
            "level": level,
            "suggestion": suggestion,
            "details": scores,
        }
