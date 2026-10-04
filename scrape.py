import argparse
import io
import sys

import pdfplumber
import requests

def fetch_holdings(source):
    if source.lower().startswith(("http://", "https://")):
        source = io.BytesIO(requests.get(source, timeout=120).content)
    table = None
    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            if "AKTIESPARARNA AKTIV" not in (page.extract_text() or "").upper():
                continue
            table = next(
                (t for t in page.extract_tables() if any("Andel i fonden" in (c or "") for c in t[1])),
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
    return f"{n:,.2f}".replace(",", " ").replace(".", ",")


def main():
    parser = argparse.ArgumentParser(description="Distribute an amount over the Aktiespararna Aktiv holdings.")
    parser.add_argument("pdf", help="PDF URL or local file path")
    parser.add_argument("--amount", help="total amount to distribute (prompted if omitted)")
    args = parser.parse_args()
    raw = args.amount or input("Total summa att fördela (kr): ")
    total = float(raw.replace(" ", "").replace(",", "."))
    holdings = fetch_holdings(args.pdf)
    width = max(len(n) for n in holdings)
    print(f"\n{'Bolag'.ljust(width)}  {'Andel':>7}  {'Summa (kr)':>14}")
    for name in sorted(holdings, key=str.casefold):
        pct = holdings[name]
        print(f"{name.ljust(width)}  {pct:>6.2f}%  {fmt(total * pct / 100):>14}")
    s = sum(holdings.values())
    print(f"{'Totalt'.ljust(width)}  {s:>6.2f}%  {fmt(total * s / 100):>14}")


if __name__ == "__main__":
    main()

