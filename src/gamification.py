"""
游戏化引擎 - 等级、成就、任务系统
让资产配置像玩游戏一样有趣
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent.parent / "data"

LEVELS = [
    {"level": 1, "name": "投资新手", "min_xp": 0, "icon": "🌱"},
    {"level": 2, "name": "理财学徒", "min_xp": 100, "icon": "📚"},
    {"level": 3, "name": "资产配置师", "min_xp": 300, "icon": "📊"},
    {"level": 4, "name": "量化交易员", "min_xp": 600, "icon": "📈"},
    {"level": 5, "name": "投资大师", "min_xp": 1000, "icon": "🏆"},
]

ACHIEVEMENTS = [
    {"id": "first_config", "name": "初次配置", "desc": "完成首次资产配置", "xp": 50, "icon": "🎯"},
    {"id": "first_trade", "name": "首次交易", "desc": "执行第一次基金操作", "xp": 30, "icon": "💰"},
    {"id": "dca_4weeks", "name": "定投达人", "desc": "连续4周执行定投", "xp": 100, "icon": "📅"},
    {"id": "dca_12weeks", "name": "定投大师", "desc": "连续12周执行定投", "xp": 200, "icon": "🌟"},
    {"id": "backtest_win", "name": "回测胜者", "desc": "策略回测胜率超过60%", "xp": 80, "icon": "🏅"},
    {"id": "rebalance", "name": "再平衡", "desc": "完成一次资产再平衡", "xp": 60, "icon": "⚖️"},
    {"id": "profit_10pct", "name": "盈利10%", "desc": "总资产盈利超过10%", "xp": 150, "icon": "🚀"},
    {"id": "risk_master", "name": "风控达人", "desc": "最大回撤控制在5%以内", "xp": 120, "icon": "🛡️"},
    {"id": "diversified", "name": "分散投资", "desc": "持有5种以上不同类型基金", "xp": 70, "icon": "🌐"},
    {"id": "patient", "name": "耐心持有", "desc": "单只基金持有超过365天", "xp": 90, "icon": "⏳"},
]

WEEKLY_TASKS = [
    {"id": "check_portfolio", "name": "检查持仓", "desc": "查看当前持仓状态", "xp": 10},
    {"id": "execute_dca", "name": "执行定投", "desc": "按计划执行本周定投", "xp": 20},
    {"id": "review_report", "name": "查看报告", "desc": "阅读周度回测报告", "xp": 15},
    {"id": "check_signals", "name": "检查信号", "desc": "查看最新交易信号", "xp": 10},
    {"id": "update_strategy", "name": "更新策略", "desc": "检查并更新投资策略", "xp": 10},
]

# 资产配置目标（总资产60万，平衡型配置）
ALLOCATION_TARGET = {
    "total_assets": 600000,
    "allocation": {
        "A股指数基金": {"target_pct": 25, "current_pct": 20, "funds": ["易方达沪深300联接A", "南方中证500联接A"]},
        "海外指数基金": {"target_pct": 20, "current_pct": 15, "funds": ["广发纳指100联接A", "博时标普500联接A"]},
        "黄金ETF": {"target_pct": 10, "current_pct": 10, "funds": ["华安黄金ETF"]},
        "债券基金": {"target_pct": 30, "current_pct": 35, "funds": ["易方达中短期美元债A"]},
        "货币基金": {"target_pct": 5, "current_pct": 10, "funds": ["余额宝"]},
        "行业主题基金": {"target_pct": 10, "current_pct": 10, "funds": ["工银前沿医疗股票A"]},
    }
}


class GamificationEngine:
    """游戏化引擎核心类"""

    def __init__(self):
        self.state_file = DATA_DIR / "game_state.json"
        self.state = self._load_state()

    def _load_state(self):
        """加载游戏状态"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "xp": 0,
            "level": 1,
            "achievements": [],
            "weekly_tasks_completed": [],
            "current_streak": 0,
            "last_active_date": None,
            "total_trades": 0,
            "dca_streak": 0,
            "history": [],
            "allocation_progress": 0,
            "total_assets": 600000,
            "target_assets": 600000,
        }

    def _save_state(self):
        """保存游戏状态"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def add_xp(self, amount, reason=""):
        """增加经验值"""
        self.state["xp"] += amount
        self.state["history"].append({
            "date": datetime.now().isoformat(),
            "xp": amount,
            "reason": reason,
        })
        # 保留最近50条历史
        if len(self.state["history"]) > 50:
            self.state["history"] = self.state["history"][-50:]
        self._update_level()
        self._save_state()

    def _update_level(self):
        """更新等级"""
        for lvl in reversed(LEVELS):
            if self.state["xp"] >= lvl["min_xp"]:
                self.state["level"] = lvl["level"]
                break

    def get_level_info(self):
        """获取当前等级信息"""
        for lvl in reversed(LEVELS):
            if self.state["xp"] >= lvl["min_xp"]:
                return lvl
        return LEVELS[0]

    def get_next_level(self):
        """获取下一等级信息"""
        current = self.get_level_info()
        idx = LEVELS.index(current)
        if idx < len(LEVELS) - 1:
            return LEVELS[idx + 1]
        return None

    def unlock_achievement(self, achievement_id):
        """解锁成就"""
        if achievement_id not in self.state["achievements"]:
            for ach in ACHIEVEMENTS:
                if ach["id"] == achievement_id:
                    self.state["achievements"].append(achievement_id)
                    self.add_xp(ach["xp"], f"解锁成就: {ach['name']}")
                    return ach
        return None

    def complete_task(self, task_id):
        """完成每周任务"""
        today = datetime.now().strftime("%Y-%W")
        key = f"{today}_{task_id}"
        if key not in self.state["weekly_tasks_completed"]:
            self.state["weekly_tasks_completed"].append(key)
            # 保留最近20条
            if len(self.state["weekly_tasks_completed"]) > 20:
                self.state["weekly_tasks_completed"] = self.state["weekly_tasks_completed"][-20:]
            for task in WEEKLY_TASKS:
                if task["id"] == task_id:
                    self.add_xp(task["xp"], f"完成任务: {task['name']}")
                    return task
        return None

    def get_pending_tasks(self):
        """获取待完成的每周任务"""
        today = datetime.now().strftime("%Y-%W")
        pending = []
        for task in WEEKLY_TASKS:
            key = f"{today}_{task['id']}"
            if key not in self.state["weekly_tasks_completed"]:
                pending.append(task)
        return pending

    def update_streak(self):
        """更新连续活跃天数"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.state["last_active_date"] == today:
            return
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if self.state["last_active_date"] == yesterday:
            self.state["current_streak"] += 1
        else:
            self.state["current_streak"] = 1
        self.state["last_active_date"] = today
        self._save_state()

    def record_trade(self):
        """记录一笔交易"""
        self.state["total_trades"] += 1
        self._save_state()
        # 自动检查成就
        if self.state["total_trades"] == 1:
            self.unlock_achievement("first_trade")

    def record_dca(self):
        """记录一次定投"""
        self.state["dca_streak"] += 1
        self._save_state()
        # 检查定投成就
        if self.state["dca_streak"] >= 4:
            self.unlock_achievement("dca_4weeks")
        if self.state["dca_streak"] >= 12:
            self.unlock_achievement("dca_12weeks")

    def get_all_achievements(self):
        """获取所有成就（含解锁状态）"""
        unlocked = set(self.state["achievements"])
        return [
            {**ach, "unlocked": ach["id"] in unlocked}
            for ach in ACHIEVEMENTS
        ]

    def get_allocation_progress(self):
        """计算资产配置完成度"""
        target = ALLOCATION_TARGET["allocation"]
        total_deviation = 0
        categories = []

        for name, info in target.items():
            deviation = abs(info["current_pct"] - info["target_pct"])
            total_deviation += deviation
            categories.append({
                "name": name,
                "target_pct": info["target_pct"],
                "current_pct": info["current_pct"],
                "deviation": deviation,
                "funds": info["funds"],
                "status": "达标" if deviation <= 3 else "需调整",
            })

        # 完成度 = 100 - 总偏差/2
        progress = max(0, min(100, 100 - total_deviation / 2))
        self.state["allocation_progress"] = round(progress, 1)
        self._save_state()

        return {
            "progress": round(progress, 1),
            "categories": categories,
            "total_deviation": total_deviation,
        }

    def check_auto_achievements(self, backtest_data=None):
        """根据数据自动检查成就"""
        # 回测胜率成就
        if backtest_data:
            win_rate = backtest_data.get("win_rate", 0)
            if win_rate > 60:
                self.unlock_achievement("backtest_win")

            max_drawdown = abs(backtest_data.get("max_drawdown", 0))
            if max_drawdown < 5:
                self.unlock_achievement("risk_master")

        # 首次配置成就
        if self.state["allocation_progress"] > 0:
            self.unlock_achievement("first_config")

    def to_dict(self):
        """导出完整状态为字典（用于JSON序列化）"""
        level_info = self.get_level_info()
        next_level = self.get_next_level()
        allocation = self.get_allocation_progress()

        return {
            "level": level_info,
            "next_level": next_level,
            "xp": self.state["xp"],
            "xp_progress": self.state["xp"] - level_info["min_xp"],
            "xp_needed": (next_level["min_xp"] - level_info["min_xp"]) if next_level else 0,
            "achievements": self.get_all_achievements(),
            "pending_tasks": self.get_pending_tasks(),
            "streak": self.state["current_streak"],
            "total_trades": self.state["total_trades"],
            "dca_streak": self.state["dca_streak"],
            "allocation": allocation,
            "total_assets": self.state["total_assets"],
            "target_assets": self.state["target_assets"],
            "last_active": self.state["last_active_date"],
            "recent_history": self.state["history"][-10:],
        }


if __name__ == "__main__":
    engine = GamificationEngine()
    engine.update_streak()
    engine.add_xp(10, "每日签到")
    state = engine.to_dict()
    print(json.dumps(state, ensure_ascii=False, indent=2))
