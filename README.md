# Aktiespararen Scraper

Scrapes the "Aktiespararna Aktiv" holdings table from the Aktiespararna PDF.
Asks for a total amount to distribute and prints every stock alphabetically with its percentage and amount.

## Setup (first time)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

The prompt shows `(.venv)` when it is active. On macOS/Linux use `source .venv/bin/activate`.
Leave the environment with `deactivate`.

## Run

```powershell
python scrape.py <pdf-url-or-path>                   # prompts for the total amount
python scrape.py <pdf-url-or-path> --amount 100000   # pass the amount as an argument
```

Without activating the environment: `.\.venv\Scripts\python scrape.py <pdf-url-or-path>`
