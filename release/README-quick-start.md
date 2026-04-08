# IPAWS Message Puller Quick Start (Windows)

1. Run `ipaws-puller.exe`.
2. Enter the start date (`mm/dd/yyyy`).
3. Enter the end date (`mm/dd/yyyy`).
4. Enter one or more COG IDs (comma-separated), or `*` for all COG IDs.
5. After completion, look in the `data` folder for:
   - `ipaws_alerts.json`
   - `ipaws_alerts.csv`

The app requires outbound HTTPS access to `www.fema.gov`.
