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

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

### Example: one COG ID for a date range

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-id 200032
```

### Example: multiple COG IDs for a date range

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-ids 200032 200033 200034
```

### Example: comma-separated COG IDs

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-ids 200032,200033,200034
```

### Example: COG IDs from a file

Create `cog_ids.txt` with either one per line:

```text
200032
200033
200034
```

or comma-separated values:

```text
200032,200033,200034
```

Then run:

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-ids-file cog_ids.txt
```

### Example: multiple COG IDs plus event code

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-08T00:00:00.000Z \
  --cog-ids 200032 200033 \
  --event-code CEM
```

### Example: only first two pages

```bash
python -m app.main \
  --start 2026-03-01T00:00:00.000Z \
  --end 2026-03-02T00:00:00.000Z \
  --cog-ids 200032 200033 \
  --max-pages 2 \
  --page-size 1000
```

## Output

- `data/ipaws_alerts.json` → raw payload records
- `data/ipaws_alerts.csv` → one row per alert, with nested fields compacted into pipe-delimited values

The CLI also prints the exact filter it applied so you can verify the query.

## Notes

- This endpoint is large, so narrow by date or COG whenever possible.
- The script pages until the endpoint returns a short page, which means all matching records have been retrieved.
- Some useful nested structures in the FEMA schema are `info`, `eventCode`, `searchGeometry`, and `originalMessage`.
- If you want to inspect the original CAP XML, use the `originalMessage` field from the raw JSON output.
