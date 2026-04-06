from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import unescape
import re
import smtplib

from colorama import Style, Fore
from pathlib import Path
from emailhandler import EmailHandler
import numpy as np

DEBUG=False

type html_str=str

def convert_numpy_types(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    return obj

def send_email(to: str, body_html: html_str, debug: bool = True, subject: str = "NHS Proposal Confirmation", sender: str = "eddy12597@163.com", attachments: list[str] | None = None) -> bool:
    handler = EmailHandler()
    return handler.send_email(to, body_html, subject, sender, attachments, debug=debug)

# pyright: ignore[reportUnusedExpression]

import sys
from datetime import datetime, timezone
import functools
from colorama import Fore, Style
import html2text

class _flush_t:
    def __init__(self, content: str = "") -> None:
        self.content = content

class Lvl:
    INFO = info = Info = f"[INFO] "
    WARN = warn = Warn = f"[WARN] "
    FATAL = fatal = Fatal = f"[FATAL] "

flush = _flush_t()
endl = _flush_t(content="\n")

class TeeLogger:
    def __init__(self, *files) -> None:
        if len(files) == 0:
            files = [sys.stdout]
        self.files = files
        self.content: str = ""
        self.raise_afterward = False
    
    def __lshift__(self, other) -> 'TeeLogger':
        if isinstance(other, _flush_t):
            for f in self.files:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] ")
                f.write(self.content)
                
                f.write(other.content)
                f.flush()
            self.content = ""
            if self.raise_afterward:
                raise RuntimeError(self.content)
            else:
                return self
        elif isinstance(other, Lvl):
            if other == Lvl.FATAL:
                self.raise_afterward = True
        self.content += other # type: ignore
        return self
    
log = TeeLogger(sys.stdout, open("./app.log", "w", encoding="utf-8"))

def Log(_func=None, *, logger=log):
    """Decorator factory that works with or without parentheses"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger << Lvl.INFO << f"Function {func.__name__} called with {args}{f" and {kwargs}" if kwargs else ""}" << endl # pyright: ignore[reportUnusedExpression]
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger << Lvl.FATAL << f"Function {func.__name__} raised an error: {e}" << endl # pyright: ignore[reportUnusedExpression]
                raise
            
            logger << Lvl.INFO << f"Function {func.__name__} returned: {result}" << endl # pyright: ignore[reportUnusedExpression]
            return result
        return wrapper
    
    # Handle both @Log and @Log() syntax
    if _func is None:
        # Called with parentheses or with arguments: @Log() or @Log(logger=...)
        return decorator
    else:
        # Called without parentheses: @Log
        return decorator(_func)


# Similarity
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def similarity(str1: str, str2: str) -> float:
    def jaccard_similarity(str1, str2):
        set1 = set(str1.split())
        set2 = set(str2.split())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union != 0 else 0
    return (jaccard_similarity(str1, str2) + fuzz.ratio(str1, str2))/2


import tkinter as tk
from itertools import cycle

class TextSpinner:
    def __init__(self, parent):
        self.label = tk.Label(parent, text="", font=("Courier", 14))
        self.label.pack(pady=20)
        
        # Different spinner character sets
        # self.spinner_chars = cycle(['|', '/', '-', '\\'])
        self.spinner_chars = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        # or: cycle(['◐', '◓', '◑', '◒'])
        # or: cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
        
    def start(self):
        self.update_spinner()
        
    def update_spinner(self):
        char = next(self.spinner_chars)
        self.label.config(text=f"Loading {char}")
        self.label.after(100, self.update_spinner)  # Update every 100ms