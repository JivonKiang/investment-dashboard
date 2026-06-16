"""邮件发送模块"""
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP 邮件发送器"""

    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "465"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.email_to = os.environ.get("EMAIL_TO", "")

    def send(self, subject: str, html_content: str) -> bool:
        if not all([self.smtp_user, self.smtp_pass, self.email_to]):
            logger.error("SMTP 配置不完整，请设置环境变量")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = self.email_to
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, self.email_to, msg.as_string())
            server.quit()
            logger.info(f"邮件已发送: {subject}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
