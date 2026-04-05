from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import unescape
import re
import smtplib

from colorama import Style, Fore
from pathlib import Path

DEBUG=False

def html_to_markdown(html: str) -> str:
    """Convert HTML email template into markdown/plaintext preview."""
    text = html
    text = re.sub(r"<\s*(p|div|br)\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<\s*b\s*>(.*?)<\s*/b\s*>", r"**\1**", text, flags=re.I)
    text = re.sub(r'<a\s+href="(.*?)">(.*?)</a>', r"[\2](\1)", text, flags=re.I)
    text = re.sub(r"<(style|script).*?>.*?</\1>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\n\s*\n\s*", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text

type html_str=str

def send_email(to: str, body_html: html_str, server: smtplib.SMTP | None, subject: str = "NHS Proposal Confirmation", sender: str = "eddy12597@163.com", attachments: list[str] | None = None) -> bool:
    body_text = html_to_markdown(body_html)
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg['Cc'] = "eddy12597@163.com"

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    
    if attachments:
        for f in attachments:
            try:
                with open(f, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {f}')
                    msg.attach(part)
            except FileNotFoundError:
                print(f"{Fore.RED}File {f} not found.{Style.RESET_ALL}")
                if input("Skip? [Y/n]") in ("n", "no", "0"):
                    raise SystemExit
    
    print(f"{Fore.MAGENTA}Sending email to {to}:{Style.RESET_ALL}\n---\n{Style.BRIGHT}Subject: {subject}{Style.RESET_ALL}\n\nPreview:\n\n{body_text}\n")
    
    if DEBUG or server is None:
        outbox_dir = Path("./outbox")
        outbox_dir.mkdir(exist_ok=True)
        outbox_file = outbox_dir / f"{to.replace('@','_at_')}.eml"
        with open(outbox_file, "w", encoding="utf-8") as f:
            f.write(msg.as_string())
        print(f"{Fore.GREEN}Saved to outbox: {outbox_file}{Style.RESET_ALL}")
        return True 

    # confirm = input("Send this email? [Y/n] ").lower().strip()
    confirm = "y"
    if confirm != "n":
        try:
            server.send_message(msg)
            print(f"{Fore.GREEN}Email sent!{Style.RESET_ALL}")
            return True
        except smtplib.SMTPException as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            choice = input(f"{Fore.YELLOW}Email failed. [S]kip, [R]etry, [A]bort? ").lower().strip()
            if choice == 'r':
                try:
                    server.send_message(msg)
                    return True
                except:
                    return False
            elif choice == 'a':
                raise SystemExit
            return False
    return False