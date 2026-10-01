"""Explicit public GET inputs -> the unchanged object-to-daily-kpi transform."""
import argparse
import hashlib
import json
from pathlib import Path

from aggregate import aggregate
from http_adapter import get_json


def fetch_and_aggregate(first_url, second_url, *, timeout=10, allow_loopback=False):
    events = [get_json(url, timeout=timeout, allow_loopback=allow_loopback) for url in (first_url, second_url)]
    if all(event["status"] == "ok" for event in events):
        snapshots = {slot: {"status": event["http_status"], "json": event["json"]} for slot, event in zip(("traffic", "revenue"), events)}
        result = aggregate(snapshots)
        if result["status"] == "completed_offline":
            result["status"] = "completed_public_get"
        result["network_calls"] = sum(event["request_count"] for event in events)
    else:
        snapshots = None
        result = {"status": "unknown" if any(event["status"] == "unknown" for event in events) else "failed", "items": [], "network_calls": sum(event["request_count"] for event in events)}
    return {"evidence": "EXECUTED_HTTP_GET_NO_REMOTE_CODE_EXECUTION", "source_events": events, "snapshots": snapshots, "result": result, "adaptation": "Explicit URLs replace upstream example.com HTTP nodes. Repository metadata is not traffic/revenue; daily-kpi is only the preserved Set-node tag.", "external_writes": 0, "incremental_spend_brl": 0, "customer_or_sale_claimed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("first_url")
    parser.add_argument("second_url")
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--allow-loopback", action="store_true")
    args = parser.parse_args()
    report = fetch_and_aggregate(args.first_url, args.second_url, timeout=args.timeout, allow_loopback=args.allow_loopback)
    root = Path(__file__).resolve().parent
    report["source_sha256"] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("aggregate.py", "http_adapter.py", "live_demo.py")}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(0 if report["result"]["status"] == "completed_public_get" else 2)
