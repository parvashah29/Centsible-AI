"""
Debug script — shows exactly what pdfplumber extracts from your bank PDF.
Run: python src/debug_pdf.py /path/to/your/statement.pdf
"""

import sys
import pdfplumber

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("Usage: python src/debug_pdf.py /path/to/statement.pdf")
    sys.exit(1)

print(f"\n{'='*70}")
print(f"PDF DEBUG: {path}")
print(f"{'='*70}")

with pdfplumber.open(path) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")

    for i, page in enumerate(pdf.pages[:4]):   # first 4 pages only
        print(f"\n{'─'*60}")
        print(f"PAGE {i+1}")
        print(f"{'─'*60}")

        # Raw text
        text = page.extract_text() or ''
        print("\n[RAW TEXT — first 80 lines]\n")
        for j, line in enumerate(text.split('\n')[:80]):
            print(f"  {j+1:>3}: {line}")

        # Tables
        tables = page.extract_tables()
        print(f"\n[TABLES FOUND: {len(tables)}]\n")
        for t_i, table in enumerate(tables):
            print(f"  Table {t_i+1} ({len(table)} rows):")
            for row in table[:8]:
                print(f"    {row}")
            if len(table) > 8:
                print(f"    ... ({len(table) - 8} more rows)")
