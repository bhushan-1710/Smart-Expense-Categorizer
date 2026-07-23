from src.schema import Transaction
from src.categorizer import categorize, CATEGORIES


class TestKnownMerchants:
    """Known merchants should get the correct category with high confidence."""

    def test_swiggy_is_food(self):
        tx = categorize(Transaction("2024-01-01", "Swiggy", 350, "UPI-SWIGGY-swiggy@axisbank"))
        assert tx.category == "Food"
        assert tx.confidence == 0.9

    def test_netflix_is_subscriptions(self):
        tx = categorize(Transaction("2024-01-01", "Netflix", 649, "ACH/NETFLIX INC/MONTHLY SUB"))
        assert tx.category == "Subscriptions"
        assert tx.confidence == 0.9

    def test_uber_is_travel(self):
        tx = categorize(Transaction("2024-01-01", "Uber India", 180, "UPI-UBER INDIA-uber@icici"))
        assert tx.category == "Travel"
        assert tx.confidence == 0.9

    def test_amazon_is_shopping(self):
        tx = categorize(Transaction("2024-01-01", "Amazon", 1599, "POS AMAZON RETAIL IN"))
        assert tx.category == "Shopping"
        assert tx.confidence == 0.9

    def test_bescom_is_utilities(self):
        tx = categorize(Transaction("2024-01-01", "BESCOM", 1200, "BIL/BPAY/BESCOM ELECTRI"))
        assert tx.category == "Utilities"
        assert tx.confidence == 0.9

    def test_rent_keyword(self):
        tx = categorize(Transaction("2024-01-01", "Apartment Rent", 18000, "NEFT-LANDLORD"))
        assert tx.category == "Rent"
        assert tx.confidence == 0.9


class TestAmbiguousCases:
    """Transactions matching multiple categories should get lower confidence."""

    def test_amazon_prime_matches_shopping_and_subscriptions(self):
        # "amazon" → Shopping, "prime" → Subscriptions
        tx = categorize(Transaction("2024-01-01", "Amazon Prime", 1499, "Amazon Prime membership"))
        assert tx.category in ("Shopping", "Subscriptions")
        assert tx.confidence == 0.6

    def test_jio_recharge_store(self):
        # "jio" → Subscriptions, "store" → Shopping
        tx = categorize(Transaction("2024-01-01", "Jio Store", 599, "Jio Store recharge"))
        assert tx.confidence == 0.6


class TestUnknownMerchants:
    """Unknown merchants should fall back to Other with low confidence."""

    def test_unknown_merchant(self):
        tx = categorize(Transaction("2024-01-01", "Ravi Kumar", 500, "UPI-RAVI KUMAR SH-ravi@ok"))
        assert tx.category == "Other"
        assert tx.confidence == 0.3

    def test_empty_merchant(self):
        tx = categorize(Transaction("2024-01-01", "", 100, ""))
        assert tx.category == "Other"
        assert tx.confidence == 0.3

    def test_numeric_description(self):
        tx = categorize(Transaction("2024-01-01", "12345", 200, "67890"))
        assert tx.category == "Other"
        assert tx.confidence == 0.3


class TestCategoriesAreValid:
    """Every result category should be one of the 7 defined categories."""

    def test_all_returned_categories_are_valid(self):
        test_merchants = [
            "Swiggy", "Netflix", "Uber", "Amazon", "BESCOM",
            "Rajesh Prop", "Random Person", "", "12345",
        ]
        for merchant in test_merchants:
            tx = categorize(Transaction("2024-01-01", merchant, 100, merchant))
            assert tx.category in CATEGORIES, f"{merchant} got invalid category: {tx.category}"
