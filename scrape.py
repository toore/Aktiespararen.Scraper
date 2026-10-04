import argparse
import io
import sys

import pdfplumber
import pypdfium2 as pdfium
import requests

def fetch_holdings(source):
    if source.lower().startswith(("http://", "https://")):
        print("Downloading PDF...", file=sys.stderr)
        source = io.BytesIO(requests.get(source, timeout=120).content)
    else:
        with open(source, "rb") as f:
            source = io.BytesIO(f.read())
    table = None
    # pdfium is much faster than pdfplumber for locating the right page.
    doc = pdfium.PdfDocument(source)
    total = len(doc)
    candidates = []
    for i in range(total):
        print(f"\rScanning PDF: page {i + 1}/{total}", end="", file=sys.stderr, flush=True)
        text = doc[i].get_textpage().get_text_bounded()
        if "AKTIESPARARNA AKTIV" in text.upper():
            candidates.append(i)
    print(file=sys.stderr)
    doc.close()
    source.seek(0)
    with pdfplumber.open(source) as pdf:
        for i in candidates:
            print(f"Reading table on page {i + 1}...", file=sys.stderr)
            table = next(
                (t for t in pdf.pages[i].extract_tables() if any("Andel i fonden" in (c or "") for c in t[1])),
                None,
            )
            if table:
                break
    if not table:
        sys.exit("Could not find the Aktiespararna Aktiv table in the PDF.")
    holdings = {}
    for row in table[2:]:
        for name, share in ((row[0], row[1]), (row[2], row[3])):
            if name and share:
                holdings[name.strip()] = float(share.strip().rstrip("%").replace(",", "."))
    return holdings


def fmt(n):
    return f"{n:,.2f}"


def main():
    parser = argparse.ArgumentParser(description="Distribute an amount over the Aktiespararna Aktiv holdings.")
    parser.add_argument("pdf", help="PDF URL or local file path")
    parser.add_argument("--amount", help="total amount to distribute (prompted if omitted)")
    args = parser.parse_args()
    raw = args.amount or input("Total amount to distribute (SEK): ")
    total = float(raw.replace(" ", "").replace(",", "."))
    holdings = fetch_holdings(args.pdf)
    width = max(len(n) for n in holdings)
    print(f"\n{'Company'.ljust(width)}  {'Share':>7}  {'Amount (SEK)':>14}")
    for name in sorted(holdings, key=str.casefold):
        pct = holdings[name]
        print(f"{name.ljust(width)}  {pct:>6.2f}%  {fmt(total * pct / 100):>14}")
    s = sum(holdings.values())
    print(f"{'Total'.ljust(width)}  {s:>6.2f}%  {fmt(total * s / 100):>14}")


if __name__ == "__main__":
    main()

