"""投资面板系统主入口"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.fetcher import DataFetcher
from src.data.cache import DataCache
from src.strategy.fund_momentum import FundMomentumStrategy
from src.strategy.stock_factor import MultiFactorStrategy
from src.strategy.timing import TimingStrategy
from src.strategy.sentiment import SentimentAnalyzer
from src.backtest.engine import BacktestEngine
from src.backtest.report import BacktestReport
from src.report.html_generator import DashboardGenerator
from src.report.email_generator import EmailGenerator
from src.notify.email_sender import EmailSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def run_full_analysis():
    """运行完整分析（盘前）"""
    logger.info("开始完整分析...")
    fetcher = DataFetcher()
    cache = DataCache(str(DATA_DIR))

    # 1. 获取数据
    logger.info("获取市场数据...")
    hs300_data = fetcher.fetch_index_history("000300", days=365)
    zz500_data = fetcher.fetch_index_history("000905", days=365)

    fund_data = {}
    for name, code in DataFetcher.FUND_MAP.items():
        nv = fetcher.fetch_fund_net_value(code, days=90)
        if not nv.empty:
            fund_data[name] = nv

    # 2. 运行策略
    logger.info("运行策略分析...")
    momentum_strategy = FundMomentumStrategy()
    mock_fund_data = {}
    for name, df in [("hs300", hs300_data), ("zz500", zz500_data)]:
        if not df.empty and len(df) >= 60:
            mock_fund_data[name] = {
                "return_3m": df["close"].pct_change(63).iloc[-1] if len(df) > 63 else 0,
                "return_6m": df["close"].pct_change(126).iloc[-1] if len(df) > 126 else 0,
                "return_12m": df["close"].pct_change(252).iloc[-1] if len(df) > 252 else 0,
                "pe_percentile": 50,
            }
    for name in ["nasdaq100", "sp500", "gold", "bond"]:
        if name not in mock_fund_data:
            mock_fund_data[name] = {
                "return_3m": 0.02, "return_6m": 0.05, "return_12m": 0.10, "pe_percentile": 50
            }

    fund_signals = momentum_strategy.generate_signals(mock_fund_data)

    timing_strategy = TimingStrategy()
    if not hs300_data.empty and len(hs300_data) >= 20:
        current_price = hs300_data["close"].iloc[-1]
        ma20 = hs300_data["close"].rolling(20).mean().iloc[-1]
        volume = hs300_data["volume"].iloc[-1]
        volume_ma20 = hs300_data["volume"].rolling(20).mean().iloc[-1]
        timing_signal = timing_strategy.generate_signal(
            current_price=current_price, ma20=ma20,
            volume=volume, volume_ma20=volume_ma20
        )
    else:
        timing_signal = {"direction": "neutral", "strength": 0.5, "reason": "数据不足"}

    sentiment_analyzer = SentimentAnalyzer()
    sentiment = sentiment_analyzer.calculate_score({
        "north_flow": 30.0, "margin_change": 0.01, "vix": 18.0,
        "volume_ratio": 1.05, "new_accounts": 180000,
    })

    backtest_report = BacktestReport(str(DATA_DIR))
    backtest_results = backtest_report.load_results()

    signals = []
    fund_code_map = DataFetcher.FUND_MAP
    for sig in fund_signals:
        if sig["action"] in ("overweight", "underweight"):
            amount = int(600000 * sig["weight"])
            signals.append({
                "action": "buy" if sig["action"] == "overweight" else "hold",
                "name": sig["name"],
                "code": fund_code_map.get(sig["name"], ""),
                "amount": amount,
                "channel": "alipay",
                "channel_label": "支付宝",
                "reason": sig["reason"],
                "win_rate": backtest_results.get("win_rate", 0.65),
                "momentum_score": sig["momentum_score"],
            })

    cache.save_json("signals.json", {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "fund_signals": signals,
        "timing_signal": timing_signal,
        "sentiment_score": sentiment["score"],
    })

    logger.info(f"分析完成，生成 {len(signals)} 条操作信号")
    return signals, timing_signal, sentiment, backtest_results


def generate_dashboard():
    """生成 HTML 面板"""
    logger.info("生成投资面板...")
    cache = DataCache(str(DATA_DIR))
    backtest_report = BacktestReport(str(DATA_DIR))

    signals_data = cache.load_json("signals.json")
    backtest_results = backtest_report.load_results()

    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_assets": 600000,
        "daily_pnl": 0,
        "daily_pnl_pct": 0,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "signals": signals_data.get("fund_signals", []),
        "positions": [],
        "backtest": backtest_results,
        "sentiment": {
            "score": signals_data.get("sentiment_score", 50),
            "level": "中性",
            "suggestion": "暂无数据",
        },
        "allocation_labels": ["A股指数", "海外指数", "黄金", "债券", "货币", "个股"],
        "allocation_values": [25, 10, 10, 30, 5, 20],
    }

    generator = DashboardGenerator()
    output_path = str(OUTPUT_DIR / "index.html")
    generator.generate(data, output_path)
    logger.info(f"面板已生成: {output_path}")


def run_backtest():
    """运行回测"""
    logger.info("运行回测...")
    fetcher = DataFetcher()
    engine = BacktestEngine(initial_cash=600000)

    hs300_data = fetcher.fetch_index_history("000300", days=750)
    if hs300_data.empty:
        logger.error("无法获取回测数据")
        return

    results = engine.run(hs300_data, strategy="ma_cross")

    report = BacktestReport(str(DATA_DIR))
    report.save_results(results)
    logger.info(f"回测完成: 年化{results['annual_return']:.2%}, 最大回撤{results['max_drawdown']:.2%}")


def send_email():
    """发送邮件通知"""
    logger.info("发送邮件通知...")
    cache = DataCache(str(DATA_DIR))
    backtest_report = BacktestReport(str(DATA_DIR))

    signals_data = cache.load_json("signals.json")
    backtest_results = backtest_report.load_results()

    signals = signals_data.get("fund_signals", [])
    buy_count = sum(1 for s in signals if s.get("action") == "buy")
    if buy_count >= 2:
        conclusion = "今日建议加仓，市场信号偏多"
    elif buy_count == 0:
        conclusion = "今日建议持有，等待更好时机"
    else:
        conclusion = "今日建议小幅调整，注意控制仓位"

    email_gen = EmailGenerator()
    email_data = email_gen.generate({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "conclusion": conclusion,
        "signals": signals,
        "backtest": backtest_results,
        "risk_warning": "投资有风险，入市需谨慎。请根据自身情况决策。",
    })

    sender = EmailSender()
    success = sender.send(email_data["subject"], email_data["html"])
    if success:
        logger.info("邮件发送成功")
    else:
        logger.error("邮件发送失败")


def quick_update():
    """盘中快速更新"""
    logger.info("盘中快速更新...")
    generate_dashboard()


def main():
    parser = argparse.ArgumentParser(description="投资面板系统")
    parser.add_argument("--mode", choices=[
        "full-analysis", "generate-dashboard", "backtest",
        "send-email", "quick-update", "monthly-report"
    ], required=True, help="运行模式")
    args = parser.parse_args()

    if args.mode == "full-analysis":
        run_full_analysis()
        generate_dashboard()
    elif args.mode == "generate-dashboard":
        generate_dashboard()
    elif args.mode == "backtest":
        run_backtest()
    elif args.mode == "send-email":
        send_email()
    elif args.mode == "quick-update":
        quick_update()
    elif args.mode == "monthly-report":
        run_backtest()
        run_full_analysis()
        generate_dashboard()


if __name__ == "__main__":
    main()
