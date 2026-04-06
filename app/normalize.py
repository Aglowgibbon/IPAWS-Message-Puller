from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _extract_event_codes(alert: Dict[str, Any]) -> List[str]:
    codes: List[str] = []

    for item in alert.get("eventCode", []) or []:
        if isinstance(item, dict):
            for _, value in item.items():
                if value:
                    codes.append(str(value))

    if codes:
        return sorted(set(codes))

    for info in alert.get("info", []) or []:
        for event_code in info.get("eventCode", []) or []:
            if isinstance(event_code, dict):
                for _, value in event_code.items():
                    if value:
                        codes.append(str(value))

    return sorted(set(codes))


def _extract_events(alert: Dict[str, Any]) -> List[str]:
    events = [
        str(info.get("event"))
        for info in (alert.get("info", []) or [])
        if info.get("event")
    ]
    return sorted(set(events))


def _extract_headlines(alert: Dict[str, Any]) -> List[str]:
    headlines = [
        str(info.get("headline"))
        for info in (alert.get("info", []) or [])
        if info.get("headline")
    ]
    return sorted(set(headlines))


def _extract_sender_names(alert: Dict[str, Any]) -> List[str]:
    names = [
        str(info.get("senderName"))
        for info in (alert.get("info", []) or [])
        if info.get("senderName")
    ]
    return sorted(set(names))


def _extract_area_desc(alert: Dict[str, Any]) -> List[str]:
    area_descs: List[str] = []
    for info in alert.get("info", []) or []:
        for area in info.get("area", []) or []:
            value = area.get("areaDesc")
            if value:
                area_descs.append(str(value))
    return sorted(set(area_descs))


def _extract_geocodes(alert: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    for info in alert.get("info", []) or []:
        for area in info.get("area", []) or []:
            for geocode in area.get("geocode", []) or []:
                if isinstance(geocode, dict):
                    for _, value in geocode.items():
                        if value:
                            values.append(str(value))
    return sorted(set(values))


def flatten_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": alert.get("id"),
        "identifier": alert.get("identifier"),
        "sent": alert.get("sent"),
        "status": alert.get("status"),
        "msgType": alert.get("msgType"),
        "scope": alert.get("scope"),
        "sender": alert.get("sender"),
        "cogId": alert.get("cogId"),
        "eventCodes": "|".join(_extract_event_codes(alert)),
        "events": "|".join(_extract_events(alert)),
        "headlines": "|".join(_extract_headlines(alert)),
        "senderNames": "|".join(_extract_sender_names(alert)),
        "areaDescs": "|".join(_extract_area_desc(alert)),
        "geocodes": "|".join(_extract_geocodes(alert)),
    }


def write_json(path: str | Path, alerts: List[Dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(alerts, indent=2), encoding="utf-8")


def write_csv(path: str | Path, alerts: Iterable[Dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [flatten_alert(alert) for alert in alerts]

    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
