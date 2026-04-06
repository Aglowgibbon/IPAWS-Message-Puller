from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

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



def main() -> None:
    args = parse_args()
    cog_ids = resolve_cog_ids(args)

    options = QueryOptions(
        start=args.start,
        end=args.end,
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
    print(f"Applied filter: {build_filter(options) or '[none]'}")
    print(f"Raw JSON: {args.json_output}")
    print(f"Flat CSV: {args.csv_output}")


if __name__ == "__main__":
    main()
