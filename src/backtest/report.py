"""回测报告生成"""
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class BacktestReport:
    """回测报告管理"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR

    def save_results(self, results: dict):
        results["last_updated"] = datetime.now().isoformat()
        filepath = self.data_dir / "backtest_results.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"回测结果已保存到 {filepath}")

    def load_results(self) -> dict:
        filepath = self.data_dir / "backtest_results.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def format_summary(self, results: dict) -> str:
        if not results:
            return "暂无回测数据"
        return (
            f"年化收益率: {results.get('annual_return', 0):.2%}\n"
            f"最大回撤: {results.get('max_drawdown', 0):.2%}\n"
            f"夏普比率: {results.get('sharpe_ratio', 0):.2f}\n"
            f"胜率: {results.get('win_rate', 0):.2%}\n"
            f"盈亏比: {results.get('profit_loss_ratio', 0):.2f}\n"
            f"总交易次数: {results.get('total_trades', 0)}"
        )
