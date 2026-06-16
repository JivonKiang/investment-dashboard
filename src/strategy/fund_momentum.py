"""基金动量轮动策略"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class FundMomentumStrategy:
    """基金动量轮动策略

    每月评估各类基金标的动量，动态调整配置权重。
    """

    WEIGHT_3M = 0.5
    WEIGHT_6M = 0.3
    WEIGHT_12M = 0.2
    PE_PERCENTILE_THRESHOLD = 70
    MAX_SINGLE_WEIGHT = 0.20
    OVERWEIGHT_TOP_N = 3
    UNDERWEIGHT_NEXT_N = 2

    def calculate_momentum_score(
        self, return_3m: float, return_6m: float, return_12m: float
    ) -> float:
        return (
            self.WEIGHT_3M * return_3m
            + self.WEIGHT_6M * return_6m
            + self.WEIGHT_12M * return_12m
        )

    def generate_signals(self, fund_data: Dict[str, Dict]) -> List[Dict]:
        scored = []
        for name, data in fund_data.items():
            score = self.calculate_momentum_score(
                data["return_3m"], data["return_6m"], data["return_12m"]
            )
            scored.append({
                "name": name,
                "momentum_score": score,
                "pe_percentile": data.get("pe_percentile", 50),
                "return_3m": data["return_3m"],
                "return_6m": data["return_6m"],
                "return_12m": data["return_12m"],
            })

        scored.sort(key=lambda x: x["momentum_score"], reverse=True)

        signals = []
        for i, item in enumerate(scored):
            if i < self.OVERWEIGHT_TOP_N:
                weight = min(self.MAX_SINGLE_WEIGHT, 0.60 / self.OVERWEIGHT_TOP_N)
                if item["pe_percentile"] > self.PE_PERCENTILE_THRESHOLD:
                    weight *= 0.7
                    reason = f"动量排名第{i+1}（评分{item['momentum_score']:.2%}），但估值偏高（PE分位{item['pe_percentile']}%），适度降低权重"
                else:
                    reason = f"动量排名第{i+1}（评分{item['momentum_score']:.2%}），估值合理（PE分位{item['pe_percentile']}%），建议超配"
                action = "overweight"
            elif i < self.OVERWEIGHT_TOP_N + self.UNDERWEIGHT_NEXT_N:
                weight = 0.10
                reason = f"动量排名第{i+1}（评分{item['momentum_score']:.2%}），维持低配"
                action = "underweight"
            else:
                weight = 0.02
                reason = f"动量排名第{i+1}（评分{item['momentum_score']:.2%}），动量较弱，建议清仓"
                action = "sell"

            signals.append({
                "name": item["name"],
                "action": action,
                "weight": round(weight, 4),
                "momentum_score": round(item["momentum_score"], 4),
                "pe_percentile": item["pe_percentile"],
                "reason": reason,
            })

        return signals
