"""
Parse AIB Axys Africa portfolio valuation PDFs (layout table) into holdings rows.
"""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# NSE-oriented sectors for known tickers; unknowns become "Other"
SECTOR_BY_TICKER: dict[str, str] = {
    "COOP": "Banking",
    "EQT": "Banking",
    "GLD": "Commodities",
    "JUB": "Insurance",
    "KAPC": "Agriculture",
    "KCB": "Banking",
    "NCBA": "Banking",
    "SASN": "Agriculture",
    "SCBK": "Banking",
    "SCOM": "Telecom",
    "UCHM": "Retail",
    "ABSA": "Banking",
    "BAT": "Consumer",
    "IMH": "Banking",
    "BKGR": "Banking",
    "NMG": "Media",
    "CRWN": "Manufacturing",
    "KNRE": "Insurance",
    "HFCK": "Banking",
    "KPLC": "Utilities",
}

DEFAULT_THESIS_BY_TICKER: dict[str, str] = {
    "UCHM": "speculative",
    "SASN": "value",
    "KAPC": "value",
    "GLD": "core",
    "KNRE": "value",
    "HFCK": "speculative",
    "KPLC": "speculative",
    "NMG": "speculative",
}


def _is_numeric_token(tok: str) -> bool:
    t = tok.replace(",", "")
    if re.fullmatch(r"-?\d+\.\d+", t):
        return True
    if re.fullmatch(r"-?\d+", t):
        return True
    return False


def _parse_num(s: str) -> float:
    return float(s.replace(",", ""))


@dataclass
class ParsedHolding:
    ticker: str
    security_name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float


def _split_data_line(merged_line: str) -> Optional[ParsedHolding]:
    merged_line = " ".join(merged_line.split())
    m = re.match(r"^(\d+)\s+([A-Z]{2,5})\s+(.+)$", merged_line)
    if not m:
        return None
    _, ticker, rest = m.groups()
    tokens = rest.split()
    nums: list[str] = []
    i = len(tokens) - 1
    while i >= 0 and len(nums) < 6:
        if _is_numeric_token(tokens[i]):
            nums.insert(0, tokens[i])
            i -= 1
        else:
            break
    if len(nums) != 6:
        return None
    name = " ".join(tokens[: i + 1]).strip()
    try:
        qty = int(_parse_num(nums[0]))
        avg_cost = _parse_num(nums[1])
        current_price = _parse_num(nums[2])
        market_value = _parse_num(nums[3])
    except ValueError:
        return None
    return ParsedHolding(
        ticker=ticker,
        security_name=name,
        quantity=qty,
        avg_cost=avg_cost,
        current_price=current_price,
        market_value=market_value,
    )


