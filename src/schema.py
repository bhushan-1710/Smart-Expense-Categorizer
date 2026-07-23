from dataclasses import dataclass, field


@dataclass
class Transaction:
    date: str          # normalized to YYYY-MM-DD
    merchant: str      # cleaned merchant/payee name
    amount: float      # always positive (debits only in v1)
    description: str   # raw narration/description from CSV
    category: str = ""
    confidence: float = 0.0
