#!/usr/bin/env python3
"""
GalaxyTrader MK3 - Shared Log Analysis Utilities
=================================================
Common functions used across all GT analysis scripts.
"""

import io
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Windows UTF-8 fix (call once at script startup)
# ---------------------------------------------------------------------------
def fix_windows_encoding():
    """Force UTF-8 output on Windows to avoid cp1252 encoding errors."""
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external deps)
# ---------------------------------------------------------------------------
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if _USE_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text

def cyan(t):    return _c("36", t)
def yellow(t):  return _c("33", t)
def red(t):     return _c("31", t)
def green(t):   return _c("32", t)
def magenta(t): return _c("35", t)
def gray(t):    return _c("90", t)
def dkred(t):   return _c("31;2", t)
def white(t):   return _c("37", t)
def bold(t):    return _c("1", t)

def print_header(text: str):
    print()
    print(cyan(text))
    print(cyan("=" * len(text)))
    print()

def print_check(status: str, message: str):
    """Print a [PASS]/[WARN]/[FAIL]/[INFO] prefixed line."""
    colors = {"PASS": green, "WARN": yellow, "FAIL": red, "INFO": cyan}
    c = colors.get(status, white)
    print(f"  {c(f'[{status}]')} {message}")

# ---------------------------------------------------------------------------
# Compiled regex patterns (shared across scripts)
# ---------------------------------------------------------------------------
RE_TIMESTAMP = re.compile(
    r"\[(?:Scripts|ERROR|General|Init|=ERROR=)\]\s+(\d+\.\d+)(?:\s+\*\*\*|:)"
)

RE_TIMESTAMP_STRICT = re.compile(
    r"\[(?:Scripts|ERROR|General|Init)\]\s+(\d+\.\d+)(?:\s+\*\*\*|:)"
)

RE_CONTEXT_LINE = re.compile(
    r"^\[Scripts\]\s+(?P<time>\d+(?:\.\d+)?)\s+\*\*\*\s+Context:(?P<ctx>[^:]+):\s+(?P<msg>.*)$"
)

RE_HEADER_LINE = re.compile(
    r"^\[Scripts\]\s+(?P<time>\d+(?:\.\d+)?)\s+\*\*\*\s+(?P<rest>.*)$"
)

RE_SHIP_ID = re.compile(r"\b([A-Z]{3}-\d{3})\b")

RE_SHIP_ID_PAREN = re.compile(r"\(([A-Z]{3}-\d{3})\)")
RE_SHIP_ID_ATTR = re.compile(r"Ship=([A-Z]{3}-\d{3})")
RE_SHIP_ID_GTAI = re.compile(r"\[GT-AI\]\s+([A-Z]{3}-\d{3})\b")

