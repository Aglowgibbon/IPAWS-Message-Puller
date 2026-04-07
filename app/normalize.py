from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple
from xml.etree import ElementTree


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


def _extract_info_values(alert: Dict[str, Any], field_name: str) -> List[str]:
    values: List[str] = []
    for info in (alert.get("info", []) or []):
        raw_value = info.get(field_name)
        if not raw_value:
            continue
        if isinstance(raw_value, list):
            for item in raw_value:
                if item:
                    values.append(str(item))
        else:
            values.append(str(raw_value))
    return sorted(set(values))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _extract_original_wea_messages(alert: Dict[str, Any]) -> Dict[str, str]:
    parsed = {
        "originalMessage90English": "",
        "originalMessage360English": "",
        "originalMessage90Spanish": "",
        "originalMessage360Spanish": "",
    }
    original_message = alert.get("originalMessage")
    if not original_message or not isinstance(original_message, str):
        return parsed

    try:
        root = ElementTree.fromstring(original_message)
    except ElementTree.ParseError:
        return parsed

    for info_node in root:
        if _local_name(info_node.tag) != "info":
            continue

        language = ""
        params: Dict[str, str] = {}

        for node in info_node:
            node_name = _local_name(node.tag)
            if node_name == "language":
                language = (node.text or "").strip().lower()
            elif node_name == "parameter":
                value_name = ""
                value = ""
                for param_node in node:
                    param_name = _local_name(param_node.tag)
                    if param_name == "valueName":
                        value_name = (param_node.text or "").strip()
                    elif param_name == "value":
                        value = (param_node.text or "").strip()
                if value_name and value:
                    params[value_name] = value

        if language.startswith("en"):
            cmam_text = params.get("CMAMtext", "")
            cmam_long_text = params.get("CMAMlongtext", "")
            if cmam_text:
                parsed["originalMessage90English"] = cmam_text
            if cmam_long_text:
                parsed["originalMessage360English"] = cmam_long_text
        elif language.startswith("es"):
            cmam_text = params.get("CMAMtext", "")
            cmam_long_text = params.get("CMAMlongtext", "")
            if cmam_text:
                parsed["originalMessage90Spanish"] = cmam_text
            if cmam_long_text:
                parsed["originalMessage360Spanish"] = cmam_long_text

    return parsed


def _extract_delivery_metadata(alert: Dict[str, Any]) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
    systems: Set[str] = set()
    eas_senders: Set[str] = set()
    wea_senders: Set[str] = set()
    nwem_senders: Set[str] = set()
    eas_org_codes: Set[str] = set()

    for info in alert.get("info", []) or []:
        parameters = info.get("parameter", []) or []
        has_eas = False
        has_wea = False
        has_nwem = False

        for parameter in parameters:
            if not isinstance(parameter, dict):
                continue

            name = str(parameter.get("name") or parameter.get("valueName") or "").strip()
            value = str(parameter.get("value") or "").strip()

            if name == "EAS-ORG":
                has_eas = True
                if value:
                    eas_org_codes.add(value)

            if name in {"WEAHandling", "CMAMtext", "CMAMlongtext"}:
                has_wea = True

            if name == "BLOCKCHANNEL":
                if value.upper() == "NWEM":
                    has_nwem = True
                if value.upper() == "CMAS":
                    has_wea = True

        resources = info.get("resource", []) or []
        for resource in resources:
            if not isinstance(resource, dict):
                continue
            resource_desc = str(resource.get("resourceDesc") or "")
            if "EAS Broadcast Content" in resource_desc:
                has_eas = True

        sender_label = str(info.get("senderName") or alert.get("sender") or "").strip()
        if has_eas:
            systems.add("EAS")
            if sender_label:
                eas_senders.add(sender_label)
        if has_wea:
            systems.add("WEA")
            if sender_label:
                wea_senders.add(sender_label)
        if has_nwem:
            systems.add("NWEM")
            if sender_label:
                nwem_senders.add(sender_label)

    return (
        sorted(systems),
        sorted(eas_senders),
        sorted(wea_senders),
        sorted(nwem_senders),
        sorted(eas_org_codes),
    )


def flatten_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    info_languages = _extract_info_values(alert, "language")
    info_categories = _extract_info_values(alert, "category")
    info_events = _extract_info_values(alert, "event")
    info_expires = _extract_info_values(alert, "expires")
    original_wea_messages = _extract_original_wea_messages(alert)
    delivery_systems, eas_senders, wea_senders, nwem_senders, eas_org_codes = _extract_delivery_metadata(alert)

    return {
        "id": alert.get("id"),
        "identifier": alert.get("identifier"),
        "sent": alert.get("sent"),
        "status": alert.get("status"),
        "msgType": alert.get("msgType"),
        "scope": alert.get("scope"),
        "sender": alert.get("sender"),
        "cogId": alert.get("cogId"),
        "source": alert.get("source"),
        "info.language": "|".join(info_languages),
        "info.category": "|".join(info_categories),
        "info.event": "|".join(info_events),
        "info.expires": "|".join(info_expires),
        "deliverySystems": "|".join(delivery_systems),
        "easOrgs": "|".join(eas_org_codes),
        "easSenders": "|".join(eas_senders),
        "weaSenders": "|".join(wea_senders),
        "nwemSenders": "|".join(nwem_senders),
        "eventCodes": "|".join(_extract_event_codes(alert)),
        "events": "|".join(_extract_events(alert)),
        "headlines": "|".join(_extract_headlines(alert)),
        "senderNames": "|".join(_extract_sender_names(alert)),
        "areaDescs": "|".join(_extract_area_desc(alert)),
        "geocodes": "|".join(_extract_geocodes(alert)),
        **original_wea_messages,
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
