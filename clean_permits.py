
#!/usr/bin/env python3
"""
Permit Data Cleaner
====================

Takes a raw permits CSV — either from router.py's live multi-city export
(columns: date, address, city, record_type, description, contractor, status, url)
or a legacy scraper schema (issue_date, permit_type, work_description,
contractor_name, ...) — and outputs a normalized CSV/Excel file.

Field readers fall back across supported schemas so either input works;
see _first() below.

What it does:
  - Removes duplicates
  - Filters invalid and excluded records
  - Standardizes addresses, dates, and phone numbers
  - Normalizes compatible input schemas
  - Exports CSV and optional Excel files

Usage:
    python clean_permits.py input.csv
    python clean_permits.py input.csv --min-value 5000
    python clean_permits.py input.csv --output-excel

Note:
    This utility normalizes and exports records; it does NOT anonymize,
    de-identify, or determine whether data is lawful to publish. Inputs may
    contain personal or business information. Review and minimize fields
    before sharing output. Spreadsheet-formula-like text is escaped on export.
"""

import csv
import re
import sys
import os
import argparse
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import PatternFill, Font
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

OUTPUT_DIR = "./output"

# ─── FILTERS ──────────────────────────────────────────────────────────────────

# [REDACTED] Production exclusion criteria omitted to protect
# proprietary record-selection logic.

DEFAULT_MIN_VALUE = 0


# ─── SCHEMA COMPAT ────────────────────────────────────────────────────────────
# router.py's live CSV export and legacy scraper exports use different
# column names for equivalent data. Field readers support both schemas.

def _first(row: dict, *keys) -> str:
    for k in keys:
        v = row.get(k)
        if v:
            return v
    return ""


def _split_city_state(raw_city: str) -> tuple[str, str]:
    """Separate a combined city/state display value when present."""
    raw_city = (raw_city or "").strip()
    m = re.match(r"^(.*),\s*([A-Za-z]{2})$", raw_city)
    if m:
        return m.group(1).strip(), m.group(2).upper()
    return raw_city, ""


# ─── PROPRIETARY LEAD SCORING ─────────────────────────────────────────────────
# [REDACTED] Production scoring criteria, weighting, and prioritization
# implementation intentionally omitted to protect proprietary IP.


# ─── CLEANERS ─────────────────────────────────────────────────────────────────

def clean_address(addr: str) -> str:
    if not addr:
        return ""
    addr = addr.strip().upper()
    # Normalize common abbreviations
    addr = re.sub(r"\bST\b", "ST", addr)
    addr = re.sub(r"\bAVE\b", "AVE", addr)
    addr = re.sub(r"\bBLVD\b", "BLVD", addr)
    addr = re.sub(r"\bDR\b", "DR", addr)
    addr = re.sub(r"\s+", " ", addr)
    return addr


def clean_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone.strip()


