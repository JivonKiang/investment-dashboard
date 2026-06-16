"""邮件内容生成器"""
import logging
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


class EmailGenerator:
    """邮件 HTML 内容生成器"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "j2"]),
        )
        self.env.filters["format_number"] = lambda v: f"{float(v):,.0f}" if v else "0"
        self.env.filters["format_pct"] = lambda v: f"{float(v)*100:.2f}%" if v else "0.00%"

    def generate(self, data: dict) -> dict:
        template = self.env.get_template("email.html.j2")
        data.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        data.setdefault("conclusion", "暂无数据")
        data.setdefault("signals", [])
        data.setdefault("backtest", {})
        data.setdefault("risk_warning", "请注意市场风险，合理控制仓位。")
        data.setdefault("dashboard_url", "https://yourusername.github.io/investment-dashboard/")

        html = template.render(**data)
        win_rate = data.get("backtest", {}).get("win_rate", 0)
        subject = f"[投资面板] {data['date']} 操作建议 | 回测胜率{win_rate*100:.0f}%"

        return {"subject": subject, "html": html}
