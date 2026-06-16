# 智能投资面板

基于量化策略的每日投资建议系统，部署在 GitHub Pages 上，通过邮件推送操作建议。

## 功能

- 每日自动分析 A 股/基金市场数据
- 基金动量轮动策略 + 多因子选股策略 + 技术指标择时 + 市场情绪分析
- 回测引擎（Backtrader），提供胜率和盈利率
- GitHub Pages 静态面板，每分钟自动刷新
- 交易日 14:30 邮件推送最终投资意见

## 投资范围

- **基金（支付宝）**：沪深300、中证500、纳斯达克100、标普500、黄金、债券
- **个股（券商APP）**：沪深300成分股多因子选股

## 总资产

60万人民币，平衡型配置（50%权益 + 50%固收）

## 技术栈

- Python 3.11 + AKShare + BaoStock + pandas + numpy
- Backtrader 回测框架
- Jinja2 + Chart.js 静态页面
- GitHub Actions 定时调度
- GitHub Pages 部署
- SMTP 邮件推送

## 项目结构

```
src/
├── data/           # 数据获取（AKShare）
├── strategy/       # 策略引擎
├── backtest/       # 回测模块
├── report/         # 报告生成（HTML + 邮件）
├── notify/         # 邮件推送
└── main.py         # 主入口
```

## 本地运行

```bash
pip install -r requirements.txt
python src/main.py --mode full-analysis    # 完整分析
python src/main.py --mode generate-dashboard  # 生成面板
python src/main.py --mode backtest          # 运行回测
python src/main.py --mode send-email        # 发送邮件
```

## GitHub Actions 配置

在仓库 Settings → Secrets 中添加：
- `SMTP_HOST`: SMTP 服务器地址
- `SMTP_PORT`: SMTP 端口
- `SMTP_USER`: 邮箱账号
- `SMTP_PASS`: 邮箱授权码
- `EMAIL_TO`: 接收邮箱

## 免责声明

本系统仅供投资参考，不构成投资建议。投资有风险，入市需谨慎。
