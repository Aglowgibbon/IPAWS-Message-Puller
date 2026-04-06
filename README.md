# FEMA IPAWS Archived Alerts Starter Project

A small Python CLI project for pulling archived IPAWS alerts from the OpenFEMA endpoint:

`https://www.fema.gov/api/open/v1/IpawsArchivedAlerts`

## What this project does

- Pulls data from the FEMA IPAWS Archived Alerts endpoint
- Supports common filters:
  - sent date range
  - one or many COG IDs
  - optional event code
  - optional area geocode
- Paginates through the endpoint until all matching results are returned
- Saves:
  - raw JSON
  - flattened CSV for analysis

## Setup

> This project is **Python** (not Java).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Super simple step-by-step (first time users)

### Windows

1. Install Python 3.11+ from https://www.python.org/downloads/windows/
2. Open **Command Prompt**.
3. Go to the project folder:

```bat
cd C:\path\to\IPAWS-Message-Puller
```

4. Create and activate a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate
```

5. Install dependencies:

```bat
pip install -r requirements.txt
```

6. Run the app:

```bat
python -m app.main
```

7. When prompted:
   - Enter start date as `mm/dd/yyyy`
   - Enter end date as `mm/dd/yyyy`
   - Enter COG IDs as comma-separated values (example: `200032,200033`)

### macOS / Linux

1. Open Terminal.
2. Go to the project folder:

```bash
cd /path/to/IPAWS-Message-Puller
```

3. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the app:

```bash
python -m app.main
```

## Run (interactive, recommended)

Start the app and follow the prompts:

```bash
python -m app.main
```

The app will ask for:

- Start date in `mm/dd/yyyy`
- End date in `mm/dd/yyyy`
- A comma-separated list of COG IDs (for example `200032,200033,200034`)

Date behavior:

- Start date is interpreted at midnight (`00:00:00Z`) for that day.
- End date is inclusive through that full day (implemented as midnight of the next day in the API filter).

## Build a Windows `.exe` (optional)

Yes — you can package this app as a single executable using **PyInstaller**.

1. Activate your virtual environment.
2. Install PyInstaller:

```bash
pip install pyinstaller
```

3. Build the executable:

```bash
pyinstaller --onefile --name ipaws-puller -m app.main
```

4. Find the executable at:

```text
dist/ipaws-puller.exe
```

5. Run it from Command Prompt:

```bat
dist\ipaws-puller.exe
```

Notes:
- On first launch, antivirus/SmartScreen can sometimes warn on unsigned executables built locally.
- The `.exe` still needs internet access to query the FEMA API.

## Optional CLI mode (for scripts/automation)

You can still pass explicit CLI flags:

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-ids 200032 200033 200034
```

Additional optional flags:

- `--event-code CEM`
- `--geocode 042081`
- `--max-pages 2`
- `--page-size 1000`
- `--json-output data/ipaws_alerts.json`
- `--csv-output data/ipaws_alerts.csv`

## Output

- `data/ipaws_alerts.json` → raw payload records
- `data/ipaws_alerts.csv` → one row per alert, with nested fields compacted into pipe-delimited values

The CLI also prints the exact filter it applied so you can verify the query.

## Notes

- This endpoint is large, so narrow by date or COG whenever possible.
- The script pages until the endpoint returns a short page, which means all matching records have been retrieved.
- Some useful nested structures in the FEMA schema are `info`, `eventCode`, `searchGeometry`, and `originalMessage`.
- If you want to inspect the original CAP XML, use the `originalMessage` field from the raw JSON output.
