import re
import io
from datetime import datetime

import pandas as pd

from src.schema import Transaction


KNOWN_BANKS = {
    "AXIS BANK", "HDFC BANK", "ICICI BANK", "SBI", "STATE BANK",
    "YES BANK", "KOTAK BANK", "IDFC BANK", "FEDERAL BANK",
    "CANARA BANK", "PNB", "BOB", "UNION BANK", "INDUSIND BANK",
}

# Column sets for auto-detection (all lowercased for comparison)
BANK_COLUMNS = {"date", "narration", "debit", "credit", "balance"}
UPI_COLUMNS = {"date", "time", "transaction id", "type", "amount", "status", "payee name"}


def _is_bank_name(text: str) -> bool:
    upper = text.strip().upper()
    if upper in KNOWN_BANKS:
        return True
    # IFSC codes: 4 uppercase letters followed by 7 digits
    if re.match(r"^[A-Z]{4}\d{7}$", upper):
        return True
    return False


def extract_merchant_from_narration(narration: str) -> str:
    """Extract merchant name from a bank statement narration.

    Tries pattern-specific extraction for UPI, POS, NEFT, IMPS/MMT, BIL,
    and ACH narration formats. Falls back to a cleaned version of the raw
    narration if no pattern matches.
    """
    text = narration.strip()
    upper = text.upper()

    # Pattern 1: UPI transactions
    if upper.startswith("UPI"):
        parts = text.split("-")
        for part in parts:
            p = part.strip()
            if p.upper() in ("UPI", "DR", "CR"):
                continue
            if p.isdigit():
                continue
            if "@" in p:
                continue
            if _is_bank_name(p):
                continue
            return p

    # Pattern 2: POS transactions
    if upper.startswith("POS"):
        remainder = re.sub(
            r"^POS\s+\d{6}X+\d{4}\s*", "", text, flags=re.IGNORECASE
        )
        if remainder.strip():
            return remainder.strip()

    # Pattern 3: NEFT transactions
    if upper.startswith("NEFT"):
        parts = text.split("-")
        if len(parts) >= 3:
            return parts[2].strip()

    # Pattern 4: IMPS/MMT transactions
    if upper.startswith(("MMT", "IMPS")):
        parts = text.split("/")
        for part in parts:
            p = part.strip()
            if p.upper() in ("MMT", "IMPS"):
                continue
            if p.isdigit():
                continue
            if p.upper() in ("SAVINGS", "CURRENT"):
                continue
            return p

    # Pattern 5: Bill payments
    if upper.startswith("BIL"):
        parts = text.split("/")
        for part in reversed(parts):
            p = part.strip()
            if p.upper() in ("BIL", "ONL", "BPAY"):
                continue
            if p.isdigit():
                continue
            return p

    # Pattern 6: ACH / direct debits
    if upper.startswith("ACH"):
        parts = text.split("/")
        if len(parts) >= 2:
            return parts[1].strip()

    # Fallback: strip long digit sequences, collapse whitespace
    cleaned = re.sub(r"\b\d{10,}\b", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else text


def _normalize_date(date_str: str) -> str:
    """Try several common date formats and return YYYY-MM-DD."""
    date_str = date_str.strip()
    formats = [
        "%d/%m/%y",     # 15/03/24
        "%d/%m/%Y",     # 15/03/2024
        "%d-%m-%Y",     # 15-03-2024
        "%d-%m-%y",     # 15-03-24
        "%Y-%m-%d",     # 2024-03-15
        "%d %b %Y",     # 15 Mar 2024
        "%d %B %Y",     # 15 March 2024
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: '{date_str}'")


def parse_bank_statement(csv_content: str) -> list[Transaction]:
    """Parse a bank statement CSV (Date, Narration, Debit, Credit, Balance).

    Keeps only debit rows (expenses). Skips rows with no debit amount.
    """
    df = pd.read_csv(io.StringIO(csv_content))
    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []
    for _, row in df.iterrows():
        debit = row.get("debit")
        # Skip rows with no debit (credits, opening balance, etc.)
        if pd.isna(debit) or debit == "" or float(debit) == 0:
            continue

        narration = str(row.get("narration", "")).strip()
        transactions.append(Transaction(
            date=_normalize_date(str(row["date"])),
            merchant=extract_merchant_from_narration(narration),
            amount=float(debit),
            description=narration,
        ))
    return transactions


def parse_upi_statement(csv_content: str) -> list[Transaction]:
    """Parse a UPI app export CSV (Date, Time, Transaction ID, Type, Amount, Status, Payee Name).

    Keeps only successful debit/paid/sent transactions.
    """
    df = pd.read_csv(io.StringIO(csv_content))
    df.columns = [c.strip().lower() for c in df.columns]

    valid_types = {"debit", "paid", "sent"}
    valid_statuses = {"success", "completed"}

    transactions = []
    for _, row in df.iterrows():
        tx_type = str(row.get("type", "")).strip().lower()
        status = str(row.get("status", "")).strip().lower()

        if tx_type not in valid_types or status not in valid_statuses:
            continue

        payee = str(row.get("payee name", "")).strip()
        transactions.append(Transaction(
            date=_normalize_date(str(row["date"])),
            merchant=payee,
            amount=float(row["amount"]),
            description=payee,
        ))
    return transactions


def detect_and_parse(csv_content: str) -> list[Transaction]:
    """Auto-detect CSV format from headers and parse accordingly."""
    first_line = csv_content.strip().split("\n")[0]
    headers = {h.strip().lower() for h in first_line.split(",")}

    if BANK_COLUMNS.issubset(headers):
        return parse_bank_statement(csv_content)
    if UPI_COLUMNS.issubset(headers):
        return parse_upi_statement(csv_content)

    raise ValueError(
        f"Unrecognized CSV format. Headers found: {headers}. "
        f"Expected bank statement columns {BANK_COLUMNS} "
        f"or UPI export columns {UPI_COLUMNS}."
    )