def pdf_to_layout_text(pdf_path: Path) -> str:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        r = subprocess.run(
            [pdftotext, "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        r.check_returncode()
        return r.stdout
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "Install poppler (pdftotext) or add pypdf: pip install pypdf"
        ) from e
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_report_meta(text: str) -> tuple[Optional[str], Optional[str]]:
    """Return (valuation_as_of, market_price_as_on) if found."""
    val_as = None
    m = re.search(
        r"Portfolio\s+Valuation\s+Report\s+as\s+on\s+([^\n]+)",
        text,
        re.IGNORECASE,
    )
    if m:
        val_as = m.group(1).strip()
    mkt = None
    m = re.search(
        r"Market\s+Price\s+as\s+on\s*:?\s*([^\n]+)",
        text,
        re.IGNORECASE,
    )
    if m:
        mkt = m.group(1).strip()
    return val_as, mkt


def _split_numeric_tail(tokens: list[str], n: int = 6) -> tuple[list[str], list[str]]:
    """Last n numeric tokens and everything before them."""
    nums: list[str] = []
    i = len(tokens) - 1
    while i >= 0 and len(nums) < n:
        if _is_numeric_token(tokens[i]):
            nums.insert(0, tokens[i])
            i -= 1
        else:
            break
    return tokens[: i + 1], nums


def _merge_name_continuation(buf: str, cont_line: str) -> str:
    """
    AIB wraps long issuer names on the next line (e.g. '... KENYA' then 'LTD').
    Those continuations must sit *before* the numeric columns, not after the P/L%.
    """
    cont = cont_line.strip()
    if not cont:
        return buf
    tokens = buf.split()
    head, tail = _split_numeric_tail(tokens, 6)
    if len(tail) != 6:
        return buf.rstrip() + " " + cont
    return " ".join(head + cont.split() + tail)


def parse_holdings_from_text(text: str) -> tuple[list[ParsedHolding], Optional[str], Optional[str]]:
    val_as, mkt_as = extract_report_meta(text)
    lines = text.splitlines()
    in_table = False
    merged_lines: list[str] = []
    buf: Optional[str] = None

    row_start = re.compile(r"^\s*\d+\s+[A-Z]{2,5}\s+")

    for raw in lines:
        line = raw.rstrip()
        if not in_table:
            if "Portfolio Details" in line or re.search(r"S\.No\.\s+Code", line):
                in_table = True
            continue
        if "Total" in line and re.search(r"\d", line):
            break
        if "*** End Of Report" in line:
            break
        if not line.strip():
            continue
        if row_start.search(line):
            if buf is not None:
                merged_lines.append(buf)
            buf = line
        elif buf is not None and line.strip():
            buf = _merge_name_continuation(buf, line)
    if buf is not None:
        merged_lines.append(buf)

    holdings: list[ParsedHolding] = []
    for ml in merged_lines:
        ph = _split_data_line(ml)
        if ph:
            holdings.append(ph)
    return holdings, val_as, mkt_as


def load_prior_holdings_meta(path: Path) -> dict[str, dict[str, str]]:
    """ticker -> {thesis_bucket, notes, sector} from existing CSV."""
    if not path.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            t = (row.get("ticker") or "").strip().upper()
            if not t:
                continue
            out[t] = {
                "thesis_bucket": (row.get("thesis_bucket") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
                "sector": (row.get("sector") or "").strip(),
            }
    return out


def _strip_prior_aib_note_prefix(notes: str) -> str:
    """Remove earlier sync provenance lines so re-sync does not stack duplicates."""
    s = notes.strip()
    s = re.sub(
        r"(?:AIB valuation as [^;]+;\s*mkt px [^\s.]+\s*\.?\s*)+",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"(?:From AIB valuation[^\n.]*\.?\s*)+", "", s, flags=re.IGNORECASE)
    return s.strip().strip(".").strip()


def holdings_to_csv_rows(
    parsed: list[ParsedHolding],
    prior: dict[str, dict[str, str]],
    val_as: Optional[str],
    mkt_as: Optional[str],
) -> list[dict[str, str]]:
    meta_bits = []
    if val_as:
        meta_bits.append(f"AIB valuation as {val_as}")
    if mkt_as:
        meta_bits.append(f"mkt px {mkt_as}")
    auto_note = "; ".join(meta_bits) if meta_bits else "Synced from AIB PDF"

    rows: list[dict[str, str]] = []
    for h in sorted(parsed, key=lambda x: x.ticker):
        t = h.ticker.upper()
        prev = prior.get(t, {})
        sector = prev.get("sector") or SECTOR_BY_TICKER.get(t, "Other")
        thesis = prev.get("thesis_bucket") or DEFAULT_THESIS_BY_TICKER.get(t, "core")
        tail = _strip_prior_aib_note_prefix(prev.get("notes") or "")
        notes = f"{auto_note}. {tail}".strip().rstrip(".") if tail else auto_note
        rows.append(
            {
                "ticker": t,
                "security_name": h.security_name,
                "sector": sector,
                "quantity": str(h.quantity),
                "avg_cost": str(h.avg_cost),
                "current_price": str(h.current_price),
                "thesis_bucket": thesis,
                "notes": notes.strip(),
            }
        )
    return rows


def write_holdings_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ticker",
        "security_name",
        "sector",
        "quantity",
        "avg_cost",
        "current_price",
        "thesis_bucket",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def find_newest_pdf(search_dir: Path, patterns: list[str]) -> Optional[Path]:
    if not search_dir.is_dir():
        return None
    candidates: list[Path] = []
    for pat in patterns:
        candidates.extend(search_dir.glob(pat))
    pdfs = [p for p in candidates if p.is_file() and p.suffix.lower() == ".pdf"]
    if not pdfs:
        return None
    return max(pdfs, key=lambda p: p.stat().st_mtime)


def sync_from_pdf(
    pdf_path: Path,
    holdings_csv: Path,
    *,
    dry_run: bool = False,
    backup: bool = True,
) -> tuple[int, Optional[str]]:
    """
    Parse pdf_path and write holdings_csv. Returns (row_count, summary line).
    """
    text = pdf_to_layout_text(pdf_path)
    parsed, val_as, mkt_as = parse_holdings_from_text(text)
    if not parsed:
        raise ValueError(f"No holdings rows parsed from {pdf_path}")

    prior = load_prior_holdings_meta(holdings_csv)
    rows = holdings_to_csv_rows(parsed, prior, val_as, mkt_as)
    summary = (
        f"{pdf_path.name} → {len(rows)} positions"
        + (f" | report {val_as}" if val_as else "")
    )

    if dry_run:
        return len(rows), summary

    if backup and holdings_csv.exists():
        bak = holdings_csv.with_suffix(
            holdings_csv.suffix + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        bak.write_bytes(holdings_csv.read_bytes())

    write_holdings_csv(holdings_csv, rows)
    return len(rows), summary
