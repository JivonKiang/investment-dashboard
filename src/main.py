"""
游戏化资产配置专家 - 整合版主入口
融合 investment-dashboard + fund-trend-system + nasdaq-dca 精华

支持模式：
  --mode full-analysis       完整分析（数据采集+策略+回测+游戏化+面板生成）
  --mode generate-dashboard  生成HTML面板（从缓存数据）
  --mode send-email           发送邮件推送
  --mode quick-update         快速更新面板
  --mode backtest             运行回测
  --mode update-game          更新游戏化状态
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_json(filename):
    """从data目录加载JSON文件"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filename, data):
    """保存JSON到data目录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_backtest_summary():
    """加载回测汇总数据"""
    return load_json("backtest_summary.json")


def load_nasdaq_cache():
    """加载纳斯达克缓存数据"""
    return load_json("nasdaq_cache.json")


def load_index_backtest():
    """加载指数回测数据"""
    return load_json("index_backtest_summary.json")


def load_game_state():
    """加载游戏化状态"""
    try:
        from src.gamification import GamificationEngine
        engine = GamificationEngine()
        engine.update_streak()
        return engine.to_dict()
    except Exception as e:
        logger.warning(f"加载游戏化状态失败: {e}")
        return {}


def run_full_analysis():
    """运行完整分析（盘前）"""
    logger.info("=" * 60)
    logger.info("开始完整分析...")
    logger.info("=" * 60)

    # 1. 初始化游戏化引擎
    logger.info("[1/5] 初始化游戏化引擎...")
    try:
        from src.gamification import GamificationEngine
        game = GamificationEngine()
        game.update_streak()
        game.add_xp(5, "执行完整分析")
    except Exception as e:
        logger.warning(f"游戏化引擎初始化失败: {e}")
        game = None

    # 2. 加载回测数据（从缓存）
    logger.info("[2/5] 加载回测数据...")
    backtest_summary = load_backtest_summary()
    index_backtest = load_index_backtest()
    nasdaq_cache = load_nasdaq_cache()

    # 3. 运行趋势策略分析（如果数据可用）
    logger.info("[3/5] 运行趋势策略分析...")
    trend_signals = []
    try:
        from src.engine.decision import DecisionEngine
        decision = DecisionEngine()
        decisions = decision.daily_run(save_signals=False)
        for d in decisions:
            if d.get("should_execute"):
                trend_signals.append(d)
        logger.info(f"趋势策略生成 {len(trend_signals)} 条可执行信号")
    except Exception as e:
        logger.warning(f"趋势策略分析失败（可能缺少数据库）: {e}")

    # 4. 纳斯达克PE分析
    logger.info("[4/5] 分析纳斯达克PE估值...")
    nasdaq_pe = 0
    nasdaq_grade = "未知"
    nasdaq_suggestion = "无数据"
    pe_history = []

    if nasdaq_cache:
        nasdaq_pe = nasdaq_cache.get("pe", 0)
        pe_grade = nasdaq_cache.get("peGrade", {})
        nasdaq_grade = pe_grade.get("name", "未知")
        pe_history = nasdaq_cache.get("historicalPE", [])

        if nasdaq_pe > 0:
            if nasdaq_pe < 25:
                nasdaq_suggestion = f"PE={nasdaq_pe:.1f} 估值偏低，建议加倍定投纳指基金"
            elif nasdaq_pe < 35:
                nasdaq_suggestion = f"PE={nasdaq_pe:.1f} 估值正常，正常定投纳指基金"
            elif nasdaq_pe < 40:
                nasdaq_suggestion = f"PE={nasdaq_pe:.1f} 估值偏高，建议减半定投纳指基金"
            else:
                nasdaq_suggestion = f"PE={nasdaq_pe:.1f} 估值严重偏高，建议暂停定投纳指基金"

    # 5. 生成操作建议
    logger.info("[5/5] 生成操作建议...")

    # 综合信号
    signals_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "trend_signals": trend_signals,
        "nasdaq_pe": nasdaq_pe,
        "nasdaq_grade": nasdaq_grade,
        "nasdaq_suggestion": nasdaq_suggestion,
        "pe_history": pe_history,
    }
    save_json("latest_signals.json", signals_data)

    # 更新游戏化成就
    if game and index_backtest:
        best_win_rate = 0
        for idx_name, idx_data in index_backtest.items():
            wr = idx_data.get("win_rate", 0)
            if wr > best_win_rate:
                best_win_rate = wr
        game.check_auto_achievements({"win_rate": best_win_rate})

    logger.info("完整分析完成!")
    return signals_data


def generate_dashboard():
    """生成游戏化HTML面板"""
    logger.info("生成游戏化投资面板...")

    # 加载所有数据
    backtest_summary = load_backtest_summary()
    nasdaq_cache = load_nasdaq_cache()
    index_backtest = load_index_backtest()
    game_state = load_game_state()

    # 读取index.html模板并注入数据
    index_html_path = PROJECT_ROOT / "index.html"
    if not index_html_path.exists():
        logger.error("index.html 模板不存在")
        return

    with open(index_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 构建GAME_DATA
    game_data = {
        "level": game_state.get("level", {"level": 1, "name": "投资新手", "icon": "🌱", "min_xp": 0}),
        "nextLevel": game_state.get("next_level", {"level": 2, "name": "理财学徒", "icon": "📚", "min_xp": 100}),
        "xp": game_state.get("xp", 0),
        "xpProgress": game_state.get("xp_progress", 0),
        "xpNeeded": game_state.get("xp_needed", 100),
        "streak": game_state.get("streak", 0),
        "totalTrades": game_state.get("total_trades", 0),
        "dcaStreak": game_state.get("dca_streak", 0),
        "achievements": game_state.get("achievements", []),
        "pendingTasks": game_state.get("pending_tasks", []),
        "allocation": game_state.get("allocation", {
            "progress": 72.5,
            "categories": [
                {"name": "A股指数基金", "target_pct": 25, "current_pct": 20, "funds": ["易方达沪深300联接A", "南方中证500联接A"], "status": "需调整"},
                {"name": "海外指数基金", "target_pct": 20, "current_pct": 15, "funds": ["广发纳指100联接A", "博时标普500联接A"], "status": "需调整"},
                {"name": "黄金ETF", "target_pct": 10, "current_pct": 10, "funds": ["华安黄金ETF"], "status": "达标"},
                {"name": "债券基金", "target_pct": 30, "current_pct": 35, "funds": ["易方达中短期美元债A"], "status": "需调整"},
                {"name": "货币基金", "target_pct": 5, "current_pct": 10, "funds": ["余额宝"], "status": "需调整"},
                {"name": "行业主题基金", "target_pct": 10, "current_pct": 10, "funds": ["工银前沿医疗股票A"], "status": "达标"},
            ]
        }),
        "backtest": {
            "total_return": backtest_summary.get("当前持仓", {}).get("累计收益", 0),
            "annual_return": backtest_summary.get("当前持仓", {}).get("年化收益", 0),
            "sharpe": backtest_summary.get("当前持仓", {}).get("夏普比率", 0),
            "max_drawdown": backtest_summary.get("当前持仓", {}).get("最大回撤", 0),
            "win_rate": 65,
            "adjusted_return": backtest_summary.get("调整后方案", {}).get("累计收益", 0),
            "adjusted_annual": backtest_summary.get("调整后方案", {}).get("年化收益", 0),
            "dca_total_return": backtest_summary.get("定投模拟", {}).get("总收益率", 0),
            "dca_irr": backtest_summary.get("定投模拟", {}).get("年化IRR", 0),
        },
        "nasdaqPE": nasdaq_cache.get("pe", 0),
        "nasdaqGrade": nasdaq_cache.get("peGrade", {}).get("name", "未知"),
        "nasdaqGradeColor": nasdaq_cache.get("peGrade", {}).get("cls", "yellow"),
        "nasdaqSuggestion": "",
        "peHistory": nasdaq_cache.get("historicalPE", []),
        "sentiment": {"score": 55, "level": "中性", "desc": "市场情绪中性偏谨慎"},
        "fundStats": backtest_summary.get("基金统计", []),
        "trendBacktest": [],
        "dcaData": {"dates": [], "values": [], "invested": []},
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 纳斯达克建议
    pe = game_data["nasdaqPE"]
    if pe > 0:
        if pe < 25:
            game_data["nasdaqSuggestion"] = f"PE={pe:.1f} 估值偏低，建议加倍定投纳指基金"
        elif pe < 35:
            game_data["nasdaqSuggestion"] = f"PE={pe:.1f} 估值正常，正常定投纳指基金"
        elif pe < 40:
            game_data["nasdaqSuggestion"] = f"PE={pe:.1f} 估值偏高，建议减半定投纳指基金"
        else:
            game_data["nasdaqSuggestion"] = f"PE={pe:.1f} 估值严重偏高，建议暂停定投纳指基金"

    # 趋势回测数据
    for idx_name, idx_data in index_backtest.items():
        game_data["trendBacktest"].append({
            "index": idx_name,
            "code": idx_data.get("fund_code", ""),
            "trades": idx_data.get("trades", 0),
            "winRate": idx_data.get("win_rate", 0),
            "totalNet": idx_data.get("total_net%", 0),
            "avgHold": idx_data.get("avg_hold_days", 0),
            "bhReturn": idx_data.get("bh_total%", 0),
        })

    # 读取定投数据
    dca_csv = DATA_DIR / "dca_backtest.csv"
    if dca_csv.exists():
        try:
            import csv
            dates, values, invested = [], [], []
            with open(dca_csv, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date_str = row.get("日期", "")
                    if date_str:
                        dates.append(date_str[:7])  # YYYY-MM
                        val = row.get("市值", "")
                        inv = row.get("投入", "")
                        values.append(round(float(val) / 10000, 1) if val else 0)
                        invested.append(round(float(inv) / 10000, 1) if inv else 0)
            game_data["dcaData"] = {"dates": dates, "values": values, "invested": invested}
        except Exception as e:
            logger.warning(f"读取定投数据失败: {e}")

    # 注入数据到HTML
    game_data_json = json.dumps(game_data, ensure_ascii=False, indent=8)
    html_content = html_content.replace(
        "const GAME_DATA = {",
        f"const GAME_DATA = {game_data_json};\n    // END INJECTED DATA\n    const _ORIGINAL = {{"
    )

    # 输出
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROJECT_ROOT / "index.html"  # 直接覆盖根目录的index.html
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"面板已生成: {output_path}")


def run_backtest():
    """运行回测"""
    logger.info("运行回测...")

    # 尝试使用fund-trend-system的回测引擎
    try:
        from src.engine.backtest import BacktestEngine
        from src.engine.strategies import STRATEGY_MAP

        engine = BacktestEngine(initial_capital=100000, fee_mode="full")

        # 从CSV缓存数据加载
        index_data_dir = DATA_DIR / "index_data"
        if index_data_dir.exists():
            import pandas as pd
            results = []
            for csv_file in index_data_dir.glob("*.csv"):
                index_name = csv_file.stem.split("_")[1] if "_" in csv_file.stem else csv_file.stem
                logger.info(f"回测指数: {index_name}")
                try:
                    df = pd.read_csv(csv_file)
                    if "nav_date" in df.columns and "nav" in df.columns:
                        for strategy_name in ["MA60-120"]:
                            result = engine.run_single(
                                csv_file.stem.split("_")[0],
                                strategy_name
                            )
                            if result:
                                results.append(result)
                except Exception as e:
                    logger.warning(f"回测 {index_name} 失败: {e}")

            if results:
                summary = engine.summary_table()
                logger.info(f"\n回测汇总:\n{summary.to_string()}")
                save_json("backtest_results.json", {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "results_count": len(results),
                })
    except Exception as e:
        logger.error(f"回测失败: {e}")

    logger.info("回测完成")


def send_email():
    """发送邮件推送"""
    logger.info("发送邮件推送...")

    try:
        from src.notify.email_sender import EmailSender
        from src.report.email_generator import EmailGenerator

        backtest_summary = load_backtest_summary()
        nasdaq_cache = load_nasdaq_cache()
        game_state = load_game_state()

        # 生成邮件内容
        email_gen = EmailGenerator()
        email_data = email_gen.generate({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "conclusion": _generate_conclusion(backtest_summary, nasdaq_cache),
            "signals": [],
            "backtest": backtest_summary,
            "nasdaq_pe": nasdaq_cache.get("pe", 0),
            "nasdaq_grade": nasdaq_cache.get("peGrade", {}).get("name", "未知"),
            "game_level": game_state.get("level", {}).get("name", "投资新手"),
            "risk_warning": "投资有风险，入市需谨慎。请根据自身情况决策。",
        })

        sender = EmailSender()
        success = sender.send(email_data["subject"], email_data["html"])
        if success:
            logger.info("邮件发送成功")
            # 记录游戏化经验
            try:
                from src.gamification import GamificationEngine
                game = GamificationEngine()
                game.add_xp(5, "发送邮件推送")
            except Exception:
                pass
        else:
            logger.error("邮件发送失败")
    except Exception as e:
        logger.error(f"邮件推送失败: {e}")


def _generate_conclusion(backtest_summary, nasdaq_cache):
    """生成今日结论"""
    pe = nasdaq_cache.get("pe", 0) if nasdaq_cache else 0
    parts = []

    if pe > 40:
        parts.append("纳斯达克估值偏高，暂停纳指定投")
    elif pe > 35:
        parts.append("纳斯达克估值正常偏高，维持定投")
    elif pe > 0:
        parts.append("纳斯达克估值偏低，建议加码定投")

    current_return = backtest_summary.get("当前持仓", {}).get("累计收益", 0)
    if current_return > 0:
        parts.append(f"当前持仓累计收益{current_return:.1f}%")

    return "；".join(parts) if parts else "市场平稳，按计划执行定投"


def quick_update():
    """快速更新面板"""
    logger.info("快速更新面板...")
    generate_dashboard()


def update_game():
    """更新游戏化状态"""
    logger.info("更新游戏化状态...")
    try:
        from src.gamification import GamificationEngine
        game = GamificationEngine()
        game.update_streak()
        game.add_xp(5, "每日签到")

        # 检查自动成就
        index_backtest = load_index_backtest()
        if index_backtest:
            best_wr = max(d.get("win_rate", 0) for d in index_backtest.values())
            game.check_auto_achievements({"win_rate": best_wr})

        state = game.to_dict()
        logger.info(f"游戏状态: Lv.{state['level']['level']} {state['level']['name']}, "
                     f"XP={state['xp']}, 连续{state['streak']}天")
    except Exception as e:
        logger.error(f"更新游戏状态失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="游戏化资产配置专家 - 整合版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --mode full-analysis       # 完整分析
  python main.py --mode generate-dashboard  # 生成面板
  python main.py --mode send-email          # 发送邮件
  python main.py --mode quick-update        # 快速更新
  python main.py --mode backtest            # 运行回测
  python main.py --mode update-game         # 更新游戏状态
        """
    )
    parser.add_argument(
        "--mode",
        choices=[
            "full-analysis", "generate-dashboard", "send-email",
            "quick-update", "backtest", "update-game"
        ],
        required=True,
        help="运行模式"
    )
    args = parser.parse_args()

    mode_actions = {
        "full-analysis": lambda: (run_full_analysis(), generate_dashboard()),
        "generate-dashboard": generate_dashboard,
        "send-email": send_email,
        "quick-update": quick_update,
        "backtest": run_backtest,
        "update-game": update_game,
    }

    action = mode_actions.get(args.mode)
    if action:
        result = action()
        logger.info(f"模式 [{args.mode}] 执行完成")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
