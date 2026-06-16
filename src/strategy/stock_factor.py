"""多因子选股策略"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class MultiFactorStrategy:
    """多因子选股策略

    基于 PE、PB、ROE、营收增速、动量、波动率等因子
    从沪深300成分股中筛选优质个股。
    """

    FACTOR_WEIGHTS = {
        "pe": 0.20,
        "pb": 0.15,
        "roe": 0.20,
        "revenue_growth": 0.20,
        "momentum_3m": 0.15,
        "volatility": 0.10,
    }

    FACTOR_RANGES = {
        "pe": {"good": 10, "bad": 50},
        "pb": {"good": 0.8, "bad": 5.0},
        "roe": {"good": 0.25, "bad": 0.05},
        "revenue_growth": {"good": 0.30, "bad": -0.05},
        "momentum_3m": {"good": 0.20, "bad": -0.10},
        "volatility": {"good": 0.15, "bad": 0.40},
    }

    def _normalize_factor(self, factor_name: str, value: float) -> float:
        ranges = self.FACTOR_RANGES[factor_name]
        good, bad = ranges["good"], ranges["bad"]
        inverse_factors = {"pe", "pb", "volatility"}
        if factor_name in inverse_factors:
            if value <= good:
                return 100
            elif value >= bad:
                return 0
            else:
                return 100 * (bad - value) / (bad - good)
        else:
            if value >= good:
                return 100
            elif value <= bad:
                return 0
            else:
                return 100 * (value - bad) / (good - bad)

    def calculate_composite_score(self, factors: Dict[str, float]) -> float:
        total_score = 0
        for factor_name, weight in self.FACTOR_WEIGHTS.items():
            value = factors.get(factor_name, 0)
            normalized = self._normalize_factor(factor_name, value)
            total_score += weight * normalized
        return round(total_score, 2)

    def rank_stocks(self, stocks: List[Dict], top_n: int = 10) -> List[Dict]:
        for stock in stocks:
            factors = {
                "pe": stock.get("pe", 30),
                "pb": stock.get("pb", 3),
                "roe": stock.get("roe", 0.10),
                "revenue_growth": stock.get("revenue_growth", 0),
                "momentum_3m": stock.get("momentum_3m", 0),
                "volatility": stock.get("volatility", 0.30),
            }
            stock["composite_score"] = self.calculate_composite_score(factors)
        ranked = sorted(stocks, key=lambda x: x["composite_score"], reverse=True)
        return ranked[:top_n]
