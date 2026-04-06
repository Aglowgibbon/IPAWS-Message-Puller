from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .client import FEMAIpawsClient, QueryOptions, build_filter
from .normalize import write_csv, write_json


def _split_csv_values(values: Iterable[str]) -> List[str]:
    items: List[str] = []
    for value in values:
        for piece in value.split(","):
            cleaned = piece.strip()
            if cleaned:
                items.append(cleaned)
    return items


def _read_cog_ids_file(path: str) -> List[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return _split_csv_values(lines)


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _parse_mmddyyyy(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%m/%d/%Y")


def _to_utc_midnight_iso(value: datetime) -> str:
    return f"{value.strftime('%Y-%m-%d')}T00:00:00.000Z"


def _parse_date_range(start_text: str, end_text: str) -> Tuple[str, str, datetime, datetime]:
    start_dt = _parse_mmddyyyy(start_text)
    end_dt = _parse_mmddyyyy(end_text)

    if end_dt < start_dt:
        raise ValueError("End date must be the same day as or after the start date.")

    start_iso = _to_utc_midnight_iso(start_dt)
    # API filter uses `sent lt <end>` (exclusive), so add one day to include full end date.
    end_exclusive_iso = _to_utc_midnight_iso(end_dt + timedelta(days=1))
    return start_iso, end_exclusive_iso, start_dt, end_dt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and flatten FEMA IPAWS archived alerts."
    )
    parser.add_argument("--start", help="Inclusive start time, e.g. 2026-03-01T00:00:00.000Z")
    parser.add_argument("--end", help="Exclusive end time, e.g. 2026-03-02T00:00:00.000Z")
    parser.add_argument(
        "--cog-id",
        action="append",
        default=[],
        help="COG ID filter. Repeat the flag for multiple IDs.",
    )
    parser.add_argument(
        "--cog-ids",
        nargs="*",
        default=[],
        help="One or more COG IDs, comma-separated or space-separated.",
    )
    parser.add_argument(
        "--cog-ids-file",
        help="Optional text file containing COG IDs, one per line or comma-separated.",
    )
    parser.add_argument("--event-code", help="Optional event code filter, e.g. CEM, CAE, FLW")
    parser.add_argument("--geocode", help="Optional area geocode filter, e.g. 042081")
    parser.add_argument("--page-size", type=int, default=1000, help="Rows per page (max 10000)")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional stop after N pages")
    parser.add_argument(
        "--json-output",
        default="data/ipaws_alerts.json",
        help="Path for raw JSON output",
    )
    parser.add_argument(
        "--csv-output",
        default="data/ipaws_alerts.csv",
        help="Path for flattened CSV output",
    )
    return parser.parse_args()


def resolve_cog_ids(args: argparse.Namespace) -> List[str]:
    cog_ids: List[str] = []
    cog_ids.extend(_split_csv_values(args.cog_id))
    cog_ids.extend(_split_csv_values(args.cog_ids))

    if args.cog_ids_file:
        cog_ids.extend(_read_cog_ids_file(args.cog_ids_file))

    return _dedupe_preserve_order(cog_ids)


def _prompt_for_date(prompt_text: str) -> str:
    while True:
        user_value = input(prompt_text).strip()
        try:
            _parse_mmddyyyy(user_value)
            return user_value
        except ValueError:
            print("  Invalid date. Please use mm/dd/yyyy (example: 03/01/2026).")


def _prompt_for_cog_ids() -> List[str]:
    while True:
        raw = input("Enter COG IDs (comma-separated, e.g. 200032,200033): ").strip()
        cog_ids = _dedupe_preserve_order(_split_csv_values([raw]))
        if cog_ids:
            return cog_ids
        print("  Please enter at least one COG ID.")


def _collect_prompted_values() -> Tuple[str, str, List[str], datetime, datetime]:
    print("No command-line filters were provided. Let's set up your query.")
    print("Dates should use mm/dd/yyyy and run from midnight to midnight.")

    while True:
        start_raw = _prompt_for_date("Start date (mm/dd/yyyy): ")
        end_raw = _prompt_for_date("End date (mm/dd/yyyy): ")
        try:
            start_iso, end_iso, start_dt, end_dt = _parse_date_range(start_raw, end_raw)
            break
        except ValueError as exc:
            print(f"  {exc}")

    cog_ids = _prompt_for_cog_ids()
    return start_iso, end_iso, cog_ids, start_dt, end_dt


def _resolve_query_inputs(args: argparse.Namespace) -> Tuple[str, str, List[str], Optional[datetime], Optional[datetime]]:
    cli_cog_ids = resolve_cog_ids(args)

    has_cli_filters = bool(args.start or args.end or cli_cog_ids)
    if not has_cli_filters:
        return _collect_prompted_values()

    # CLI fallback for existing scripted usage.
    start = args.start
    end = args.end

    if not start or not end:
        raise ValueError("When using CLI arguments, both --start and --end are required.")

    return start, end, cli_cog_ids, None, None


def main() -> None:
    args = parse_args()
    start, end, cog_ids, start_dt, end_dt = _resolve_query_inputs(args)

    options = QueryOptions(
        start=start,
        end=end,
        cog_ids=cog_ids,
        event_code=args.event_code,
        geocode=args.geocode,
        page_size=args.page_size,
    )

    client = FEMAIpawsClient()
    alerts = client.fetch_all(options, max_pages=args.max_pages)

    write_json(Path(args.json_output), alerts)
    write_csv(Path(args.csv_output), alerts)

    print(f"Downloaded {len(alerts)} alerts")
    print(f"COG IDs: {', '.join(cog_ids) if cog_ids else 'none'}")
    if start_dt and end_dt:
        print(f"Date range: {start_dt.strftime('%m/%d/%Y')} through {end_dt.strftime('%m/%d/%Y')} (inclusive)")
    print(f"Applied filter: {build_filter(options) or '[none]'}")
    print(f"Raw JSON: {args.json_output}")
    print(f"Flat CSV: {args.csv_output}")


if __name__ == "__main__":
    main()
