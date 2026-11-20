"""
Phase 2 — Spending Aggregator & Financial Profile Builder
Takes classified transactions and produces a structured JSON financial profile.
Currency: USD ($)
Project: Centsible AI
"""

import pandas as pd
import numpy as np
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from parser import parse_statement
from classifier import predict_category

import joblib


# Categories excluded from "spending" analysis (internal money movement)
EXCLUDE_FROM_SPENDING = {'Transfers', 'Uncategorised'}
INCOME_CATEGORIES     = {'Income'}


def classify_dataframe(df: pd.DataFrame, pipeline) -> pd.DataFrame:
    """
    Applies the classifier to every transaction in df.
    Adds 'category' and 'confidence' columns.
    """
    results = df['description'].apply(lambda desc: predict_category(desc, pipeline))
    df = df.copy()
    df['category']   = results.apply(lambda r: r['category'])
    df['confidence'] = results.apply(lambda r: r['confidence'])
    return df


def build_financial_profile(df: pd.DataFrame) -> dict:
    """
    Generates a comprehensive financial profile dict from a classified DataFrame.

    Expected df columns: date (datetime), description (str), amount (float), category (str)

    Returns a structured dict ready to be JSON-serialised and injected into LLM prompts.
    """
    df = df.copy()
    df['month'] = df['date'].dt.to_period('M').astype(str)

    # ── Drop partial months (< 10 days of data) to avoid skewed MoM stats ────
    days_per_month = df.groupby('month')['date'].apply(lambda x: x.dt.day.nunique())
    full_months    = days_per_month[days_per_month >= 10].index.tolist()
    df             = df[df['month'].isin(full_months)]

    # ── Income ────────────────────────────────────────────────────────────────
    income_df  = df[df['category'].isin(INCOME_CATEGORIES)]
    expense_df = df[~df['category'].isin(INCOME_CATEGORIES | EXCLUDE_FROM_SPENDING) & (df['amount'] != 0)]

    # Force expenses to be positive for readability
    expense_df = expense_df.copy()
    expense_df['amount'] = expense_df['amount'].abs()

    total_income   = income_df['amount'].abs().sum()
    total_expenses = expense_df['amount'].sum()
    net_savings    = total_income - total_expenses
    savings_rate   = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

    # ── Monthly breakdown ─────────────────────────────────────────────────────
    months_present   = sorted(df['month'].unique())
    num_months       = max(len(months_present), 1)
    avg_monthly_income   = round(total_income / num_months, 2)
    avg_monthly_expenses = round(total_expenses / num_months, 2)

    monthly_income_series = (
        income_df.groupby('month')['amount'].apply(lambda x: round(x.abs().sum(), 2))
        .to_dict()
    )
    monthly_expense_series = (
        expense_df.groupby('month')['amount'].sum().round(2)
        .to_dict()
    )

    # ── Category breakdown ────────────────────────────────────────────────────
    category_totals = (
        expense_df.groupby('category')['amount']
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .to_dict()
    )

    category_pct = {
        cat: round(amt / total_expenses * 100, 1) if total_expenses > 0 else 0.0
        for cat, amt in category_totals.items()
    }

    # Top 3 spending categories
    top_categories = list(category_totals.keys())[:3]

    # ── Merchant intelligence ─────────────────────────────────────────────────
    top_merchants = (
        expense_df.groupby('description')['amount']
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .head(10)
        .to_dict()
    )

    # ── Month-over-month expense trend ────────────────────────────────────────
    mom_expense = {}
    sorted_months = sorted(monthly_expense_series.keys())
    for i in range(1, len(sorted_months)):
        prev  = monthly_expense_series.get(sorted_months[i - 1], 0)
        curr  = monthly_expense_series.get(sorted_months[i], 0)
        change_pct = round(((curr - prev) / prev * 100), 1) if prev else 0.0
        mom_expense[sorted_months[i]] = change_pct

    # ── 50/30/20 benchmark ────────────────────────────────────────────────────
    benchmark_50_30_20 = {
        'needs_budget_50pct':  round(avg_monthly_income * 0.50, 2),
        'wants_budget_30pct':  round(avg_monthly_income * 0.30, 2),
        'savings_target_20pct': round(avg_monthly_income * 0.20, 2),
        'actual_savings':       round(net_savings / num_months, 2),
        'savings_gap':          round((avg_monthly_income * 0.20) - (net_savings / num_months), 2),
    }

    return {
        'summary': {
            'total_income':          round(total_income, 2),
            'total_expenses':        round(total_expenses, 2),
            'net_savings':           round(net_savings, 2),
            'savings_rate_pct':      savings_rate,
            'num_months_of_data':    num_months,
            'avg_monthly_income':    avg_monthly_income,
            'avg_monthly_expenses':  avg_monthly_expenses,
        },
        'top_spending_categories':  top_categories,
        'expenses_by_category':     category_totals,
        'category_pct_of_spending': category_pct,
        'monthly_income':           monthly_income_series,
        'monthly_expenses':         monthly_expense_series,
        'mom_expense_change_pct':   mom_expense,
        'top_merchants':            top_merchants,
        'benchmark_50_30_20':       benchmark_50_30_20,
    }


