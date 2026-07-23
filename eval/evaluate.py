import csv
import sys
import os
from collections import defaultdict

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.schema import Transaction
from src.categorizer import categorize


def load_labeled_data(filepath: str) -> list[dict]:
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate(filepath: str) -> None:
    rows = load_labeled_data(filepath)

    correct = 0
    total = 0
    per_category_correct = defaultdict(int)
    per_category_total = defaultdict(int)
    mismatches = []

    for row in rows:
        tx = Transaction(
            date=row["date"],
            merchant=row["merchant"],
            amount=float(row["amount"]),
            description=row["description"],
        )
        result = categorize(tx)
        expected = row["expected_category"]

        per_category_total[expected] += 1
        total += 1

        if result.category == expected:
            correct += 1
            per_category_correct[expected] += 1
        else:
            mismatches.append({
                "merchant": row["merchant"],
                "expected": expected,
                "predicted": result.category,
                "confidence": result.confidence,
            })

    print(f"\n{'='*60}")
    print(f"BASELINE EVALUATION — Keyword Categorizer v1")
    print(f"{'='*60}")
    print(f"Total transactions: {total}")
    print(f"Correct: {correct}")
    print(f"Overall accuracy: {correct / total:.1%}")
    print(f"\n{'--- Per-Category Breakdown ---'}")
    print(f"{'Category':<16} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    print(f"{'-'*44}")

    for cat in sorted(per_category_total.keys()):
        cat_correct = per_category_correct[cat]
        cat_total = per_category_total[cat]
        accuracy = cat_correct / cat_total if cat_total > 0 else 0
        print(f"{cat:<16} {cat_correct:>8} {cat_total:>8} {accuracy:>10.1%}")

    if mismatches:
        print(f"\n{'--- Misclassifications ---'}")
        print(f"{'Merchant':<25} {'Expected':<16} {'Predicted':<16} {'Conf':>6}")
        print(f"{'-'*65}")
        for m in mismatches:
            print(
                f"{m['merchant']:<25} {m['expected']:<16} "
                f"{m['predicted']:<16} {m['confidence']:>6.2f}"
            )


if __name__ == "__main__":
    eval_file = os.path.join(os.path.dirname(__file__), "labeled_transactions.csv")
    evaluate(eval_file)
