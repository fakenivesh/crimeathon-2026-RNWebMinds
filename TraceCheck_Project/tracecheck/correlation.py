from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_correlations(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"api": [], "changes": []})
    for record in records:
        request_id = record.get("request_id")
        if not request_id:
            continue
        event_type = (record.get("event_type") or "").lower()
        if event_type in {"api_request", "api_call", "vendor_api_request"}:
            grouped[request_id]["api"].append(record)
        elif event_type in {"vendor_change", "vendor_edit", "vendor_update"}:
            grouped[request_id]["changes"].append(record)

    pairs: list[dict[str, Any]] = []
    unmatched_api: list[dict[str, Any]] = []
    unmatched_changes: list[dict[str, Any]] = []
    for request_id, sides in grouped.items():
        apis, changes = sides["api"], sides["changes"]
        if apis and changes:
            for api in apis:
                for change in changes:
                    pairs.append({"request_id": request_id, "api": api, "change": change})
        elif apis:
            unmatched_api.extend(apis)
        elif changes:
            unmatched_changes.extend(changes)

    pairs.sort(key=lambda item: item["request_id"])
    return {
        "pairs": pairs,
        "matched_request_count": len({pair["request_id"] for pair in pairs}),
        "unmatched_api": unmatched_api,
        "unmatched_changes": unmatched_changes,
        "unmatched_count": len(unmatched_api) + len(unmatched_changes),
    }