def run_full_pipeline(csv_path: str, model_path: str) -> dict:
    """
    End-to-end: CSV → parse → classify → aggregate → financial profile JSON.
    """
    print(f"📂 Parsing: {csv_path}")
    df = parse_statement(csv_path)

    print(f"🤖 Loading classifier from: {model_path}")
    pipeline = joblib.load(model_path)

    print("🏷️  Classifying transactions...")
    df = classify_dataframe(df, pipeline)

    print("📊 Building financial profile...")
    profile = build_financial_profile(df)

    return profile, df


if __name__ == '__main__':
    BASE       = os.path.dirname(os.path.dirname(__file__))
    csv_path   = os.path.join(BASE, 'demo_data.csv')
    model_path = os.path.join(BASE, 'models', 'classifier.pkl')

    profile, classified_df = run_full_pipeline(csv_path, model_path)

    print("\n" + "═" * 60)
    print("💰  CENTSIBLE AI — Financial Profile")
    print("═" * 60)

    s = profile['summary']
    print(f"\n  Monthly Income (avg):    ${s['avg_monthly_income']:>12,.2f}")
    print(f"  Monthly Expenses (avg):  ${s['avg_monthly_expenses']:>12,.2f}")
    print(f"  Net Savings:             ${s['net_savings']:>12,.2f}")
    print(f"  Savings Rate:             {s['savings_rate_pct']:>11.1f}%")
    print(f"  Months of Data:          {s['num_months_of_data']:>12}")

    print("\n  📂 Spending by Category:")
    for cat, amt in profile['expenses_by_category'].items():
        pct = profile['category_pct_of_spending'].get(cat, 0)
        bar = '█' * int(pct / 3)
        print(f"    {cat:<20} ${amt:>10,.2f}  ({pct:>5.1f}%)  {bar}")

    print("\n  🏪 Top Merchants:")
    for i, (merchant, amt) in enumerate(profile['top_merchants'].items(), 1):
        print(f"    {i:>2}. {merchant:<35} ${amt:>8,.2f}")

    b = profile['benchmark_50_30_20']
    print("\n  📐 50/30/20 Benchmark (monthly):")
    print(f"    Needs  budget (50%): ${b['needs_budget_50pct']:>10,.2f}")
    print(f"    Wants  budget (30%): ${b['wants_budget_30pct']:>10,.2f}")
    print(f"    Savings target (20%):${b['savings_target_20pct']:>10,.2f}")
    print(f"    Actual savings/month:${b['actual_savings']:>10,.2f}")
    gap = b['savings_gap']
    flag = '🟢 Ahead' if gap <= 0 else f'🔴 Short by ${gap:,.2f}'
    print(f"    Status: {flag}")

    print("\n  📅 Month-over-Month Expense Change:")
    for month, pct in profile['mom_expense_change_pct'].items():
        arrow = '↑' if pct > 0 else ('↓' if pct < 0 else '→')
        print(f"    {month}: {arrow} {abs(pct):.1f}%")

    # Save profile JSON for Flask API to read
    out_path = os.path.join(BASE, 'data', 'financial_profile.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(profile, f, indent=2)
    print(f"\n💾 Profile saved → {out_path}")
    print("═" * 60)
