#!/usr/bin/env python3
"""
GalaxyTrader MK3 - Bug Report Diagnostic Tool
===============================================
Player-friendly diagnostic script that collects system info, mod version,
and runs condensed health checks to produce a single bug report file.

No arguments required. Auto-detects the log file, or opens a file picker.

Usage:
    python gt_bug_report.py
    python gt_bug_report.py path/to/log.log
"""

import argparse
import os
import platform
import re
import sys
import time as _time
import urllib.request
import urllib.error
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime


import gt_log_utils as u

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
UPLOAD_URL = "https://0x0.st"
UPLOAD_RETENTION = "30 days (small files) to 365 days"

# ---------------------------------------------------------------------------
TOOL_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Compiled regex patterns for single-pass parsing
# ---------------------------------------------------------------------------
RE_GT_TAG = re.compile(r"\[GT-")
RE_ERROR_LINE = re.compile(r"\[=ERROR=\]")
RE_PROP_LOOKUP = re.compile(r"Property lookup failed", re.I)
RE_CRITICAL = re.compile(r"CRITICAL|EXCEPTION", re.I)

# Messages that X4 logs via [=ERROR=] but are NOT actual errors
# (Lua has no other log level; engine uses [=ERROR=] for warnings/info too)
RE_FALSE_ERROR = re.compile(
    r"={10,}"                            # separator lines (======…)
    r"|^\[=ERROR=\].*\[GT-Mods-Lua\]"    # GT Lua module loading messages
    r"|^\[=ERROR=\].*\[GT Context"       # GT context-menu integration
    r"|^\[=ERROR=\].*\bInit$"            # mod init announcements (e.g. "Forleyor Cheat Menu Init")
    r"|^\[=ERROR=\].*\bModule\s+loaded"  # "… Module loaded successfully"
    r"|^\[=ERROR=\].*\bRegistered\s+event" # "Registered event: …"
    r"|^\[=ERROR=\].*\bTo use:"          # usage hint lines
    r"|^\[=ERROR=\].*\bSkipping MD file\b" # duplicate MD scripts (expected with mod overrides)
    r"|^\[=ERROR=\].*\bDuplicate addon\b"  # duplicate addon entries (expected with mod overrides)
    r"|^\[=ERROR=\].*\bCould not find signature file\b" # missing .sig files (normal for mods)
    r"|^\[=ERROR=\].*\bRestricted function\b" # engine-internal restricted function calls
)

# Trade order events
RE_REQUEST = re.compile(r"SENDING GT_Find_(?:Trade|Sell)\b")
RE_ORDER_CREATED = re.compile(r"\bCreated (?:BUY|SELL) trade order\b|\bTrade orders created:\b|\bexecuting trade\b")
RE_NO_TRADE = re.compile(r"GT_No_Trade_Found\b")
RE_TIMEOUT = re.compile(r"MD system response timeout\b")
RE_ALL_REJECTED = re.compile(r"\bALL\s+\d+\s+trades.*were rejected")

# Live search events
RE_QUEUE_BUSY = re.compile(r"Live search busy\s+\(active:\s+\d+/\d+\)\s+-\s+QUEUING")
RE_HOME_DENY = re.compile(r"Home-sector live refresh already active.*denying live search")
RE_LOCK_ACQ = re.compile(r"\[GT-Lock\].*LOCK ACQUIRED")
RE_LOCK_REL = re.compile(r"\[GT-Lock\].*LOCK RELEASED")

# Cache events
RE_BEST_TRADE_SEL = re.compile(r"BEST TRADE SELECTED:")
RE_CLAIM_SWITCH = re.compile(r"\[GT-Fleet\].*Best trade was already reserved.*switched")

# Threat events
RE_THREAT = re.compile(r"\[GT-Threat\]|\[GT-Blacklist\]|CRITICAL THREAT|Ship destruction ignored")
RE_SHIP_DESTROYED = re.compile(r"CRITICAL THREAT|Ship destruction")

# Home sector (two formats in log)
RE_HOME_SECTOR = re.compile(r"Operating with home base:\s+(?P<home>.+?)\s+\(maxbuy=")
RE_HOME_SECTOR2 = re.compile(r"homeSector=(?P<home>.+?)(?:\s+[\w.]+\s*=|,|$)")

# Insufficient funds / money cap events
RE_BLOCKED_EARLY_REJECT = re.compile(
    r"BLOCKED trade \(early reject\).*player\.money=(?P<money>[\d.]+)\s*Cr.*purchaseCost=(?P<cost>[\d.]+)\s*Cr.*MinPlayerMoney.*\((?P<threshold>[\d.]+)\s*Cr\)")
RE_BLOCKED_AUTH_GUARD = re.compile(
    r"BLOCKED trade \(authoritative guard\).*player\.money=(?P<money>[\d.]+)\s*Cr.*purchaseCost=(?P<cost>[\d.]+)\s*Cr.*MinPlayerMoney.*\((?P<threshold>[\d.]+)\s*Cr\)")
RE_EARLY_MONEY_GATE = re.compile(
    r"EARLY MONEY GATE.*player money=(?P<money>[\d.]+)\s*Cr.*threshold=(?P<threshold>[\d.]+)\s*Cr")