# ---------------------------------------------------------------------------
# Log file auto-detection + file dialog
# ---------------------------------------------------------------------------
def show_file_dialog(initial_dir: str | None = None) -> str | None:
    """Open a native file picker dialog. Returns selected path or None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Select GalaxyTrader log file",
            initialdir=initial_dir or os.getcwd(),
            filetypes=[
                ("Log files", "*.log *.log.txt *.txt"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def resolve_log_path(hint: str = "", script_dir: str | None = None) -> str | None:
    """Try to locate the log file from common paths. Returns absolute path or None."""
    if script_dir is None:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    candidates = []
    if hint:
        candidates.append(hint)
        candidates.append(os.path.join(script_dir, hint))

    # 1) Script's own directory — for players who place scripts next to log.log
    candidates += [
        os.path.join(script_dir, "log.log"),
        os.path.join(script_dir, "log.log.txt"),
    ]
    # 2) Parent directory — for developers (scripts in GalaxyTraderMK3/tools/, log in GalaxyTraderMK3/)
    mod_root = os.path.dirname(script_dir)
    candidates += [
        os.path.join(mod_root, "log.log"),
        os.path.join(mod_root, "log.log.txt"),
    ]
    # 3) Current working directory and legacy paths
    candidates += [
        os.path.join(".", "log.log"),
        os.path.join(".", "GalaxyTraderMK3", "log.log"),
    ]

    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None


def require_log_file(hint: str = "", script_dir: str | None = None) -> str:
    """Resolve log file path, showing file dialog if not found. Exits on failure."""
    path = resolve_log_path(hint, script_dir)
    if path:
        return path

    print(yellow(f"Log file not found at default location: {hint or '(auto)'}"))
    print(yellow("Opening file picker..."))
    print()

    initial_dir = os.path.dirname(os.path.abspath(hint)) if hint else None
    if initial_dir and not os.path.isdir(initial_dir):
        initial_dir = script_dir or os.path.dirname(os.path.abspath(sys.argv[0]))

    selected = show_file_dialog(initial_dir)
    if selected and os.path.isfile(selected):
        path = os.path.abspath(selected)
        print(green(f"Selected: {path}"))
        print()
        return path

    # Fallback: manual input
    print(yellow("No file selected. Enter the path manually:"))
    print(gray("  (You can drag and drop the file into this window)"))
    try:
        user_input = input("Log file path: ").strip().strip('"').strip("'")
    except (EOFError, KeyboardInterrupt):
        user_input = ""
    if user_input and os.path.isfile(user_input):
        return os.path.abspath(user_input)

    print(red("ERROR: Log file not found."))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Log record reconstruction (handles multi-line continuation)
# ---------------------------------------------------------------------------
@dataclass
class LogRecord:
    time: float
    context: str
    message: str
    raw: str


def reconstruct_records(lines: list[str]) -> list[LogRecord]:
    """Parse raw log lines into structured records, joining continuation lines."""
    records: list[LogRecord] = []
    current: LogRecord | None = None

    for line in lines:
        m = RE_CONTEXT_LINE.match(line)
        if m:
            if current is not None:
                records.append(current)
            current = LogRecord(
                time=float(m.group("time")),
                context=m.group("ctx").strip(),
                message=m.group("msg"),
                raw=line,
            )
            continue

        m = RE_HEADER_LINE.match(line)
        if m:
            if current is not None:
                records.append(current)
            current = LogRecord(
                time=float(m.group("time")),
                context="",
                message=m.group("rest"),
                raw=line,
            )
            continue

        # Continuation line
        if current is not None:
            current.message += "\n" + line
            current.raw += "\n" + line

    if current is not None:
        records.append(current)
    return records


def stream_records(filepath: str, *, progress: bool = False):
    """Generator that yields LogRecord objects from a file, streaming line by line."""
    file_size = os.path.getsize(filepath)
    bytes_read = 0
    last_pct = 0
    current: LogRecord | None = None

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            bytes_read += len(line)
            if progress and file_size > 0:
                pct = int(bytes_read * 100 / file_size)
                if pct >= last_pct + 5:
                    last_pct = pct
                    print(f"\r  Reading: {pct}%", end="", flush=True)

            m = RE_CONTEXT_LINE.match(line)
            if m:
                if current is not None:
                    yield current
                current = LogRecord(
                    time=float(m.group("time")),
                    context=m.group("ctx").strip(),
                    message=m.group("msg"),
                    raw=line.rstrip(),
                )
                continue

            m = RE_HEADER_LINE.match(line)
            if m:
                if current is not None:
                    yield current
                current = LogRecord(
                    time=float(m.group("time")),
                    context="",
                    message=m.group("rest"),
                    raw=line.rstrip(),
                )
                continue

            if current is not None:
                current.message += "\n" + line.rstrip()
                current.raw += "\n" + line.rstrip()

    if current is not None:
        yield current
    if progress:
        print("\r  Reading: 100%        ")


# ---------------------------------------------------------------------------
# Ship ID extraction helpers
# ---------------------------------------------------------------------------
def extract_ship_id(text: str) -> str | None:
    """Extract ship ID from text, trying multiple patterns in priority order."""
    m = RE_SHIP_ID_GTAI.search(text)
    if m:
        return m.group(1)
    m = RE_SHIP_ID_PAREN.search(text)
    if m:
        return m.group(1)
    m = RE_SHIP_ID_ATTR.search(text)
    if m:
        return m.group(1)
    m = RE_SHIP_ID.search(text)
    if m:
        return m.group(1)
    return None


def has_ship_ref(text: str, ship_id: str) -> bool:
    """Check if text references a specific ship ID."""
    if ship_id not in text:
        return False
    return bool(re.search(
        r"(?:[(]|Ship=|ship=|\s|:|^)" + re.escape(ship_id) + r"(?:\s|[):\],]|$)",
        text
    ))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def truncate(s: str, n: int) -> str:
    return s[:n - 3] + "..." if len(s) > n else s


def percentile(sorted_values: list[float], p: float) -> float:
    """Linear interpolation percentile on a pre-sorted list."""
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    k = (n - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= n:
        return sorted_values[-1]
    d = k - f
    return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


def format_table(rows: list[dict], columns: list[tuple[str, str, int]] | None = None,
                 max_rows: int = 0) -> str:
    """
    Simple table formatter.
    columns: list of (key, header, min_width). If None, auto-detect from first row.
    """
    if not rows:
        return "  (no data)"

    if columns is None:
        columns = [(k, k, max(len(str(k)), 6)) for k in rows[0].keys()]

    # Compute widths
    widths = {}
    for key, header, min_w in columns:
        w = max(min_w, len(header))
        for row in rows[:max_rows or len(rows)]:
            val = str(row.get(key, ""))
            w = max(w, len(val))
        widths[key] = w

    # Header
    hdr = "  " + "  ".join(h.ljust(widths[k]) for k, h, _ in columns)
    sep = "  " + "  ".join("-" * widths[k] for k, _, _ in columns)
    lines = [hdr, sep]

    display_rows = rows[:max_rows] if max_rows > 0 else rows
    for row in display_rows:
        line = "  " + "  ".join(str(row.get(k, "")).ljust(widths[k]) for k, _, _ in columns)
        lines.append(line)

    if max_rows > 0 and len(rows) > max_rows:
        lines.append(f"  ... and {len(rows) - max_rows} more")

    return "\n".join(lines)
