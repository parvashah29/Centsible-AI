import os
import pandas as pd
from parser import parse_bank_csv

def test():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo_data.csv')
    if not os.path.exists(data_path):
        print("❌ 'demo_data.csv' not found. Run generate_faker_csv.py first.")
        return
        
    print(f"Reading {data_path}...")
    try:
        clean_df = parse_bank_csv(data_path)
        print("\n✅ Parser successfully extracted data! Here are the first 5 rows:")
        print("-" * 50)
        print(clean_df.head())
        print("-" * 50)
        print(f"Total Rows parsed: {len(clean_df)}")
        
        expenses = clean_df[clean_df['amount'] < 0]['amount'].sum()
        income = clean_df[clean_df['amount'] > 0]['amount'].sum()
        
        print("\n📊 MVP Quick Stats:")
        print(f"Total Income: {income:.2f}")
        print(f"Total Expenses: {expenses:.2f}")
        
    except Exception as e:
        print(f"❌ Parser failed: {e}")

if __name__ == '__main__':
    test()
