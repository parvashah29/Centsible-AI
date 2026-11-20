"""
Data Ingestion — Bank CSV & PDF Parser
Supports: CSV (all major US/global bank formats) + PDF bank statements
Project: Centsible AI | Currency: USD
"""

import pandas as pd
import warnings
import re
import os

warnings.filterwarnings('ignore', category=UserWarning, module='pandas')


# ──────────────────────────────────────────────────────────────────────────────
# COLUMN DETECTION
# ──────────────────────────────────────────────────────────────────────────────

def detect_date_column(df: pd.DataFrame) -> str:
    candidates = ['date', 'trans date', 'value date', 'transaction date', 'txn date', 'posted date', 'post date']
    for col in df.columns:
        if any(c in col for c in candidates):
            return col
    raise ValueError("Could not detect a Date column. Rename it to 'Date'.")


def detect_description_column(df: pd.DataFrame) -> str:
    candidates = ['description', 'narration', 'particulars', 'details', 'memo', 'remarks', 'merchant']
    for col in df.columns:
        if any(c in col for c in candidates):
            return col
    raise ValueError("Could not detect a Description column. Rename it to 'Description'.")


def detect_amount_column(df: pd.DataFrame) -> str:
    candidates = ['amount', 'withdrawal', 'deposit', 'debit', 'credit']
    for col in df.columns:
        if any(c in col for c in candidates):
            return col
    raise ValueError("Could not detect an Amount column.")


# ──────────────────────────────────────────────────────────────────────────────
# AMOUNT CLEANING
# ──────────────────────────────────────────────────────────────────────────────

def clean_amount(val) -> float:
    if pd.isna(val) or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val)
    val_str = re.sub(r'[₹$£€,\s]', '', val_str)
    val_str = val_str.replace('(', '-').replace(')', '')   # (123.45) → -123.45
    try:
        return float(val_str)
    except ValueError:
        return 0.0


# ──────────────────────────────────────────────────────────────────────────────
# CSV PARSING
# ──────────────────────────────────────────────────────────────────────────────

def parse_bank_csv(filepath: str) -> pd.DataFrame:
    """
    Parses an unformatted bank CSV into a clean DataFrame.
    Schema: date (datetime), description (str), amount (float — positive=credit/income, negative=debit/expense)
    """
    encodings = ['utf-8', 'windows-1252', 'latin1']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(filepath, encoding=enc, on_bad_lines='skip')
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("Could not read the CSV file.")

    df.columns = [str(c).strip().lower() for c in df.columns]

    date_col = detect_date_column(df)
    desc_col = detect_description_column(df)

    # Split debit/credit columns (e.g., Chase, HDFC) OR single amount column
    debit_cols  = [c for c in df.columns if any(k in c for k in ['debit', 'withdrawal', '(dr)', 'dr)'])]
    credit_cols = [c for c in df.columns if any(k in c for k in ['credit', 'deposit',   '(cr)', 'cr)'])]

    if debit_cols and credit_cols:
        d_col, c_col = debit_cols[0], credit_cols[0]
        df['amount'] = df[c_col].apply(clean_amount) - df[d_col].apply(clean_amount)
    else:
        amount_col   = detect_amount_column(df)
        df['amount'] = df[amount_col].apply(clean_amount)

    df['date']        = pd.to_datetime(df[date_col], format='mixed', dayfirst=False, errors='coerce')
    df['description'] = df[desc_col].astype(str).str.strip()

    df = df.dropna(subset=['date'])
    summary_kw = ['opening balance', 'closing balance', 'statement summary', 'beginning balance']
    df = df[~df['description'].str.lower().apply(lambda x: any(kw in x for kw in summary_kw))]

    return df[['date', 'description', 'amount']].reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# PDF PARSING
# ──────────────────────────────────────────────────────────────────────────────

