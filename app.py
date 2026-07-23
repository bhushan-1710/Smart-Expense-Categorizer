import os
import streamlit as st
import pandas as pd

from src.parser import detect_and_parse
from src.categorizer import categorize, CATEGORIES


CORRECTIONS_PATH = os.path.join("data", "corrections.csv")


st.set_page_config(page_title="Smart Expense Categorizer", layout="wide")
st.title("Smart Expense Categorizer")
st.caption("Upload a bank or UPI statement CSV to categorize your expenses.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    csv_content = uploaded_file.read().decode("utf-8")

    try:
        transactions = detect_and_parse(csv_content)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    if not transactions:
        st.warning("No expense transactions found in the uploaded file.")
        st.stop()

    # Categorize each transaction
    categorized = [categorize(tx) for tx in transactions]

    # Build a DataFrame for display and editing
    df = pd.DataFrame([
        {
            "Date": tx.date,
            "Merchant": tx.merchant,
            "Amount": tx.amount,
            "Description": tx.description,
            "Category": tx.category,
            "Confidence": tx.confidence,
        }
        for tx in categorized
    ])

    st.subheader(f"Parsed Transactions ({len(df)} expenses)")

    # Editable category column via per-row dropdowns
    edited_categories = []
    for i, row in df.iterrows():
        cols = st.columns([1.2, 2, 1, 3, 2, 1])
        cols[0].text(row["Date"])
        cols[1].text(row["Merchant"])
        cols[2].text(f"₹{row['Amount']:,.2f}")
        cols[3].text(row["Description"][:50])

        current_index = CATEGORIES.index(row["Category"]) if row["Category"] in CATEGORIES else 6
        selected = cols[4].selectbox(
            "Category",
            CATEGORIES,
            index=current_index,
            key=f"cat_{i}",
            label_visibility="collapsed",
        )
        edited_categories.append(selected)

        confidence_pct = f"{row['Confidence']:.0%}"
        cols[5].text(confidence_pct)

    # Header row above the transaction list (shown via markdown for clarity)
    # The columns above already serve as the table.

    st.divider()

    if st.button("Save Corrections"):
        df["Category"] = edited_categories
        # Append to corrections file
        write_header = not os.path.exists(CORRECTIONS_PATH)
        os.makedirs(os.path.dirname(CORRECTIONS_PATH), exist_ok=True)
        df.to_csv(
            CORRECTIONS_PATH,
            mode="a",
            header=write_header,
            index=False,
        )
        st.success(f"Saved {len(df)} transactions to {CORRECTIONS_PATH}")
