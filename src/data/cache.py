"""数据缓存管理 - 避免重复请求"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class DataCache:
    """JSON 文件数据缓存"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_json(self, filename: str) -> dict:
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(self, filename: str, data: dict):
        filepath = self.data_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_df(self, filename: str) -> pd.DataFrame:
        filepath = self.data_dir / filename
        if filepath.exists():
            return pd.read_csv(filepath, index_col=0, parse_dates=True)
        return pd.DataFrame()

    def save_df(self, filename: str, df: pd.DataFrame):
        filepath = self.data_dir / filename
        df.to_csv(filepath)

    def is_cache_valid(self, filename: str, max_age_hours: int = 4) -> bool:
        filepath = self.data_dir / filename
        if not filepath.exists():
            return False
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        return (datetime.now() - mtime) < timedelta(hours=max_age_hours)
