# Smart Expense Categorizer

Automatically categorize bank and UPI transactions into expense categories using keyword-based matching. Upload a CSV statement, review predicted categories, and correct any mistakes — building a labeled dataset for future ML-based improvements.

## Features

- **CSV Parser** — Auto-detects and parses two formats:
  - Bank statements (`Date, Narration, Debit, Credit, Balance`)
  - UPI app exports (`Date, Time, Transaction ID, Type, Amount, Status, Payee Name`)
- **Merchant Extraction** — Extracts clean merchant names from messy bank narrations (UPI, POS, NEFT, IMPS, BIL, ACH patterns)
- **Keyword Categorizer** — Assigns transactions to one of 7 categories: Food, Rent, Subscriptions, Travel, Utilities, Shopping, Other
- **Streamlit UI** — Upload, review, correct categories via dropdown, and save corrections locally
- **Baseline Evaluation** — 86% accuracy on a frozen 114-transaction labeled set

## Project Structure

```
Smart Expense Categorizer/
├── app.py                            # Streamlit UI
├── requirements.txt                  # Dependencies (streamlit, pandas)
├── src/
│   ├── schema.py                     # Transaction dataclass
│   ├── parser.py                     # CSV parser + merchant extraction
│   └── categorizer.py               # Keyword-based categorizer
├── tests/
│   ├── test_parser.py               # Parser and merchant extraction tests
│   └── test_categorizer.py          # Categorizer tests
├── data/
│   ├── sample_bank_statement.csv    # Sample bank format CSV
│   └── sample_upi_statement.csv     # Sample UPI format CSV
└── eval/
    ├── labeled_transactions.csv      # Frozen evaluation set (never modify)
    └── evaluate.py                   # Accuracy measurement script
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Run the Streamlit UI

```bash
streamlit run app.py
```

Upload a bank or UPI statement CSV. The app will auto-detect the format, parse transactions, and display them with predicted categories. Use the dropdowns to correct any category, then click "Save Corrections" to save to `data/corrections.csv`.

### Run Tests

```bash
python -m pytest tests/ -v
```

### Run Baseline Evaluation

```bash
python eval/evaluate.py
```

## Baseline Accuracy (v1)

| Category      | Correct | Total | Accuracy |
|---------------|---------|-------|----------|
| Food          | 26      | 34    | 76.5%    |
| Other         | 9       | 10    | 90.0%    |
| Rent          | 4       | 7     | 57.1%    |
| Shopping      | 16      | 19    | 84.2%    |
| Subscriptions | 14      | 15    | 93.3%    |
| Travel        | 17      | 17    | 100.0%   |
| Utilities     | 12      | 12    | 100.0%   |
| **Overall**   | **98**  |**114**| **86.0%**|

## Roadmap

- **v2**: Active learning — use saved corrections to retrain with a proper ML model
- **v3**: Anomaly detection for unusual spending patterns
- **v4**: Deployment with API keys and external integrations