def parse_bank_pdf(filepath: str) -> pd.DataFrame:
    """
    Extracts transactions from a bank statement PDF using pdfplumber.
    Strategy:
      1. Try to extract tables from each page.
      2. If no tables found, fall back to line-by-line regex parsing.
    Schema: date (datetime), description (str), amount (float)
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing. Run: pip install pdfplumber")

    all_rows = []
    
    # Late imports for fallback logic
    import re
    from datetime import datetime

    with pdfplumber.open(filepath) as pdf:
        # First pass: try to extract tables
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                header = [str(h or '').strip().lower() for h in table[0]]
                if not any(c in h for c in ['date', 'amount', 'description'] for h in header):
                    continue
                for row in table[1:]:
                    if not row or all(not cell for cell in row):
                        continue
                    if len(row) == len(header):
                        record = dict(zip(header, [str(c or '').strip() for c in row]))
                        all_rows.append(record)

        # Second pass: if tables failed (common for Chase etc.), use text fallback
        if len(all_rows) < 3:
            all_rows = []
            for page in pdf.pages:
                text = page.extract_text() or ''
                
                # Attempt to extract year from document e.g. "August 26, 2025"
                years = re.findall(r'\b(202\d)\b', text)
                default_year = years[0] if years else str(datetime.now().year)

                # Matches: "09/02 Zelle Payment 338.00 784.92"
                # Group 1 = 09/02, Group 2 = Zelle Payment, Group 3 = 338.00 784.92
                pattern = re.compile(
                    r'^\s*(?:\d+:\s*)?(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)\s+(.+?)\s+((?:[\-\$]?[\d,]+\.\d{2}\s*)+)$',
                    re.MULTILINE
                )
                
                for m in pattern.finditer(text):
                    date_str = m.group(1).strip()
                    desc_str = m.group(2).strip()
                    # If multiple amounts (e.g., tx amount + running balance), take the first one
                    amt_str  = m.group(3).strip().split()[0]
                    
                    # Fix dates like "08/26" by appending the year "08/26/2025"
                    if date_str.count('/') == 1 and date_str.count('-') == 0:
                        date_str = f"{date_str}/{default_year}"
                    elif date_str.count('-') == 1 and date_str.count('/') == 0:
                        date_str = f"{date_str}-{default_year}"
                        
                    all_rows.append({
                        'date':        date_str,
                        'description': desc_str,
                        'amount':      amt_str,
                    })

    if not all_rows:
        raise ValueError("No transactions could be extracted from this PDF. Try exporting as CSV from your bank instead.")

    df = pd.DataFrame(all_rows)
    df.columns = [str(c).strip().lower() for c in df.columns]

    date_col = detect_date_column(df)
    desc_col = detect_description_column(df)

    debit_cols  = [c for c in df.columns if any(k in c for k in ['debit', 'withdrawal', 'dr)'])]
    credit_cols = [c for c in df.columns if any(k in c for k in ['credit', 'deposit',   'cr)'])]

    if debit_cols and credit_cols:
        df['amount'] = df[credit_cols[0]].apply(clean_amount) - df[debit_cols[0]].apply(clean_amount)
    elif 'amount' in df.columns:
        df['amount'] = df['amount'].apply(clean_amount)
    else:
        raise ValueError("Could not detect Amount columns in the PDF table.")

    df['date']        = pd.to_datetime(df[date_col], format='mixed', dayfirst=False, errors='coerce')
    df['description'] = df[desc_col].astype(str).str.strip()

    df = df.dropna(subset=['date'])
    df = df[df['amount'] != 0]

    return df[['date', 'description', 'amount']].reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# UNIFIED ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def parse_statement(filepath: str) -> pd.DataFrame:
    """Auto-detects CSV vs PDF and routes to the correct parser."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        return parse_bank_pdf(filepath)
    elif ext == '.csv':
        return parse_bank_csv(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Upload a .csv or .pdf bank statement.")


if __name__ == '__main__':
    print("Parser loaded. Supports CSV + PDF bank statements.")
