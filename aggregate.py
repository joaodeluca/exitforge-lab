"""Offline migration of one public Multi Source Aggregation workflow.

Source/attribution: provenance.json and THIRD_PARTY_NOTICE.md.
No HTTP client, dynamic code, credentials, platform runtime or dependencies.
Acquisition is intentionally replaced by caller-supplied response snapshots.
"""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys


class SnapshotError(ValueError):
    def __init__(self, source, code, unknown=False):
        self.source, self.code, self.unknown = source, code, unknown


def finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("non-string key")
            finite_json(item)
    elif isinstance(value, list):
        for item in value:
            finite_json(item)


def read_source(snapshots, name):
    if name not in snapshots:
        raise SnapshotError(name, "MISSING_SOURCE")
    response = snapshots[name]
    if type(response) is not dict:
        raise SnapshotError(name, "INVALID_RESPONSE")
    if response.get("error") == "timeout":
        raise SnapshotError(name, "TIMEOUT", unknown=True)
    if set(response) != {"status", "json"}:
        raise SnapshotError(name, "INVALID_RESPONSE")
    status = response["status"]
    if type(status) is not int or not 100 <= status <= 599:
        raise SnapshotError(name, "INVALID_STATUS")
    if not 200 <= status < 300:
        raise SnapshotError(name, "HTTP_" + str(status))
    if type(response["json"]) is not dict:
        raise SnapshotError(name, "EXPECTED_OBJECT")
    return deepcopy(response["json"])


def aggregate(snapshots):
    """Append traffic, revenue; overwrite report_type exactly as the Set node.

    Both sources must be successful JSON objects. No partial report on failure.
    Snapshot content is untrusted input, not fresh or authenticated provider data.
    """
    try:
        if type(snapshots) is not dict or set(snapshots) - {"traffic", "revenue"}:
            raise SnapshotError("input", "INVALID_INPUT")
        try:
            finite_json(snapshots)
        except ValueError:
            raise SnapshotError("input", "NON_FINITE_JSON") from None
        traffic = read_source(snapshots, "traffic")
        revenue = read_source(snapshots, "revenue")
        items = [{**item, "report_type": "daily-kpi"} for item in (traffic, revenue)]
        return {"status": "completed_offline", "items": items, "network_calls": 0}
    except SnapshotError as error:
        return {"status": "unknown" if error.unknown else "failed", "items": [], "error": {"source": error.source, "code": error.code}, "network_calls": 0}


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 aggregate.py snapshot.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(json.dumps({"status": "failed", "items": [], "error": {"source": "input", "code": "UNREADABLE_OR_INVALID_JSON"}, "network_calls": 0}))
        return 2
    result = aggregate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["status"] == "completed_offline" else 2


if __name__ == "__main__":
    raise SystemExit(main())
