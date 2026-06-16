"""数据获取模块 - 基于 AKShare 获取 A 股/基金数据"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """A 股/基金数据获取器"""

    # 指数代码映射
    INDEX_MAP = {
        "hs300": "000300",
        "zz500": "000905",
        "csi1000": "000852",
    }

    # 基金代码映射（支付宝可购买的ETF联接基金）
    FUND_MAP = {
        "hs300": "110020",       # 易方达沪深300ETF联接A
        "zz500": "160119",       # 南方中证500ETF联接A
        "nasdaq100": "160213",   # 国泰纳斯达克100ETF联接A
        "sp500": "000961",       # 博时标普500ETF联接A
        "gold": "002610",        # 博时黄金ETF联接C
        "bond_short": "003378",   # 易方达安悦超短债A
        "bond_pure": "000032",   # 易方达信用债A
        "money_market": "000198", # 天弘增利宝货币（余额宝）
    }

    def fetch_index_history(self, index_code: str, days: int = 90) -> pd.DataFrame:
        """获取指数历史行情数据"""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        try:
            df = ak.stock_zh_index_daily(symbol=f"sh{index_code}")
            df = df[df.index >= start_date]
            df = df[df.index <= end_date]
            df.columns = ["open", "close", "high", "low", "volume", "amount"]
            df.index.name = "date"
            return df.sort_index()
        except Exception as e:
            logger.error(f"获取指数 {index_code} 数据失败: {e}")
            return pd.DataFrame()

    def fetch_fund_net_value(self, fund_code: str, days: int = 90) -> pd.DataFrame:
        """获取基金净值历史数据"""
        try:
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
            df.columns = ["date", "net_value", "acc_net_value"]
            df = df.tail(days)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            return df.sort_index()
        except Exception as e:
            logger.error(f"获取基金 {fund_code} 净值失败: {e}")
            return pd.DataFrame()

    def fetch_stock_list_hs300(self) -> pd.DataFrame:
        """获取沪深300成分股列表"""
        try:
            df = ak.index_stock_cons(symbol="000300")
            return df[["品种代码", "品种名称"]].rename(
                columns={"品种代码": "code", "品种名称": "name"}
            )
        except Exception as e:
            logger.error(f"获取沪深300成分股失败: {e}")
            return pd.DataFrame()

    def fetch_stock_daily(self, stock_code: str, days: int = 90) -> pd.DataFrame:
        """获取个股日线数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=days)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            df = df.rename(columns={
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume"
            })
            df = df[["date", "open", "high", "low", "close", "volume"]]
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            return df.sort_index()
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 数据失败: {e}")
            return pd.DataFrame()

    def fetch_north_flow(self, days: int = 30) -> pd.DataFrame:
        """获取北向资金流向数据"""
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            df.columns = ["date", "north_net_buy"]
            df = df.tail(days)
            return df
        except Exception as e:
            logger.error(f"获取北向资金数据失败: {e}")
            return pd.DataFrame()
