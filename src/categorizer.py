from src.schema import Transaction


CATEGORIES = ["Food", "Rent", "Subscriptions", "Travel", "Utilities", "Shopping", "Other"]

KEYWORD_MAP = {
    "Food": [
        "swiggy", "zomato", "dominos", "pizza", "restaurant", "cafe", "food",
        "kitchen", "biryani", "burger", "mcdonalds", "kfc", "starbucks",
        "chai", "bakery",
    ],
    "Rent": [
        "rent", "landlord", "house", "flat", "apartment", "property", "pg",
        "hostel",
    ],
    "Subscriptions": [
        "netflix", "spotify", "hotstar", "prime", "youtube", "subscription",
        "membership", "jio", "airtel", "vodafone", "plan", "recharge",
    ],
    "Travel": [
        "uber", "ola", "rapido", "irctc", "railway", "flight", "makemytrip",
        "goibibo", "metro", "cab", "bus", "petrol", "fuel",
    ],
    "Utilities": [
        "electricity", "water", "gas", "broadband", "wifi", "internet",
        "bill", "maintenance", "bescom", "power",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "mall", "store", "shop",
        "market", "retail", "meesho", "nykaa",
    ],
}


def categorize(transaction: Transaction) -> Transaction:
    """Assign a category and confidence to a transaction using keyword matching.

    Confidence values are fixed heuristics for this baseline, NOT calibrated
    probabilities. They indicate match quality for the UI, nothing more.
    """
    text = (transaction.merchant + " " + transaction.description).lower()

    # Count keyword hits per category
    hits = {}
    for category, keywords in KEYWORD_MAP.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            hits[category] = count

    if len(hits) == 1:
        category = next(iter(hits))
        confidence = 0.9
    elif len(hits) > 1:
        category = max(hits, key=hits.get)
        confidence = 0.6
    else:
        category = "Other"
        confidence = 0.3

    return Transaction(
        date=transaction.date,
        merchant=transaction.merchant,
        amount=transaction.amount,
        description=transaction.description,
        category=category,
        confidence=confidence,
    )
