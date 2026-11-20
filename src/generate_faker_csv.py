import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_US')

def generate_transactions(num_records=300):
    """
    Generates a realistic US bank statement CSV with proper income/expense proportions.
    Income is monthly salary (2x per month), expenses spread across categories.
    """

    expense_cats = {
        'Groceries':      (['Whole Foods', 'Trader Joes', 'Kroger', 'Costco', 'Safeway', 'Publix', 'Aldi'],       (40,  220),  20),
        'Dining':         (['DoorDash', 'Uber Eats', 'Starbucks', 'Chipotle', 'McDonalds', 'Panera Bread'],        (12,  80),   22),
        'Transport':      (['Uber', 'Lyft', 'Shell Gas', 'BP Gas Station', 'EZPass Toll'],                          (15,  95),   14),
        'Entertainment':  (['Netflix', 'Spotify', 'Hulu', 'AMC Theatres', 'Amazon Prime', 'Disney Plus'],           (9,   55),   8),
        'Shopping':       (['Amazon', 'Target', 'Best Buy', 'Walmart', 'Nordstrom', 'Apple Store'],                 (20,  300),  12),
        'Healthcare':     (['CVS Pharmacy', 'Walgreens', 'Rite Aid', 'Quest Diagnostics', 'Urgent Care Visit'],     (15,  250),  5),
    }

    # Rent + utilities — one fixed charge per month, not random
    monthly_fixed = [
        ('Apartment Rent',     1850.00),
        ('ConEd Electric',     110.00),
        ('Comcast Internet',   75.00),
        ('National Grid Gas',  65.00),
    ]

    # One bi-weekly paycheck
    monthly_income = 5500.00

    start_date = datetime.now() - timedelta(days=92)
    end_date   = datetime.now()

    data = []

    # --- Fixed charges (rent + utilities) once per month ---
    current = start_date.replace(day=1)
    while current < end_date:
        for desc, amount in monthly_fixed:
            pay_date = current.replace(day=random.randint(1, 5))
            if pay_date < end_date:
                data.append({
                    'Transaction Date': pay_date.strftime('%m/%d/%Y'),
                    'Description':      f"DEBIT {desc} {fake.bothify('??####').upper()}",
                    'Withdrawal (Dr)':  amount,
                    'Deposit (Cr)':     '',
                    '_sort_key':        pay_date,
                })
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # --- Bi-weekly payroll (1st and 15th of each month) ---
    current = start_date.replace(day=1)
    while current < end_date:
        for day in [1, 15]:
            pay_date = current.replace(day=day)
            if start_date <= pay_date < end_date:
                data.append({
                    'Transaction Date': pay_date.strftime('%m/%d/%Y'),
                    'Description':      f"DEBIT Payroll Direct Deposit {fake.bothify('??####').upper()}",
                    'Withdrawal (Dr)':  '',
                    'Deposit (Cr)':     monthly_income / 2,
                    '_sort_key':        pay_date,
                })
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # --- Variable expense transactions (random throughout the period) ---
    for cat, (merchants, (lo, hi), count) in expense_cats.items():
        for _ in range(count):
            merchant  = random.choice(merchants)
            prefix    = random.choice(['', 'POS ', 'DEBIT ', 'PURCHASE '])
            noise     = fake.bothify('??####').upper()
            txn_date  = fake.date_time_between(start_date=start_date, end_date=end_date)
            amount    = round(random.uniform(lo, hi), 2)
            data.append({
                'Transaction Date': txn_date.strftime('%m/%d/%Y'),
                'Description':      f"{prefix}{merchant} {noise}".strip(),
                'Withdrawal (Dr)':  amount,
                'Deposit (Cr)':     '',
                '_sort_key':        txn_date,
            })

    # Sort by date, drop helper column
    df = pd.DataFrame(data)
    df = df.sort_values('_sort_key').drop(columns=['_sort_key']).reset_index(drop=True)

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo_data.csv')
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {len(df)} realistic US transactions → demo_data.csv")
    print(f"   Approx monthly income: ${monthly_income:,.0f} | Approx fixed housing: ${sum(a for _,a in monthly_fixed):,.0f}/mo")

if __name__ == '__main__':
    generate_transactions()