def clean_date(d: str) -> str:
    if not d:
        return ""
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y%m%d"]:
        try:
            return datetime.strptime(d.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return d.strip()


def clean_value(v: str) -> str:
    if not v:
        return ""
    digits = re.sub(r"[^0-9.]", "", v)
    try:
        return f"${float(digits):,.0f}"
    except ValueError:
        return v.strip()


def should_exclude(row: dict) -> bool:
    """
    [REDACTED] Production record-exclusion criteria omitted.

    The production implementation is intentionally unavailable in
    this portfolio copy.
    """
    return False


def has_valid_address(row: dict) -> bool:
    addr = row.get("address", "").strip()
    return bool(addr) and len(addr) > 5 and any(c.isdigit() for c in addr)


# ─── DEDUP ────────────────────────────────────────────────────────────────────

def deduplicate(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = (
            row.get("permit_number", ""),
            row.get("address", ""),
            row.get("issue_date", "")
        )
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


# ─── MAIN CLEAN FUNCTION ─────────────────────────────────────────────────────

def clean(rows: list[dict], min_value: float = 0) -> list[dict]:
    cleaned = []
    stats = {
        "total": len(rows),
        "no_address": 0,
        "excluded": 0,
        "low_value": 0,
        "dupes": 0
    }

    for row in rows:
        # Must have a valid address
        if not has_valid_address(row):
            stats["no_address"] += 1
            continue

        # Apply production exclusion criteria
        if should_exclude(row):
            stats["excluded"] += 1
            continue

        # Value filter
        if min_value > 0:
            val_str = re.sub(
                r"[^0-9.]",
                "",
                row.get("estimated_value", "") or "0"
            )
            val = float(val_str) if val_str else 0
            if val < min_value:
                stats["low_value"] += 1
                continue

        # Support multiple compatible input schemas.
        work_desc = _first(
            row, "description", "work_description"
        ).strip()

        contractor = _first(
            row, "contractor", "contractor_name", "contractor_company"
        ).strip().title()

        source = _first(row, "url", "source_url", "permit_url")
        issue_date = _first(row, "date", "issue_date")

        permit_type = _first(
            row, "record_type", "permit_type", "permit_type_desc"
        ).strip().title()

        city_name, city_state = _split_city_state(row.get("city", ""))

        city_name = (
            city_name or row.get("city", "")
        ).strip().title()

        state = (
            row.get("state", "") or city_state
        ).strip().upper()

        cleaned.append({
            "permit_number": row.get("permit_number", "").strip(),
            "issue_date": clean_date(issue_date),
            "address": clean_address(row.get("address", "")),
            "city": city_name,
            "state": state,
            "zip": row.get("zip", "").strip(),
            "permit_type": permit_type,
            "work_description": work_desc,
            "contractor_name": contractor,
            "contractor_phone": clean_phone(
                row.get("contractor_phone", "")
            ),
            "contractor_license": row.get(
                "contractor_license", ""
            ).strip(),
            "estimated_value": clean_value(
                row.get("estimated_value", "")
            ),
            "owner_name": row.get(
                "owner_name", ""
            ).strip().title(),
            "status": row.get(
                "status", "Active"
            ).strip().title(),
            "source_url": source,
        })

    # Dedup
    before = len(cleaned)
    cleaned = deduplicate(cleaned)
    stats["dupes"] = before - len(cleaned)

    # Sort records
    cleaned.sort(
        key=lambda r: (r.get("issue_date", "")),
        reverse=False
    )

    print(f"\n[Clean Stats]")
    print(f"  Input rows:        {stats['total']}")
    print(f"  No address:        {stats['no_address']}")
    print(f"  Excluded:          {stats['excluded']}")
    print(f"  Below min value:   {stats['low_value']}")
    print(f"  Duplicates:        {stats['dupes']}")
    print(f"  Clean output rows: {len(cleaned)}")

    return cleaned


# ─── EXPORT ───────────────────────────────────────────────────────────────────

COLUMNS = [
    "issue_date", "permit_number", "address", "city", "state", "zip",
    "permit_type", "work_description", "contractor_name", "contractor_phone",
    "contractor_license", "estimated_value", "owner_name", "status", "source_url",
]


def _spreadsheet_safe(value):
    """Keep untrusted text from being interpreted as a spreadsheet formula."""
    if value is None:
        return ""
    text = str(value)
    if re.match(r"^[\s\x00-\x1f]*[=+\-@]", text):
        return "'" + text
    return value


def export_csv(rows: list[dict], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=COLUMNS,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows([
            {key: _spreadsheet_safe(value) for key, value in row.items()}
            for row in rows
        ])
    print(f"[OK] CSV → {path}")


def export_excel(rows: list[dict], path: str):
    if not EXCEL_AVAILABLE:
        print("[WARN] openpyxl not installed. Run: pip install openpyxl")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Permits"

    # Header row
    ws.append(COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="FF37474F")
        cell.font = Font(bold=True, color="FFFFFFFF")

    # Data rows
    for row in rows:
        ws.append([_spreadsheet_safe(row.get(col, "")) for col in COLUMNS])

    # Auto-width
    for col in ws.columns:
        max_len = max(
            (len(str(c.value or "")) for c in col),
            default=0
        )
        ws.column_dimensions[
            col[0].column_letter
        ].width = min(max_len + 2, 50)

    wb.save(path)
    print(f"[OK] Excel → {path}")


# ─── GENERIC CLEANER ──────────────────────────────────────────────────────────

GENERIC_COLUMNS = [
    "date", "name", "address", "city",
    "record_type", "description", "status", "url"
]


def clean_generic(rows: list[dict]) -> list[dict]:
    """
    Generic cleaner for compatible non-permit record types.
    Removes rows with neither address nor name, deduplicates, and sorts.
    """
    stats = {"total": len(rows), "no_identity": 0, "dupes": 0}
    cleaned = []
    seen = set()

    for row in rows:
        address = row.get("address", "").strip()
        name = row.get("name", "").strip()

        # Must have at least a name or a valid address
        if not name and (not address or len(address) < 5):
            stats["no_identity"] += 1
            continue

        key = (address.upper(), name.upper(), row.get("date", ""))
        if key in seen:
            stats["dupes"] += 1
            continue
        seen.add(key)

        cleaned.append({
            "date": clean_date(row.get("date", "")),
            "name": name.title(),
            "address": clean_address(address),
            "city": row.get("city", "").strip().title(),
            "record_type": row.get("record_type", "").strip().title(),
            "description": row.get("description", "").strip().title(),
            "status": row.get("status", "").strip().title(),
            "url": row.get("url", "").strip(),
        })

    # Sort by date
    cleaned.sort(
        key=lambda r: r.get("date", ""),
        reverse=True
    )

    print(f"\n[Clean Stats]")
    print(f"  Input rows:        {stats['total']}")
    print(f"  No identity:       {stats['no_identity']}")
    print(f"  Duplicates:        {stats['dupes']}")
    print(f"  Clean output rows: {len(cleaned)}")

    return cleaned


def export_excel_generic(rows: list[dict], path: str):
    if not EXCEL_AVAILABLE:
        print("[WARN] openpyxl not installed. Run: pip install openpyxl")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Records"

    ws.append(GENERIC_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = PatternFill("solid", fgColor="FF37474F")

    for row in rows:
        ws.append([_spreadsheet_safe(row.get(col, "")) for col in GENERIC_COLUMNS])

    for col in ws.columns:
        max_len = max(
            (len(str(c.value or "")) for c in col),
            default=0
        )
        ws.column_dimensions[
            col[0].column_letter
        ].width = min(max_len + 2, 50)

    wb.save(path)
    print(f"[OK] Excel → {path}")


def export_csv_generic(rows: list[dict], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=GENERIC_COLUMNS,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows([
            {key: _spreadsheet_safe(value) for key, value in row.items()}
            for row in rows
        ])
    print(f"[OK] CSV → {path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Normalize and export structured records."
    )

    parser.add_argument(
        "input",
        help="Input CSV file"
    )

    parser.add_argument(
        "--min-value",
        type=float,
        default=DEFAULT_MIN_VALUE,
        help="Exclude records below a specified value"
    )

    parser.add_argument(
        "--output-excel",
        action="store_true",
        help="Also export .xlsx"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] File not found: {args.input}")
        sys.exit(1)

    with open(
        args.input,
        newline="",
        encoding="utf-8"
    ) as f:
        rows = list(csv.DictReader(f))

    cleaned = clean(rows, min_value=args.min_value)

    if not cleaned:
        print("[!] No rows after cleaning. Check your input file.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base = os.path.splitext(
        os.path.basename(args.input)
    )[0].replace("_raw", "")

    csv_path = os.path.join(
        OUTPUT_DIR,
        f"{base}_clean.csv"
    )

    excel_path = os.path.join(
        OUTPUT_DIR,
        f"{base}_clean.xlsx"
    )

    export_csv(cleaned, csv_path)

    if args.output_excel:
        export_excel(cleaned, excel_path)


if __name__ == "__main__":
    main()
