import pytest
from src.parser import (
    extract_merchant_from_narration,
    parse_bank_statement,
    parse_upi_statement,
    detect_and_parse,
)


# --- Merchant extraction: all 7 messy narration examples from the plan ---

class TestMerchantExtraction:
    def test_upi_truncated_payee(self):
        narration = "UPI-RAVI KUMAR SH-ravi@ok"
        assert extract_merchant_from_narration(narration) == "RAVI KUMAR SH"

    def test_pos_truncated_store(self):
        narration = "POS 422312XXXXXX1234 BIG BAZAAR FH NE"
        assert extract_merchant_from_narration(narration) == "BIG BAZAAR FH NE"

    def test_upi_dr_many_junk_parts(self):
        narration = "UPI-DR-435678912345-ZOMATO LTD-zomato@icici-ICICI BANK-1234"
        assert extract_merchant_from_narration(narration) == "ZOMATO LTD"

    def test_imps_slash_delimited_truncated(self):
        narration = "MMT/IMPS/108234756/RAPIDO BIKE TA/SAVINGS"
        assert extract_merchant_from_narration(narration) == "RAPIDO BIKE TA"

    def test_neft_truncated_landlord(self):
        narration = "NEFT-N987612-RAJESH PROP MGMT S-SBIN0001234"
        assert extract_merchant_from_narration(narration) == "RAJESH PROP MGMT S"

    def test_ach_truncated_pvt_ltd(self):
        narration = "ACH/SPOTIFY INDIA PV/RECUR PYMNT 07"
        assert extract_merchant_from_narration(narration) == "SPOTIFY INDIA PV"

    def test_bil_truncated_utility(self):
        narration = "BIL/BPAY/000987/BESCOM ELECTRI"
        assert extract_merchant_from_narration(narration) == "BESCOM ELECTRI"


# --- Additional merchant extraction edge cases ---

class TestMerchantExtractionEdgeCases:
    def test_simple_upi(self):
        narration = "UPI-SWIGGY-swiggy@axisbank-AXIS BANK-1234567890"
        assert extract_merchant_from_narration(narration) == "SWIGGY"

    def test_fallback_plain_text(self):
        narration = "MISCELLANEOUS PAYMENT"
        assert extract_merchant_from_narration(narration) == "MISCELLANEOUS PAYMENT"

    def test_fallback_strips_long_numbers(self):
        narration = "CASH WDL ATM TC.25890123456"
        result = extract_merchant_from_narration(narration)
        # Should strip the long number and return the rest
        assert "CASH WDL ATM" in result
        assert "25890123456" not in result


# --- Bank statement parsing ---

BANK_CSV = """Date,Narration,Debit,Credit,Balance
01/03/24,UPI-SWIGGY-swiggy@axisbank-AXIS BANK-1234567890,450.00,,12350.00
02/03/24,NEFT-N112233-ACME CORP PVT LTD-HDFC0004567,,45000.00,57350.00
03/03/24,POS 422312XXXXXX1234 BIG BAZAAR FH NE,2340.00,,55010.00
15-03-2024,UPI-DOMINOS PIZZA-dominos@hdfcbank-HDFC BANK-1122334455,750.00,,54260.00
"""


class TestBankStatementParsing:
    def test_parses_debit_rows_only(self):
        txns = parse_bank_statement(BANK_CSV)
        # Row 2 is a credit (salary), should be skipped
        assert len(txns) == 3

    def test_first_transaction_fields(self):
        txns = parse_bank_statement(BANK_CSV)
        tx = txns[0]
        assert tx.date == "2024-03-01"
        assert tx.merchant == "SWIGGY"
        assert tx.amount == 450.00
        assert "SWIGGY" in tx.description

    def test_mixed_date_formats(self):
        txns = parse_bank_statement(BANK_CSV)
        # DD/MM/YY format
        assert txns[0].date == "2024-03-01"
        # DD-MM-YYYY format
        assert txns[2].date == "2024-03-15"

    def test_pos_merchant_extraction(self):
        txns = parse_bank_statement(BANK_CSV)
        assert txns[1].merchant == "BIG BAZAAR FH NE"


# --- UPI statement parsing ---

UPI_CSV = """Date,Time,Transaction ID,Type,Amount,Status,Payee Name
2024-03-01,10:15:30,TXN001,Paid,350.00,Success,Swiggy
2024-03-02,12:30:00,TXN002,Received,5000.00,Success,Amit Sharma
2024-03-03,14:22:10,TXN003,Paid,120.00,Success,Uber India
15 Mar 2024,17:30:00,TXN004,Debit,1800.00,Completed,Amazon Shopping
2024-03-05,09:00:00,TXN005,Paid,500.00,Failed,Some Restaurant
"""


class TestUpiStatementParsing:
    def test_filters_out_received_and_failed(self):
        txns = parse_upi_statement(UPI_CSV)
        # Row 2 is Received, Row 5 is Failed — both should be skipped
        assert len(txns) == 3

    def test_first_transaction_fields(self):
        txns = parse_upi_statement(UPI_CSV)
        tx = txns[0]
        assert tx.date == "2024-03-01"
        assert tx.merchant == "Swiggy"
        assert tx.amount == 350.00

    def test_dd_mon_yyyy_date_format(self):
        txns = parse_upi_statement(UPI_CSV)
        assert txns[2].date == "2024-03-15"

    def test_payee_as_merchant(self):
        txns = parse_upi_statement(UPI_CSV)
        assert txns[1].merchant == "Uber India"


# --- Auto-detection ---

class TestAutoDetection:
    def test_detects_bank_format(self):
        txns = detect_and_parse(BANK_CSV)
        assert len(txns) == 3
        assert txns[0].merchant == "SWIGGY"

    def test_detects_upi_format(self):
        txns = detect_and_parse(UPI_CSV)
        assert len(txns) == 3
        assert txns[0].merchant == "Swiggy"

    def test_unknown_format_raises_error(self):
        bad_csv = "Col1,Col2,Col3\na,b,c\n"
        with pytest.raises(ValueError, match="Unrecognized CSV format"):
            detect_and_parse(bad_csv)