RE_SHIP_MONEY_CAP_SKIP = re.compile(
    r"SHIP MONEY CAP:.*player money=(?P<money>[\d.]+)\s*Cr.*last block \((?P<blocked_at>[\d.]+)\s*Cr\)")
RE_SHIP_MONEY_CAP_CLEARED = re.compile(
    r"SHIP MONEY CAP CLEARED")
RE_INSUFFICIENT_FUNDS_WAIT = re.compile(
    r"insufficient funds - waiting\s+(?P<min>[\d.]+)-(?P<max>[\d.]+)s")

# Frame cost (timestamps)
RE_TS_FLOAT = re.compile(r"\[Scripts\]\s+(\d+\.\d+)\s+\*\*\*")


# ---------------------------------------------------------------------------
# Report writer (dual output: console + file)
# ---------------------------------------------------------------------------
class ReportWriter:
    """Writes to both console (colored) and a plain-text file."""

    def __init__(self, filepath: str):
        self._lines: list[str] = []
        self._filepath = filepath

    def header(self, text: str):
        self._lines.append("")
        self._lines.append(text)
        self._lines.append("=" * len(text))
        self._lines.append("")
        print()
        print(u.cyan(text))
        print(u.cyan("=" * len(text)))
        print()

    def line(self, text: str = ""):
        self._lines.append(text)
        print(text)

    def check(self, status: str, message: str):
        self._lines.append(f"  [{status}] {message}")
        u.print_check(status, message)

    def detail(self, text: str):
        """Detail line (goes to file, shown gray on console)."""
        self._lines.append(text)
        print(u.gray(text))

    def file_only(self, text: str):
        """Write to file only (no console output). Use for large data sections."""
        self._lines.append(text)

    def save(self):
        with open(self._filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(self._lines))
            f.write("\n")


# ---------------------------------------------------------------------------
# 0x0.st upload (no auth, no account required)
# ---------------------------------------------------------------------------
def upload_file(filepath: str) -> str | None:
    """Upload a file to 0x0.st and return the download URL, or None on failure."""
    filename = os.path.basename(filepath)
    boundary = f"----GTBugReport{int(_time.time())}"

    with open(filepath, "rb") as f:
        file_data = f.read()

    # Build multipart/form-data body
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: application/zip\r\n\r\n"
    body += file_data
    body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        UPLOAD_URL,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "GT-BugReport/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            url = resp.read().decode("utf-8").strip()
            if url.startswith("http"):
                return url
            return None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(u.red(f"  Upload error: {e}"))
        return None


