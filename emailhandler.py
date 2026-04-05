from html import unescape

import imaplib2 as im
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
import dotenv
import os
import smtplib
from pathlib import Path
from typing import Optional
import html2text
import re

def html_to_text(html_body: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_tables = False
    h.body_width = 0  # no hard wrapping

    return h.handle(html_body).strip()


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

dotenv.load_dotenv(dotenv.find_dotenv())

@dataclass
class Email:
    _from: str
    subject: str
    body: str
    def __str__(self):
        return f"Subject: {self.subject}\n\n{self.body}"

class EmailHandler:
    def __init__(self, imap_server: str = "imap.163.com", imap_port: int = 993, init_num: int = 10, mailbox = "INBOX", support_email: str | None = None, smtp_server: str | None = None, smtp_port: int | None = None):
        self.email = os.getenv("EMAIL") or "eddy12597@163.com"
        self.password = os.getenv("PASSKEY") or os.getenv("PASSWORD") or "Password Not Provided"
        
        if (not self.email) or (not self.password):
            raise Exception("Fields missing for email and password. Check if .env is created with\n\tEMAIL=<your email>\n\tPASSKEY=<app password>")
        print(f"")
        self.imap_server = imap_server
        self.support_email = support_email or self.email
        self.smtp_server = smtp_server or imap_server.replace("imap", "smtp")
        self.smtp_port = smtp_port or (587 if "gmail" in self.smtp_server else 465)
        
        status, response = None, None
        try:
            self.mail = im.IMAP4_SSL(self.imap_server, imap_port)
            self.mail.login(self.email, self.password)
            try:
                id_payload = (
                    '("name" "NHS Treasury Bot" '
                    '"version" "1.0.2" '
                    '"vendor" "BIPH National Honor Society" '
                    f'"support-email" "{self.support_email}")'
                )
                sta, res = self.mail._simple_command("ID", id_payload)
            except Exception:
                pass
        except im.IMAP4.error as e:
            print("Please check if you have enabled IMAP protocol in your email client, or check the imap server address")
            print(f"Status: {status}")
            print(f"Response: {response}")
            raise
        
        self.mailbox = mailbox
        self.emailList: list[Email] = []
    
    def _reconnect(self):
        try:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.__init__(imap_server=self.imap_server)
        except Exception as e:
            raise
    
    def pull(self, max_new: int = 5) -> list[Email]:
        new_emails = self.fetch_emails(max_new)
        if not new_emails:
            return []
        truly_new = [em for em in new_emails if em not in self.emailList]
        if truly_new:
            self.emailList.extend(truly_new)
        return truly_new
    
    def fetch_emails(self, num: int = 10) -> list[Email]:
        for attempt in (1, 2):
            try:
                return self._fetch_emails_once(num)
            except Exception as e:
                msg = str(e).lower()
                if attempt == 1 and ("autologout" in msg or "bye" in msg):
                    self._reconnect()
                    continue
                raise
        raise
            
    def _fetch_emails_once(self, num: int) -> list[Email]:
        status, response = self.mail.select(self.mailbox)
        if status != "OK":
            raise Exception(f"Failed to select mailbox: {self.mailbox}")
        last_uid = getattr(self, "_last_uid", 0)
        typ, data = self.mail.uid("SEARCH", None, f"UID {last_uid + 1}:*")
        if typ != "OK":
            raise Exception("UID search failed")
        if data is None:
            raise RuntimeError(f"Data is none when searching in inboxes via UID {last_uid + 1}")
        uid_list = data[0].split() # type: ignore
        if not uid_list:
            return []
        uid_list = uid_list[-num:]
        res: list[Email] = []
        for uid_val in uid_list:
            typ, msg_data = self.mail.uid("FETCH", uid_val, "(RFC822)")
            if typ != "OK":
                continue
            for part in msg_data: # type: ignore
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    subject, enc = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(enc or "utf-8")
                    body = self.get_email_body(msg)
                    _from = msg.get("from") or ""
                    res.append(Email(_from, subject, body))
            self._last_uid = int(uid_val)
        return res
    
    def get_email_body(self, msg, length=1000) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    continue
                if content_type in ["text/plain", "text/html"]:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        part_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        body += html_to_text(part_body) + "\n"
                    except Exception:
                        body += "[Error reading part]\n"
        else:
            content_type = msg.get_content_type()
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
                return html_to_text(body) if "<html" in body.lower() else body
            except Exception:
                body = "[Error reading body]"
                raise
        return body[:length] + "..." if len(body) > length else body
    
    def send_email(self, to: str, body_html: str, subject: str = "NHS Proposal Confirmation", sender: str | None = None, attachments: list[str] | None = None, debug: bool = False) -> bool:
        sender = sender or self.email
        body_text = html_to_markdown(body_html)
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        msg['Cc'] = self.support_email
        
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))
        
        if attachments:
            for f in attachments:
                try:
                    with open(f, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={f}')
                        msg.attach(part)
                except FileNotFoundError:
                    print(f"File {f} not found.")
                    skip = input("Skip? [Y/n]")
                    if skip.lower() in ("n", "no", "0"):
                        raise SystemExit
        
        if debug:
            outbox_dir = Path("./outbox")
            outbox_dir.mkdir(exist_ok=True)
            outbox_file = outbox_dir / f"{to.replace('@','_at_')}.eml"
            with open(outbox_file, "w", encoding="utf-8") as f:
                f.write(msg.as_string())
            print(f"Saved to outbox: {outbox_file}")
            return True
        
        try:
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.email, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email, self.password)
                    server.send_message(msg)
            return True
        except smtplib.SMTPException as e:
            print(f"Error: {e}")
            choice = input("Email failed. [S]kip, [R]etry, [A]bort? ").lower().strip()
            if choice == 'r':
                try:
                    if self.smtp_port == 465:
                        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                            server.login(self.email, self.password)
                            server.send_message(msg)
                    else:
                        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                            server.starttls()
                            server.login(self.email, self.password)
                            server.send_message(msg)
                    return True
                except:
                    return False
            elif choice == 'a':
                raise SystemExit
            return False