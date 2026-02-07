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
from collections import Counter, defaultdict
from datetime import datetime


import gt_log_utils as u

# ---------------------------------------------------------------------------
# Version
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

    def save(self):
        with open(self._filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(self._lines))
            f.write("\n")


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

    # Errors
    error_lines: list[str] = []
    prop_lookup_fails: list[str] = []
    critical_lines: list[str] = []

    # Recent ship issues (collected for last 5 min of game time, filled after first pass for max_time)
    recent_no_trade: Counter = Counter()    # ship -> count
    recent_rejected: Counter = Counter()    # ship -> count
    recent_timeout: Counter = Counter()     # ship -> count

    # Raw tail (last 100 GT lines)
    gt_tail: list[str] = []

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

            # GT-specific analysis
            if not RE_GT_TAG.search(stripped) and "GT_Find_" not in stripped and "GT_No_Trade" not in stripped and "GT_Trade" not in stripped:
                continue

            gt_lines += 1

            # GT tail
            gt_tail.append(stripped)
            if len(gt_tail) > tail_size:
                gt_tail.pop(0)

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

    if not has_recent:
        rpt.check("PASS", "No recurring ship issues in the last 5 minutes of game time")

    # =====================================================================
    # Section 8: Raw Tail (last 100 GT log lines)
    # =====================================================================
    rpt.header("8. Last GT Log Lines (for context)")
    rpt.line(f"  Showing last {len(gt_tail)} GT-related log lines:")
    rpt.line("")
    for line in gt_tail:
        rpt.detail(f"  {u.truncate(line, 160)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GalaxyTrader MK3 - Bug Report Diagnostic Tool")
    parser.add_argument("logfile", nargs="?", default="",
                        help="Path to log.log (auto-detected if omitted)")
    parser.add_argument("--tail", type=int, default=500,
                        help="Number of GT log lines to include at the end of the report (default: 500)")
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

    try:
        rpt.save()
        print()
        print(u.green("  ============================================="))
        print(u.green(f"   Report saved: {report_path}"))
        print(u.green("  ============================================="))
        print()
        print(u.yellow("  Please attach this file to your bug report."))
        print()
    except OSError as e:
        print()
        print(u.red(f"  ERROR: Could not save report: {e}"))
        print(u.yellow("  The report was shown above in the console."))
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