# ---------------------------------------------------------------------------
# Section 1: System Information
# ---------------------------------------------------------------------------
def section_system_info(rpt: ReportWriter, log_path: str):
    rpt.header("1. System Information")
    rpt.line(f"  OS              : {platform.system()} {platform.release()} ({platform.version()})")
    rpt.line(f"  Architecture    : {platform.machine()}")
    rpt.line(f"  Python          : {platform.python_version()}")
    rpt.line(f"  Report date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    rpt.line(f"  Tool version    : {TOOL_VERSION}")
    rpt.line(f"  Log file        : {log_path}")
    size = os.path.getsize(log_path)
    if size > 1024 * 1024:
        rpt.line(f"  Log size        : {size / (1024*1024):.1f} MB ({size:,} bytes)")
    else:
        rpt.line(f"  Log size        : {size / 1024:.1f} KB ({size:,} bytes)")


# ---------------------------------------------------------------------------
# Section 2: Game Session Info
# ---------------------------------------------------------------------------
def section_session_info(rpt: ReportWriter, log_path: str):
    rpt.header("2. Game Session Info")

    header_lines: list[str] = []
    gpu_info: list[str] = []
    session_start = ""

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= 30:
                break
            stripped = line.rstrip()
            if i == 0 and stripped.startswith("Logfile started"):
                session_start = stripped.replace("Logfile started, time ", "").strip()
                continue
            if "[General]" in stripped and "NVIDIA" in stripped or "AMD" in stripped or "Intel" in stripped:
                # Extract GPU name
                m = re.search(r"'([^']+)'", stripped)
                if m:
                    gpu_info.append(m.group(1))
            header_lines.append(stripped)

    rpt.line(f"  Session started : {session_start or '(unknown)'}")
    if gpu_info:
        for g in gpu_info:
            rpt.line(f"  GPU             : {g}")
    else:
        rpt.line(f"  GPU             : (not found in log header)")


def _format_settings_category(rpt: ReportWriter, cat: str, raw: str):
    """Format a settings category with one key=value per line."""
    rpt.line(f"    [{cat}]")
    pairs = raw.split()
    for pair in pairs:
        rpt.line(f"      {pair}")


# ---------------------------------------------------------------------------
# Section 3: Mod Version
# ---------------------------------------------------------------------------
def section_mod_version(rpt: ReportWriter, log_path: str):
    rpt.header("3. GalaxyTrader MK3 Version & Settings")

    # Extract version and settings from the log file (logged at mod init)
    # Format: [GalaxyTrader MK3] INIT: Version=0.8.0.0 ContentVersion=0800
    # Format: [GalaxyTrader MK3] SETTINGS.Category: Key=Value Key2=Value2 ...
    re_init = re.compile(
        r"\[GalaxyTrader MK3\] INIT: Version=(\S+)\s+ContentVersion=(\S+)")
    re_settings = re.compile(
        r"\[GalaxyTrader MK3\] SETTINGS\.(\S+?):\s+(.*)")
    re_blacklist = re.compile(
        r"\[GalaxyTrader MK3\] BLACKLISTED_SECTORS:\s+(.*)")

    mod_version = "(not found in log)"
    content_version = "(not found in log)"
    # Keep last occurrence of each settings category (most recent game load)
    settings: dict[str, str] = {}
    blacklisted_sectors_raw = ""

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re_init.search(line)
                if m:
                    mod_version = m.group(1)
                    content_version = m.group(2)
                m2 = re_settings.search(line)
                if m2:
                    settings[m2.group(1)] = m2.group(2).strip()
                m3 = re_blacklist.search(line)
                if m3:
                    blacklisted_sectors_raw = m3.group(1).strip()
    except Exception as e:
        rpt.line(f"  WARNING: Failed to scan log for version/settings: {e}")

    rpt.line(f"  Mod version     : {mod_version} (content.xml: {content_version})")
    rpt.line("")

    if settings:
        rpt.line("  Active Settings (from most recent game load):")
        # Display in a consistent order, one setting per line
        preferred_order = [
            "Fleet", "XP", "Performance", "Performance2",
            "ThreatAvoidance", "Notifications", "Debug",
            "AutoRepair", "MobileIntel", "Modifications",
            "ShipNaming", "NumberFormat",
        ]
        displayed = set()
        for cat in preferred_order:
            if cat in settings:
                _format_settings_category(rpt, cat, settings[cat])
                displayed.add(cat)
        # Any unexpected categories
        for cat in sorted(settings):
            if cat not in displayed:
                _format_settings_category(rpt, cat, settings[cat])
    else:
        rpt.line("  Settings: (not found in log - mod may not have initialized yet)")

    # Blacklisted sectors snapshot
    rpt.line("")
    if blacklisted_sectors_raw:
        # Format: Count=N | SectorName(LX) SectorName(LX) ...
        m_count = re.match(r"Count=(\d+)", blacklisted_sectors_raw)
        count = int(m_count.group(1)) if m_count else 0
        if count == 0:
            rpt.line("  Blacklisted Sectors: none")
        else:
            rpt.line(f"  Blacklisted Sectors ({count}):")
            # Extract sector entries after the "|"
            parts = blacklisted_sectors_raw.split("|", 1)
            if len(parts) == 2:
                sector_entries = parts[1].strip().split()
                for entry in sector_entries:
                    rpt.line(f"    - {entry}")
    else:
        rpt.line("  Blacklisted Sectors: (not found in log)")


# ---------------------------------------------------------------------------
# Section 4-8: Single-pass log analysis
# ---------------------------------------------------------------------------
def analyze_log(rpt: ReportWriter, log_path: str, *, tail_size: int = 500):
    """Single-pass streaming analysis that powers sections 4-8."""

    # Counters and accumulators
    total_lines = 0
    gt_lines = 0
    ship_ids: set[str] = set()
    home_sectors: set[str] = set()
    first_ts: float | None = None
    last_ts: float = 0.0

    # Frame cost (operations per timestamp)
    ops_per_ts: Counter = Counter()

    # Trade order tracking (per-ship simplified)
    request_count = 0
    order_count = 0
    no_trade_count = 0
    timeout_count = 0
    all_rejected_count = 0
    ships_with_request: dict[str, float] = {}   # ship -> last request time
    ships_with_terminal: set[str] = set()        # ships that got a terminal response

    # Live search
    queue_busy_count = 0
    home_deny_count = 0
    lock_acq_count = 0
    lock_rel_count = 0

    # Cache
    best_trade_sel_count = 0
    claim_switch_count = 0

    # Threats
    threat_event_count = 0
    ship_destroyed_count = 0

    # Insufficient funds tracking
    block_early_reject_count = 0
    block_auth_guard_count = 0
    early_money_gate_count = 0
    ship_money_cap_skip_count = 0
    ship_money_cap_cleared_count = 0
    insufficient_funds_wait_count = 0
    # Per-ship: ship -> list of (timestamp, event_type, money, cost_or_threshold)
    funds_events_per_ship: dict[str, list[tuple]] = defaultdict(list)
    # Player money at block times (for trend display)
    money_at_blocks: list[tuple[float, float]] = []  # (timestamp, player_money_cr)
    # First/last insufficient funds timestamps
    first_funds_block_ts: float | None = None
    last_funds_block_ts: float = 0.0
    # Recent (last 5 min) money-blocked ships
    recent_money_blocked: Counter = Counter()

    # Errors
    error_lines: list[str] = []
    prop_lookup_fails: list[str] = []
    critical_lines: list[str] = []

    # Recent ship issues (collected for last 5 min of game time, filled after first pass for max_time)
    recent_no_trade: Counter = Counter()    # ship -> count
    recent_rejected: Counter = Counter()    # ship -> count
    recent_timeout: Counter = Counter()     # ship -> count

    # Raw log tail (complete log or last N lines)
    limit_tail = tail_size > 0  # True = keep only last N lines; False = keep all
    log_tail: deque[str] | list[str] = deque(maxlen=tail_size) if limit_tail else []

    print(u.yellow("  Analyzing log (single-pass)..."))
    start_wall = _time.time()

    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            total_lines += 1
            stripped = line.rstrip()

            # Timestamp extraction
            ts_m = RE_TS_FLOAT.search(stripped)
            ts: float | None = None
            if ts_m:
                ts = float(ts_m.group(1))
                if first_ts is None:
                    first_ts = ts
                last_ts = max(last_ts, ts)
                ops_per_ts[ts] += 1

            # Error lines (always check, regardless of GT)
            # Skip Lua/init messages that X4 logs via [=ERROR=] but aren't real errors
            if RE_ERROR_LINE.search(stripped) and not RE_FALSE_ERROR.search(stripped):
                if len(error_lines) < 200:
                    error_lines.append(stripped)

            if RE_PROP_LOOKUP.search(stripped):
                if len(prop_lookup_fails) < 50:
                    prop_lookup_fails.append(stripped)

            if RE_CRITICAL.search(stripped) and "[GT-" not in stripped:
                if len(critical_lines) < 50:
                    critical_lines.append(stripped)

            # Log tail (all lines, not just GT)
            log_tail.append(stripped)

            # GT-specific analysis
            if not RE_GT_TAG.search(stripped) and "GT_Find_" not in stripped and "GT_No_Trade" not in stripped and "GT_Trade" not in stripped:
                continue

            gt_lines += 1

            # Ship ID extraction
            sid = u.extract_ship_id(stripped)
            if sid:
                ship_ids.add(sid)

            # Home sector
            hm = RE_HOME_SECTOR.search(stripped)
            if hm:
                home_sectors.add(hm.group("home").strip())
            else:
                hm2 = RE_HOME_SECTOR2.search(stripped)
                if hm2:
                    home_sectors.add(hm2.group("home").strip())

            # Trade order events
            if RE_REQUEST.search(stripped):
                request_count += 1
                if sid:
                    ships_with_request[sid] = ts or 0.0

            if RE_ORDER_CREATED.search(stripped):
                order_count += 1
                if sid:
                    ships_with_terminal.add(sid)

            if RE_NO_TRADE.search(stripped):
                no_trade_count += 1
                if sid:
                    ships_with_terminal.add(sid)
                    if ts and last_ts > 0 and ts >= last_ts - 300:
                        recent_no_trade[sid] += 1

            if RE_TIMEOUT.search(stripped):
                timeout_count += 1
                if sid and ts and last_ts > 0 and ts >= last_ts - 300:
                    recent_timeout[sid] += 1

            if RE_ALL_REJECTED.search(stripped):
                all_rejected_count += 1
                if sid and ts and last_ts > 0 and ts >= last_ts - 300:
                    recent_rejected[sid] += 1

            # Live search
            if RE_QUEUE_BUSY.search(stripped):
                queue_busy_count += 1
            if RE_HOME_DENY.search(stripped):
                home_deny_count += 1
            if RE_LOCK_ACQ.search(stripped):
                lock_acq_count += 1
            if RE_LOCK_REL.search(stripped):
                lock_rel_count += 1

            # Cache
            if RE_BEST_TRADE_SEL.search(stripped):
                best_trade_sel_count += 1
            if RE_CLAIM_SWITCH.search(stripped):
                claim_switch_count += 1

            # Threats
            if RE_THREAT.search(stripped):
                threat_event_count += 1
            if RE_SHIP_DESTROYED.search(stripped):
                ship_destroyed_count += 1

            # Insufficient funds / money cap events
            m_er = RE_BLOCKED_EARLY_REJECT.search(stripped)
            if m_er:
                block_early_reject_count += 1
                money_cr = float(m_er.group("money"))
                cost_cr = float(m_er.group("cost"))
                if ts is not None:
                    money_at_blocks.append((ts, money_cr))
                    if first_funds_block_ts is None:
                        first_funds_block_ts = ts
                    last_funds_block_ts = ts
                if sid:
                    funds_events_per_ship[sid].append((ts or 0.0, "block_md", money_cr, cost_cr))
                    if ts and last_ts > 0 and ts >= last_ts - 300:
                        recent_money_blocked[sid] += 1

            m_ag = RE_BLOCKED_AUTH_GUARD.search(stripped)
            if m_ag:
                block_auth_guard_count += 1
                money_cr = float(m_ag.group("money"))
                cost_cr = float(m_ag.group("cost"))
                if ts is not None:
                    money_at_blocks.append((ts, money_cr))
                    if first_funds_block_ts is None:
                        first_funds_block_ts = ts
                    last_funds_block_ts = ts
                if sid:
                    funds_events_per_ship[sid].append((ts or 0.0, "block_ai", money_cr, cost_cr))
                    if ts and last_ts > 0 and ts >= last_ts - 300:
                        recent_money_blocked[sid] += 1

            m_emg = RE_EARLY_MONEY_GATE.search(stripped)
            if m_emg:
                early_money_gate_count += 1
                if sid:
                    money_cr = float(m_emg.group("money"))
                    funds_events_per_ship[sid].append((ts or 0.0, "early_gate", money_cr, 0))
                    if ts and last_ts > 0 and ts >= last_ts - 300:
                        recent_money_blocked[sid] += 1

            m_smc = RE_SHIP_MONEY_CAP_SKIP.search(stripped)
            if m_smc:
                ship_money_cap_skip_count += 1
                if sid:
                    money_cr = float(m_smc.group("money"))
                    funds_events_per_ship[sid].append((ts or 0.0, "cap_skip", money_cr, 0))
                    if ts and last_ts > 0 and ts >= last_ts - 300:
                        recent_money_blocked[sid] += 1

            if RE_SHIP_MONEY_CAP_CLEARED.search(stripped):
                ship_money_cap_cleared_count += 1

            if RE_INSUFFICIENT_FUNDS_WAIT.search(stripped):
                insufficient_funds_wait_count += 1

    elapsed = _time.time() - start_wall

    # Re-scan recent issues now that we know last_ts
    # (The counters above already conditionally collected data for the last ~5 min window)

    # =====================================================================
    # Section 4: Fleet Overview
    # =====================================================================
    rpt.header("4. Fleet Overview")
    duration = (last_ts - first_ts) if first_ts is not None else 0
    rpt.line(f"  Total log lines       : {total_lines:,}")
    rpt.line(f"  GT-related lines      : {gt_lines:,}")
    rpt.line(f"  Game time range       : {first_ts or 0:.2f}s - {last_ts:.2f}s ({duration:.0f}s / {duration/60:.1f} min)")
    rpt.line(f"  Unique ships          : {len(ship_ids)}")
    rpt.line(f"  Unique home sectors   : {len(home_sectors)}")
    if home_sectors:
        for hs in sorted(home_sectors):
            rpt.detail(f"    - {hs}")
    rpt.line(f"  Analysis time         : {elapsed:.2f}s")

    # =====================================================================
    # Section 5: Health Checks
    # =====================================================================
    rpt.header("5. Health Checks")

    # --- Timeline / Performance ---
    rpt.line("  --- Performance ---")
    if ops_per_ts:
        sorted_ops = sorted(ops_per_ts.values())
        peak_ops = sorted_ops[-1] if sorted_ops else 0
        p95_ops = u.percentile(sorted_ops, 95)
        avg_ops = sum(sorted_ops) / len(sorted_ops)

        if peak_ops >= 100:
            rpt.check("FAIL", f"Peak operations/frame: {peak_ops} (very high, likely stutter)")
        elif peak_ops >= 50:
            rpt.check("WARN", f"Peak operations/frame: {peak_ops} (elevated)")
        else:
            rpt.check("PASS", f"Peak operations/frame: {peak_ops}")

        if p95_ops >= 30:
            rpt.check("WARN", f"p95 operations/frame: {p95_ops:.0f} (sustained high load)")
        else:
            rpt.check("PASS", f"p95 operations/frame: {p95_ops:.0f}")

        rpt.detail(f"    avg={avg_ops:.1f}, p95={p95_ops:.0f}, peak={peak_ops}, unique_frames={len(ops_per_ts)}")
    else:
        rpt.check("WARN", "No GT frame data found")

    # --- Trade Orders ---
    rpt.line("")
    rpt.line("  --- Trade Orders ---")
    rpt.line(f"    Requests: {request_count}  |  Orders created: {order_count}  |  No trade found: {no_trade_count}  |  Timeouts: {timeout_count}")

    if request_count > 0:
        success_rate = order_count / request_count * 100
        if success_rate < 10 and request_count >= 10:
            rpt.check("FAIL", f"Trade success rate: {success_rate:.1f}% ({order_count}/{request_count})")
        elif success_rate < 30 and request_count >= 10:
            rpt.check("WARN", f"Trade success rate: {success_rate:.1f}% ({order_count}/{request_count})")
        else:
            rpt.check("PASS", f"Trade success rate: {success_rate:.1f}% ({order_count}/{request_count})")
    else:
        rpt.check("INFO", "No trade requests found in log")

    # Stalled ships
    stalled = set(ships_with_request.keys()) - ships_with_terminal
    if len(stalled) > 5:
        rpt.check("FAIL", f"Stalled ships (request but no response): {len(stalled)}")
        for sid in sorted(stalled)[:10]:
            rpt.detail(f"      {sid}: last request at t={ships_with_request[sid]:.2f}")
    elif stalled:
        rpt.check("WARN", f"Stalled ships: {len(stalled)} (may still be in progress)")
    else:
        rpt.check("PASS", "No stalled ships detected")

    if timeout_count > 0:
        rpt.check("WARN" if timeout_count < 10 else "FAIL", f"MD timeouts: {timeout_count}")
    else:
        rpt.check("PASS", "MD timeouts: 0")

    if all_rejected_count > 0:
        rpt.check("WARN" if all_rejected_count < 20 else "FAIL", f"All-trades-rejected events: {all_rejected_count}")
    else:
        rpt.check("PASS", "All-trades-rejected events: 0")

    # --- Live Search ---
    rpt.line("")
    rpt.line("  --- Live Search ---")

    if queue_busy_count >= 50:
        rpt.check("WARN", f"Queue busy (saturated) events: {queue_busy_count}")
    else:
        rpt.check("PASS", f"Queue busy events: {queue_busy_count}")

    if home_deny_count >= 200:
        rpt.check("WARN", f"Home-refresh denials: {home_deny_count} (very high)")
    elif home_deny_count >= 50:
        rpt.check("WARN", f"Home-refresh denials: {home_deny_count} (high, may be normal for large fleets)")
    else:
        rpt.check("PASS", f"Home-refresh denials: {home_deny_count}")

    unreleased = lock_acq_count - lock_rel_count
    if lock_acq_count == 0 and lock_rel_count == 0:
        rpt.check("INFO", "No lock operations found (lock logging may not be enabled)")
    elif unreleased > 5:
        rpt.check("FAIL", f"Unreleased locks: {unreleased} (acq={lock_acq_count} rel={lock_rel_count})")
    elif unreleased > 0:
        rpt.check("WARN", f"Unreleased locks: {unreleased} (may be in-progress searches)")
    else:
        rpt.check("PASS", f"All locks released (acq={lock_acq_count} rel={lock_rel_count})")

    # --- Cache / Fleet Reservations ---
    rpt.line("")
    rpt.line("  --- Cache & Reservations ---")
    rpt.line(f"    Trade selections: {best_trade_sel_count}  |  Claim-check switches: {claim_switch_count}")
    if best_trade_sel_count > 0:
        switch_rate = claim_switch_count / best_trade_sel_count * 100 if best_trade_sel_count > 0 else 0
        if switch_rate > 30:
            rpt.check("WARN", f"Claim-switch rate: {switch_rate:.1f}% (high contention)")
        else:
            rpt.check("PASS", f"Claim-switch rate: {switch_rate:.1f}%")
    else:
        rpt.check("INFO", "No trade selections found")

    # --- Threats ---
    rpt.line("")
    rpt.line("  --- Threats & Blacklist ---")
    rpt.line(f"    Threat events: {threat_event_count}  |  Ship destruction events: {ship_destroyed_count}")
    if ship_destroyed_count > 10:
        rpt.check("WARN", f"High ship destruction count: {ship_destroyed_count}")
    elif ship_destroyed_count > 0:
        rpt.check("INFO", f"Ship destructions: {ship_destroyed_count}")
    else:
        rpt.check("PASS", "No ship destruction events")

    # --- Insufficient Funds ---
    rpt.line("")
    rpt.line("  --- Insufficient Funds ---")
    total_funds_blocks = block_early_reject_count + block_auth_guard_count
    total_funds_skips = early_money_gate_count + ship_money_cap_skip_count

    if total_funds_blocks == 0 and total_funds_skips == 0:
        rpt.check("PASS", "No insufficient funds events")
    else:
        rpt.line(f"    Trade blocks (MD FINAL GUARD)    : {block_early_reject_count}")
        rpt.line(f"    Trade blocks (AI auth. guard)    : {block_auth_guard_count}")
        rpt.line(f"    Search skips (early money gate)  : {early_money_gate_count}")
        rpt.line(f"    Search skips (per-ship cap)      : {ship_money_cap_skip_count}")
        rpt.line(f"    Cap clears (money increased)     : {ship_money_cap_cleared_count}")
        rpt.line(f"    Backoff waits (insufficient)     : {insufficient_funds_wait_count}")

        if total_funds_blocks > 0:
            # Show severity
            if total_funds_blocks > 100:
                rpt.check("FAIL", f"Total trade blocks due to insufficient funds: {total_funds_blocks} (excessive - MinPlayerMoney may be too high or fleet too large)")
            elif total_funds_blocks > 20:
                rpt.check("WARN", f"Total trade blocks due to insufficient funds: {total_funds_blocks}")
            else:
                rpt.check("INFO", f"Total trade blocks due to insufficient funds: {total_funds_blocks}")

        # Cap effectiveness: skips mean the cap is working (avoiding pointless searches)
        if ship_money_cap_skip_count > 0:
            rpt.check("PASS", f"Per-ship money cap saved {ship_money_cap_skip_count} pointless searches")

        # Show player money trend at block times
        if money_at_blocks:
            first_block = money_at_blocks[0]
            last_block = money_at_blocks[-1]
            min_money = min(m for _, m in money_at_blocks)
            rpt.line("")
            rpt.line("    Player money at block events:")
            rpt.line(f"      First block : t={first_block[0]:.2f}s  money={first_block[1]:,.0f} Cr")
            rpt.line(f"      Last block  : t={last_block[0]:.2f}s  money={last_block[1]:,.0f} Cr")
            rpt.line(f"      Lowest      : {min_money:,.0f} Cr")
            if first_funds_block_ts is not None:
                duration_blocked = last_funds_block_ts - first_funds_block_ts
                rpt.line(f"      Block window: {duration_blocked:.0f}s ({duration_blocked/60:.1f} min)")

        # Per-ship breakdown (top blocked ships)
        ships_by_blocks = Counter()
        for sid, events in funds_events_per_ship.items():
            block_count = sum(1 for _, etype, _, _ in events if etype in ("block_md", "block_ai"))
            if block_count > 0:
                ships_by_blocks[sid] = block_count

        if ships_by_blocks:
            rpt.line("")
            rpt.line(f"    Ships blocked by insufficient funds ({len(ships_by_blocks)} ships):")
            for sid, cnt in ships_by_blocks.most_common(15):
                # Show last known money and cost for this ship
                last_event = None
                for ev in reversed(funds_events_per_ship[sid]):
                    if ev[1] in ("block_md", "block_ai"):
                        last_event = ev
                        break
                if last_event:
                    rpt.detail(f"      {sid}: {cnt}x blocked (last: money={last_event[2]:,.0f} Cr, trade cost={last_event[3]:,.0f} Cr)")
                else:
                    rpt.detail(f"      {sid}: {cnt}x blocked")

        # Ships that only hit the cap skip (never actually blocked themselves, just skipped)
        skip_only_ships = Counter()
        for sid, events in funds_events_per_ship.items():
            skip_count = sum(1 for _, etype, _, _ in events if etype in ("cap_skip", "early_gate"))
            block_count = sum(1 for _, etype, _, _ in events if etype in ("block_md", "block_ai"))
            if skip_count > 0 and block_count == 0:
                skip_only_ships[sid] = skip_count

        if skip_only_ships:
            rpt.line("")
            rpt.line(f"    Ships that only skipped searches (per-ship cap, {len(skip_only_ships)} ships):")
            for sid, cnt in skip_only_ships.most_common(10):
                rpt.detail(f"      {sid}: {cnt}x skipped")

    # =====================================================================
    # Section 6: Error Summary
    # =====================================================================
    rpt.header("6. Error Summary")

    # Deduplicate errors
    error_counts: Counter = Counter()
    for e in error_lines:
        # Normalize: remove timestamps for dedup
        cleaned = re.sub(r"\[=ERROR=\]\s+\d+\.\d+\s*", "[=ERROR=] ", e)
        cleaned = re.sub(r"^.*?\[=ERROR=\]\s*", "", cleaned).strip()
        if cleaned:
            error_counts[u.truncate(cleaned, 120)] += 1

    gt_errors = {k: v for k, v in error_counts.items() if "GT" in k or "GalaxyTrader" in k}
    other_errors = {k: v for k, v in error_counts.items() if k not in gt_errors}

    if gt_errors:
        rpt.line(f"  GT-related errors ({len(gt_errors)} unique):")
        for msg, cnt in sorted(gt_errors.items(), key=lambda x: x[1], reverse=True)[:15]:
            rpt.line(f"    {cnt:>3}x  {msg}")
    else:
        rpt.check("PASS", "No GT-related errors")

    if other_errors:
        rpt.line(f"")
        rpt.line(f"  Other errors ({len(other_errors)} unique, showing top 10):")
        for msg, cnt in sorted(other_errors.items(), key=lambda x: x[1], reverse=True)[:10]:
            rpt.detail(f"    {cnt:>3}x  {msg}")

    # Property lookup failures
    rpt.line("")
    if prop_lookup_fails:
        rpt.check("WARN" if len(prop_lookup_fails) < 10 else "FAIL",
                   f"Property lookup failures: {len(prop_lookup_fails)}")
        seen = set()
        for p in prop_lookup_fails[:10]:
            short = u.truncate(p.strip(), 120)
            if short not in seen:
                seen.add(short)
                rpt.detail(f"    {short}")
    else:
        rpt.check("PASS", "No property lookup failures")

    if critical_lines:
        rpt.line("")
        rpt.check("FAIL", f"Critical/exception lines: {len(critical_lines)}")
        for c in critical_lines[:5]:
            rpt.detail(f"    {u.truncate(c.strip(), 120)}")
    else:
        rpt.check("PASS", "No critical exceptions")

    # =====================================================================
    # Section 7: Recent Ship Issues (last 5 min of game time)
    # =====================================================================
    rpt.header("7. Recent Ship Issues (last 5 minutes of game time)")

    has_recent = False

    if recent_no_trade:
        repeat_no_trade = {s: c for s, c in recent_no_trade.items() if c >= 3}
        if repeat_no_trade:
            has_recent = True
            rpt.check("WARN", f"Ships with repeated GT_No_Trade_Found (>=3x): {len(repeat_no_trade)}")
            for sid, cnt in sorted(repeat_no_trade.items(), key=lambda x: x[1], reverse=True)[:10]:
                rpt.detail(f"    {sid}: {cnt}x")

    if recent_rejected:
        repeat_rej = {s: c for s, c in recent_rejected.items() if c >= 2}
        if repeat_rej:
            has_recent = True
            rpt.check("WARN", f"Ships with all-trades-rejected (>=2x): {len(repeat_rej)}")
            for sid, cnt in sorted(repeat_rej.items(), key=lambda x: x[1], reverse=True)[:10]:
                rpt.detail(f"    {sid}: {cnt}x")

    if recent_timeout:
        has_recent = True
        rpt.check("FAIL", f"Ships with MD timeouts: {len(recent_timeout)}")
        for sid, cnt in sorted(recent_timeout.items(), key=lambda x: x[1], reverse=True)[:10]:
            rpt.detail(f"    {sid}: {cnt}x")

    if recent_money_blocked:
        repeat_money = {s: c for s, c in recent_money_blocked.items() if c >= 2}
        if repeat_money:
            has_recent = True
            rpt.check("WARN", f"Ships blocked by insufficient funds (>=2x in last 5 min): {len(repeat_money)}")
            for sid, cnt in sorted(repeat_money.items(), key=lambda x: x[1], reverse=True)[:10]:
                rpt.detail(f"    {sid}: {cnt}x blocked/skipped")

    if not has_recent:
        rpt.check("PASS", "No recurring ship issues in the last 5 minutes of game time")

    # =====================================================================
    # Section 8: Attached Log (complete or last N lines)
    # =====================================================================
    tail_label = f"last {tail_size:,}" if limit_tail else "complete"
    rpt.header(f"8. Attached Log ({tail_label} — {len(log_tail):,} lines)")
    rpt.line(f"  {'Last ' + str(tail_size) + ' lines' if limit_tail else 'Complete log'} ({len(log_tail):,} lines):")
    rpt.line("")
    print(u.gray(f"    (writing {len(log_tail):,} log lines to report file...)"))
    for line in log_tail:
        rpt.file_only(f"  {u.truncate(line, 300)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GalaxyTrader MK3 - Bug Report Diagnostic Tool")
    parser.add_argument("logfile", nargs="?", default="",
                        help="Path to log.log (auto-detected if omitted)")
    parser.add_argument("--tail", type=int, default=0,
                        help="Limit attached log lines to last N (default: 0 = complete log)")
    parser.add_argument("--no-zip", action="store_true",
                        help="Skip ZIP compression (output plain .txt only)")
    parser.add_argument("--no-upload", action="store_true",
                        help="Skip the upload prompt (local output only)")
    args = parser.parse_args()

    # Detect tty before fix_windows_encoding wraps stdout
    is_interactive = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    u.fix_windows_encoding()

    print()
    print(u.cyan("  ============================================="))
    print(u.cyan("   GalaxyTrader MK3 - Bug Report Generator"))
    print(u.cyan(f"   Tool version: {TOOL_VERSION}"))
    print(u.cyan("  ============================================="))
    print()

    log_path = u.require_log_file(args.logfile)

    # Report output path
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.dirname(log_path)
    report_path = os.path.join(report_dir, f"GT_BugReport_{ts}.txt")

    rpt = ReportWriter(report_path)
    rpt.line("GalaxyTrader MK3 - Bug Report")
    rpt.line(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    rpt.line(f"Tool version: {TOOL_VERSION}")

    # Run all sections
    section_system_info(rpt, log_path)
    section_session_info(rpt, log_path)
    section_mod_version(rpt, log_path)
    analyze_log(rpt, log_path, tail_size=args.tail)

    # Save report
    rpt.line("")
    rpt.line("--- END OF REPORT ---")

    output_file = report_path  # tracks the final output file (txt or zip)

    try:
        rpt.save()

        # ZIP compression (default: on)
        if not args.no_zip:
            zip_path = report_path.replace(".txt", ".zip")
            report_basename = os.path.basename(report_path)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                zf.write(report_path, report_basename)

            txt_size = os.path.getsize(report_path)
            zip_size = os.path.getsize(zip_path)
            ratio = (1 - zip_size / txt_size) * 100 if txt_size > 0 else 0

            # Remove the uncompressed .txt (ZIP contains it)
            try:
                os.remove(report_path)
            except OSError:
                pass  # ZIP was created; .txt cleanup is best-effort

            output_file = zip_path

            print()
            print(u.green("  ============================================="))
            print(u.green(f"   Report saved: {zip_path}"))
            print(u.green(f"   Size: {zip_size / 1024:.0f} KB (compressed {ratio:.0f}% from {txt_size / 1024:.0f} KB)"))
            print(u.green("  ============================================="))
        else:
            print()
            print(u.green("  ============================================="))
            print(u.green(f"   Report saved: {report_path}"))
            print(u.green("  ============================================="))
    except OSError as e:
        print()
        print(u.red(f"  ERROR: Could not save report: {e}"))
        print(u.yellow("  The report was shown above in the console."))
        print()
        output_file = ""

    # -------------------------------------------------------------------
    # Upload prompt
    # -------------------------------------------------------------------
    if output_file and os.path.isfile(output_file) and not args.no_upload:
        print()
        print(u.cyan("  ----- Upload Bug Report -----"))
        print()
        print(f"  Would you like to upload the report to 0x0.st?")
        print(f"  Retention: {UPLOAD_RETENTION} (based on file size).")
        print(f"  No account required. The link can be shared freely.")
        print()

        try:
            answer = input("  Upload? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""

        if answer in ("y", "yes"):
            print()
            print(u.yellow("  Uploading..."), end=" ", flush=True)
            link = upload_file(output_file)
            if link:
                print(u.green("Done!"))
                print()
                print(u.green("  ============================================="))
                print(u.green(f"   Download link: {link}"))
                print(u.green("  ============================================="))
                print()
                print(u.yellow("  Share this link in your bug report."))
                print()
            else:
                print(u.red("Failed!"))
                print()
                print(u.red("  Upload failed. Please attach the file manually:"))
                print(u.yellow(f"  {output_file}"))
                print()
        else:
            print()
            print(u.yellow(f"  Upload skipped. Please attach the file manually:"))
            print(u.yellow(f"  {output_file}"))
            print()
    elif output_file:
        print()
        print(u.yellow(f"  Please attach this file to your bug report:"))
        print(u.yellow(f"  {output_file}"))
        print()

    # Keep console open if double-clicked on Windows (not run from terminal)
    # Only pause if both stdin AND stdout are not a tty (true double-click scenario)
    if sys.platform == "win32" and not is_interactive:
        try:
            if sys.stdin and sys.stdin.isatty():
                input("Press Enter to exit...")
        except Exception:
            pass


if __name__ == "__main__":
    main()
