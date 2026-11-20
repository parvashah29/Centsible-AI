"""
Phase 2 — Synthetic Training Data Generator
Generates 10,000 labelled bank transactions across 10 categories for classifier training.
Currency: USD | Context: United States
Project: Centsible AI
"""

import pandas as pd
from faker import Faker
import random
import os

fake = Faker('en_US')

# US Merchant pools per category
CATEGORY_MERCHANTS = {
    'Groceries': [
        'Whole Foods', 'Trader Joes', 'Kroger', 'Safeway', 'Publix',
        'Walmart Grocery', 'Target Grocery', 'Costco', 'Aldi', 'HEB',
        'Wegmans', 'Stop and Shop', 'Giant Food', 'Meijer', 'Sprouts'
    ],
    'Dining': [
        'DoorDash', 'Uber Eats', 'Grubhub', 'Starbucks', 'McDonalds',
        'Chipotle', 'Chick-fil-A', 'Subway', 'Panera Bread', 'Dominos',
        'Pizza Hut', 'Taco Bell', 'Shake Shack', 'Five Guys', 'Panda Express'
    ],
    'Transport': [
        'Uber', 'Lyft', 'Shell Gas', 'BP Gas Station', 'Chevron',
        'EZPass Toll', 'Metro Transit', 'Amtrak', 'Delta Airlines',
        'Southwest Airlines', 'United Airlines', 'Hertz Car Rental', 'Zipcar'
    ],
    'Rent & Housing': [
        'Rent Payment', 'Apartment Rent', 'ConEd Electric', 'PG&E Utility',
        'PSEG Electric', 'National Grid Gas', 'Comcast Internet',
        'AT&T Internet', 'Verizon Home', 'Water Bill', 'HOA Fee', 'Renter Insurance'
    ],
    'Entertainment': [
        'Netflix', 'Spotify', 'Amazon Prime', 'Hulu', 'Disney Plus',
        'HBO Max', 'Apple TV Plus', 'YouTube Premium', 'AMC Theatres',
        'Regal Cinemas', 'Xbox Game Pass', 'PlayStation Network', 'Audible'
    ],
    'Shopping': [
        'Amazon', 'Target', 'Walmart', 'Best Buy', 'Apple Store',
        'Macys', 'Nordstrom', 'Gap', 'H&M', 'ZARA',
        'Nike', 'Adidas', 'Etsy', 'Wayfair', 'IKEA'
    ],
    'Healthcare': [
        'CVS Pharmacy', 'Walgreens', 'Rite Aid', 'GoodRx', 'Quest Diagnostics',
        'LabCorp', 'Teladoc Health', 'WebMD Care', 'HealthNet Copay',
        'Dental Office', 'Eye Care Associates', 'Urgent Care Visit'
    ],
    'Education': [
        'Coursera', 'Udemy', 'LinkedIn Learning', 'Chegg',
        'College Tuition', 'University Fee', 'Campus Bookstore',
        'Khan Academy Donate', 'Skillshare', 'MasterClass', 'Duolingo Plus'
    ],
    'Income': [
        'Payroll Direct Deposit', 'Salary Credit', 'Freelance Payment',
        'Consulting Fee', 'Interest Credit', 'Dividend Credit',
        'Bonus Payment', 'Side Hustle Income', 'ACH Transfer In'
    ],
    'Transfers': [
        'Zelle Transfer', 'Venmo Payment', 'PayPal Transfer',
        'CashApp Send', 'Wire Transfer', 'ACH Transfer',
        'Bank Transfer', 'Check Deposit'
    ]
}

# Real US bank transaction prefixes
BANK_PREFIXES = [
    '', '', '',  # weight towards no prefix
    'POS ', 'ACH ', 'DEBIT ', 'CHK ', 'ATM ', 'PURCHASE '
]

# USD amount ranges
AMOUNT_RANGES = {
    'Groceries':      (20,   350),
    'Dining':         (8,    120),
    'Transport':      (5,    200),
    'Rent & Housing': (150,  3500),
    'Entertainment':  (8,    60),
    'Shopping':       (15,   800),
    'Healthcare':     (15,   500),
    'Education':      (20,   3000),
    'Income':         (2000, 12000),
    'Transfers':      (20,   3000),
}

CLASS_WEIGHTS = {
    'Groceries':      18,
    'Dining':         16,
    'Transport':      14,
    'Rent & Housing': 10,
    'Entertainment':  8,
    'Shopping':       12,
    'Healthcare':     6,
    'Education':      5,
    'Income':         5,
    'Transfers':      6,
}


def generate_training_data(num_records: int = 10000, output_path: str = None) -> pd.DataFrame:
    categories = list(CATEGORY_MERCHANTS.keys())
    weights    = [CLASS_WEIGHTS[c] for c in categories]
    records    = []

    for _ in range(num_records):
        cat      = random.choices(categories, weights=weights, k=1)[0]
        merchant = random.choice(CATEGORY_MERCHANTS[cat])
        prefix   = random.choice(BANK_PREFIXES)
        noise    = fake.bothify(text='??####').upper()
        description = f"{prefix}{merchant} {noise}".strip()

        lo, hi  = AMOUNT_RANGES[cat]
        amount  = round(random.uniform(lo, hi), 2)
        txn_type = 'Credit' if cat == 'Income' else 'Debit'

        records.append({
            'description': description,
            'amount':      amount,
            'type':        txn_type,
            'category':    cat
        })

    df = pd.DataFrame(records).sample(frac=1, random_state=42).reset_index(drop=True)

    if output_path:
        df.to_csv(output_path, index=False)
        print(f"✅ Generated {num_records} training records → {output_path}")

    return df


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'training_data.csv')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df = generate_training_data(10000, output_path=out)
    print(df['category'].value_counts())
