import argparse
import io
import sys

import pdfplumber
import pypdfium2 as pdfium
import requests


def _load_pdf(source):
    if source.lower().startswith(("http://", "https://")):
        print("Downloading PDF...", file=sys.stderr)
        response = requests.get(source, timeout=120)
        return io.BytesIO(response.content)

    with open(source, "rb") as pdf_file:
        return io.BytesIO(pdf_file.read())


def _find_candidate_pages(pdf_source):
    candidates = []
    document = pdfium.PdfDocument(pdf_source)
    try:
        total_pages = len(document)
        for page_number in range(total_pages):
            print(
                f"\rScanning PDF: page {page_number + 1}/{total_pages}",
                end="",
                file=sys.stderr,
                flush=True,
            )
            page_text = document[page_number].get_textpage().get_text_bounded()
            if "AKTIESPARARNA AKTIV" in page_text.upper():
                candidates.append(page_number)
    finally:
        document.close()

    print(file=sys.stderr)
    return candidates


def _is_holdings_table(table):
    return any("Andel i fonden" in (cell or "") for cell in table[1])


def _find_holdings_table(pdf_source, candidate_pages):
    with pdfplumber.open(pdf_source) as pdf:
        for page_number in candidate_pages:
            print(f"Reading table on page {page_number + 1}...", file=sys.stderr)
            for table in pdf.pages[page_number].extract_tables():
                if _is_holdings_table(table):
                    return table
    return None


def _parse_holdings(table):
    holdings = {}
    for row in table[2:]:
        for name, share in ((row[0], row[1]), (row[2], row[3])):
            if name and share:
                holdings[name.strip()] = float(share.strip().rstrip("%").replace(",", "."))
    return holdings


def fetch_holdings(source):
    pdf_source = _load_pdf(source)
    candidate_pages = _find_candidate_pages(pdf_source)
    pdf_source.seek(0)
    table = _find_holdings_table(pdf_source, candidate_pages)
    if not table:
        sys.exit("Could not find the Aktiespararna Aktiv table in the PDF.")
    return _parse_holdings(table)


def format_amount(n):
    return f"{n:,.2f}"


def _print_allocation(total, holdings):
    width = max(len(name) for name in holdings)
    print(f"\n{'Company'.ljust(width)}  {'Share':>7}  {'Amount (SEK)':>14}")
    for name in sorted(holdings, key=str.casefold):
        percentage = holdings[name]
        print(f"{name.ljust(width)}  {percentage:>6.2f}%  {format_amount(total * percentage / 100):>14}")

    total_percentage = sum(holdings.values())
    print(
        f"{'Total'.ljust(width)}  {total_percentage:>6.2f}%  "
        f"{format_amount(total * total_percentage / 100):>14}"
    )


def main():
    parser = argparse.ArgumentParser(description="Distribute an amount over the Aktiespararna Aktiv holdings.")
    parser.add_argument("pdf", help="PDF URL or local file path")
    parser.add_argument("--amount", help="total amount to distribute (prompted if omitted)")
    args = parser.parse_args()
    raw = args.amount or input("Total amount to distribute (SEK): ")
    total = float(raw.replace(" ", "").replace(",", "."))
    holdings = fetch_holdings(args.pdf)
    _print_allocation(total, holdings)


if __name__ == "__main__":
    main()
