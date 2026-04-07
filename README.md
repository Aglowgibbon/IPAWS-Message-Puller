# FEMA IPAWS Archived Alerts Puller

A Python CLI for pulling archived IPAWS alerts from:

`https://www.fema.gov/api/open/v1/IpawsArchivedAlerts`

## What this project does

- Pulls alerts from the FEMA IPAWS Archived Alerts endpoint.
- Supports filters for:
  - sent date range
  - one, many, or all COG IDs (wildcard `*` / `--all-cogs`)
  - optional event code
  - optional area geocode
- Paginates until all matching results are returned.
- Saves:
  - raw JSON
  - flattened CSV for analysis

## Setup

### Windows (Command Prompt)

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

### macOS / Linux (bash/zsh)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```


## Run

```bash
python -m app.main
```

Prompt input:

- Start date in `mm/dd/yyyy`
- End date in `mm/dd/yyyy`
- COG IDs as comma-separated values, or `*` for all COG IDs

## CLI mode (scripts/automation)

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --all-cogs
```

Examples:

```bash
# specific COG IDs
python -m app.main --start 2026-04-02T00:00:00.000Z --end 2026-04-03T00:00:00.000Z --cog-ids 200032 200033

# wildcard COG IDs (all)
python -m app.main --start 2026-04-02T00:00:00.000Z --end 2026-04-03T00:00:00.000Z --cog-id '*'
```

## Delivery-system sender fields in CSV

To help identify which organizations transmitted by channel, flattened CSV includes:

- `deliverySystems` (EAS / WEA / NWEM detected from CAP parameters)
- `easOrgs` (`EAS-ORG` CAP value)
- `easSenders` (senderName/sender for EAS messages)
- `weaSenders` (senderName/sender for WEA messages)
- `nwemSenders` (senderName/sender for NWEM messages)

## Build a standalone Windows `.exe`

From Command Prompt:

```bat
.venv\Scripts\activate
py -m pip install pyinstaller
py -m PyInstaller --onefile --name ipaws-puller ipaws_puller.py
```

Output executable:

```text
dist\ipaws-puller.exe
```

You can deploy and run `ipaws-puller.exe` directly (no manual `python -m ...` command needed on the target machine).

## Output

- `data/ipaws_alerts.json` → raw payload records
- `data/ipaws_alerts.csv` → one row per alert, with nested fields compacted into pipe-delimited values
