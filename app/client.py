from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

import requests

from .config import BASE_URL, DEFAULT_PAGE_SIZE, DEFAULT_TIMEOUT, MAX_PAGE_SIZE


class FEMAApiError(RuntimeError):
    """Raised when the FEMA endpoint returns an unexpected response."""


@dataclass
class QueryOptions:
    start: Optional[str] = None
    end: Optional[str] = None
    cog_ids: List[str] = field(default_factory=list)
    event_code: Optional[str] = None
    geocode: Optional[str] = None
    order_by: str = "sent desc"
    page_size: int = DEFAULT_PAGE_SIZE


def _escape_odata_string(value: str) -> str:
    return value.replace("'", "''")


def _format_odata_literal(value: str) -> str:
    stripped = value.strip()
    if stripped.isdigit():
        return stripped
    return f"'{_escape_odata_string(stripped)}'"


def build_filter(options: QueryOptions) -> str:
    """Build an OpenFEMA $filter string.

    Dates should be ISO-8601 strings such as:
    - 2026-03-01
    - 2026-03-01T00:00:00.000Z
    """
    parts: List[str] = []

    if options.start:
        parts.append(f"sent ge '{_escape_odata_string(options.start)}'")
    if options.end:
        parts.append(f"sent lt '{_escape_odata_string(options.end)}'")

    clean_cog_ids = [cog_id.strip() for cog_id in options.cog_ids if cog_id and cog_id.strip()]
    if clean_cog_ids:
        cog_filters = [f"cogId eq {_format_odata_literal(cog_id)}" for cog_id in clean_cog_ids]
        parts.append(f"({' or '.join(cog_filters)})")

    if options.event_code:
        parts.append(
            f"contains(infos/eventCode/value,'{_escape_odata_string(options.event_code)}')"
        )
    if options.geocode:
        parts.append(
            f"contains(infos/areas/geocode/value,'{_escape_odata_string(options.geocode)}')"
        )

    return " and ".join(parts)


class FEMAIpawsClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "fema-ipaws-client/1.0"})

    def fetch_page(self, options: QueryOptions, skip: int = 0) -> Dict[str, Any]:
        page_size = min(max(1, options.page_size), MAX_PAGE_SIZE)
        params: Dict[str, Any] = {
            "$format": "json",
            "$top": page_size,
            "$skip": skip,
            "$orderby": options.order_by,
            "$inlinecount": "allpages",
        }

        filter_expr = build_filter(options)
        if filter_expr:
            params["$filter"] = filter_expr

        response = self.session.get(BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        if "IpawsArchivedAlerts" not in payload:
            raise FEMAApiError("Unexpected response shape: missing 'IpawsArchivedAlerts'")

        return payload

    def iter_alerts(
        self, options: QueryOptions, max_pages: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        skip = 0
        page = 0
        page_size = min(max(1, options.page_size), MAX_PAGE_SIZE)

        while True:
            payload = self.fetch_page(options, skip=skip)
            alerts = payload.get("IpawsArchivedAlerts", [])
            if not alerts:
                break

            for alert in alerts:
                yield alert

            page += 1
            if max_pages is not None and page >= max_pages:
                break

            if len(alerts) < page_size:
                break

            skip += len(alerts)

    def fetch_all(self, options: QueryOptions, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        return list(self.iter_alerts(options, max_pages=max_pages))
