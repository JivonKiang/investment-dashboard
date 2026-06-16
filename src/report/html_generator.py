"""HTML 面板生成器"""
import json
import logging
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


class DashboardGenerator:
    """投资面板 HTML 生成器"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "j2"]),
        )
        self.env.filters["format_number"] = self._format_number
        self.env.filters["format_pct"] = self._format_pct

    @staticmethod
    def _format_number(value):
        if value is None:
            return "0"
        try:
            return f"{float(value):,.0f}"
        except (ValueError, TypeError):
            return str(value)

    @staticmethod
    def _format_pct(value):
        if value is None:
            return "0.00%"
        try:
            return f"{float(value) * 100:.2f}%"
        except (ValueError, TypeError):
            return str(value)

    def generate(self, data: dict, output_path: str = None) -> str:
        template = self.env.get_template("dashboard.html.j2")

        data.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        data.setdefault("total_assets", 600000)
        data.setdefault("daily_pnl", 0)
        data.setdefault("daily_pnl_pct", 0)
        data.setdefault("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        data.setdefault("signals", [])
        data.setdefault("positions", [])
        data.setdefault("backtest", {})
        data.setdefault("sentiment", {"score": 50, "level": "中性", "suggestion": "暂无数据"})
        data.setdefault("allocation_labels", [])
        data.setdefault("allocation_values", [])

        html = template.render(**data)

        if output_path:
            out = Path(output_path) if output_path else OUTPUT_DIR / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"面板已生成: {out}")

        return html
