"""
Phase 2 — Transaction Classifier
Trains a TF-IDF + LogisticRegression pipeline to classify bank transactions.
Target: Overall accuracy > 85%, per-class F1 > 0.80.
Project: Centsible AI
"""

import os
import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import re

# US Merchant-specific hard overrides (checked BEFORE the ML model)
MERCHANT_OVERRIDES = {
    # Dining
    'doordash': 'Dining', 'uber eats': 'Dining', 'grubhub': 'Dining',
    'starbucks': 'Dining', 'mcdonalds': 'Dining', 'chipotle': 'Dining',
    'chick-fil-a': 'Dining', 'subway': 'Dining', 'panera': 'Dining',
    'dominos': 'Dining', 'pizza hut': 'Dining', 'taco bell': 'Dining',
    # Entertainment
    'netflix': 'Entertainment', 'spotify': 'Entertainment',
    'hulu': 'Entertainment', 'disney plus': 'Entertainment',
    'amazon prime': 'Entertainment', 'hbo max': 'Entertainment',
    'apple tv': 'Entertainment', 'youtube premium': 'Entertainment',
    'amc theatre': 'Entertainment', 'regal cinema': 'Entertainment',
    # Transport
    'uber': 'Transport', 'lyft': 'Transport', 'shell': 'Transport',
    'bp gas': 'Transport', 'chevron': 'Transport', 'ezpass': 'Transport',
    'southwest': 'Transport', 'delta': 'Transport', 'united air': 'Transport',
    # Groceries
    'whole foods': 'Groceries', 'trader joe': 'Groceries', 'kroger': 'Groceries',
    'safeway': 'Groceries', 'publix': 'Groceries', 'costco': 'Groceries',
    'aldi': 'Groceries', 'walmart grocery': 'Groceries', 'wegmans': 'Groceries',
    # Shopping
    'amazon': 'Shopping', 'target': 'Shopping', 'best buy': 'Shopping',
    'walmart': 'Shopping', 'nordstrom': 'Shopping', 'apple store': 'Shopping',
    'wayfair': 'Shopping', 'ikea': 'Shopping',
    # Healthcare
    'cvs': 'Healthcare', 'walgreens': 'Healthcare', 'rite aid': 'Healthcare',
    'quest diagnostic': 'Healthcare', 'labcorp': 'Healthcare',
    # Income
    'payroll': 'Income', 'salary': 'Income', 'direct deposit': 'Income',
    'freelance': 'Income', 'bonus': 'Income',
    # Transfers
    'zelle': 'Transfers', 'venmo': 'Transfers', 'paypal': 'Transfers',
    'cashapp': 'Transfers', 'wire transfer': 'Transfers',
}

LOW_CONFIDENCE_THRESHOLD = 0.60


def clean_text(text: str) -> str:
    """Normalise a transaction description for the classifier."""
    text = text.lower()
    # Remove common bank prefixes
    text = re.sub(r'^(upi/|pos/|neft/|ach/|chq/|atm/|imp/)', '', text)
    # Strip transaction codes (alphanumeric noise at the end)
    text = re.sub(r'[a-z]{2}\d{4,}', '', text)
    text = re.sub(r'\d+', '', text)       # Remove digits
    text = re.sub(r'[^a-z\s]', ' ', text) # Keep only letters and spaces
    return text.strip()


def apply_merchant_override(description: str):
    """Returns a category override if the merchant is in the hard-coded dict."""
    desc_lower = description.lower()
    for keyword, category in MERCHANT_OVERRIDES.items():
        if keyword in desc_lower:
            return category
    return None


def train_classifier(training_csv: str, model_output_path: str):
    """
    Loads training data, trains a TF-IDF + LogisticRegression pipeline,
    evaluates it, and saves the model with joblib.
    """
    print("📂 Loading training data...")
    df = pd.read_csv(training_csv)
    df['clean_desc'] = df['description'].apply(clean_text)

    X = df['clean_desc']
    y = df['category']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"   Train size: {len(X_train)} | Test size: {len(X_test)}")

    # Build pipeline: TF-IDF (unigrams + bigrams) → LogisticRegression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=8000, sublinear_tf=True)),
        ('clf',   LogisticRegression(C=1.0, max_iter=1000, solver='lbfgs'))
    ])

    print("🏋️  Training classifier...")
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n📊 Overall Accuracy: {acc * 100:.2f}%")
    print("\n📋 Per-Class Report:")
    print(classification_report(y_test, y_pred))

    if acc < 0.85:
        print("⚠️  WARNING: Accuracy is below 85% target. Consider adding more training data.")
    else:
        print("✅ Accuracy target met (>85%)!")

    # Check low-confidence rate
    probs = pipeline.predict_proba(X_test)
    max_probs = probs.max(axis=1)
    low_conf_rate = (max_probs < LOW_CONFIDENCE_THRESHOLD).mean()
    print(f"\n🔍 Low-confidence rate (<{LOW_CONFIDENCE_THRESHOLD}): {low_conf_rate * 100:.1f}%")

    # Save model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(pipeline, model_output_path)
    print(f"\n💾 Model saved → {model_output_path}")
    return pipeline


def predict_category(description: str, pipeline) -> dict:
    """
    Predicts the category for a single transaction description.
    Returns: { category: str, confidence: float, source: 'override' | 'model' }
    """
    # 1. Try hard override first
    override = apply_merchant_override(description)
    if override:
        return {'category': override, 'confidence': 1.0, 'source': 'override'}

    # 2. Use ML model
    clean = clean_text(description)
    proba = pipeline.predict_proba([clean])[0]
    max_prob = proba.max()
    predicted_class = pipeline.classes_[proba.argmax()]

    if max_prob < LOW_CONFIDENCE_THRESHOLD:
        return {'category': 'Uncategorised', 'confidence': max_prob, 'source': 'model_low_conf'}

    return {'category': predicted_class, 'confidence': round(max_prob, 3), 'source': 'model'}


if __name__ == '__main__':
    BASE = os.path.dirname(os.path.dirname(__file__))
    training_csv  = os.path.join(BASE, 'data', 'training_data.csv')
    model_out     = os.path.join(BASE, 'models', 'classifier.pkl')

    pipeline = train_classifier(training_csv, model_out)

    # Quick sanity check on US real-world descriptions
    test_cases = [
        'DoorDash Order DX5523',
        'DEBIT Payroll Direct Deposit',
        'POS Whole Foods MKT AB1234',
        'Netflix Monthly Subscription NX2233',
        'PURCHASE Uber Trip AB5512',
        'CVS Pharmacy PQ8821',
        'Zelle Payment to Friend ZZ9999',
        'DEBIT Apartment Rent JUNE',
        'Best Buy Electronics BB4421',
    ]

    print("\n🧪 Prediction Sanity Check:")
    print("-" * 60)
    for desc in test_cases:
        result = predict_category(desc, pipeline)
        src = result['source']
        icon = '🎯' if src == 'override' else ('✅' if result['category'] != 'Uncategorised' else '❓')
        print(f"{icon}  '{desc}'\n     → {result['category']} ({result['confidence']*100:.0f}%) [{src}]")
