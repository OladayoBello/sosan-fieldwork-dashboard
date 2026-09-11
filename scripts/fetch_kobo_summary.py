#!/usr/bin/env python3
"""
Pulls submission data from a KoboToolbox project and writes out ONLY summary
counts (never individual answers) to data/summary.json for the dashboard.

Required environment variables:
  KOBO_API_TOKEN   - your KoboToolbox API token (Account Settings > Security)
  KOBO_ASSET_UID   - the project's asset UID (the code after "forms/" in the
                      project URL on kf.kobotoolbox.org)

Optional:
  KOBO_SERVER      - defaults to https://kf.kobotoolbox.org
"""

import os
import sys
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

import requests

SERVER = os.environ.get("KOBO_SERVER", "https://kf.kobotoolbox.org").rstrip("/")
TOKEN = os.environ.get("KOBO_API_TOKEN")
ASSET_UID = os.environ.get("KOBO_ASSET_UID")

# Field names in the SOSAN form used for aggregation.
ENUMERATOR_FIELD = "enumerator_name"   # now holds Enum-A .. Enum-Z codes
LGA_FIELD = "lga"
WARD_FIELD = "ward"
COMMUNITY_FIELD = "community"
DATE_FIELD = "date"
OUTCOME_FIELD = "interview_outcome"    # present in some deployed versions only
GPS_STATUS_FIELD = "gps_status"
GPS_REASON_FIELD = "gps_no_reason"
GPS_REASON_OTHER_FIELD = "gps_no_reason_other"

GPS_REASON_LABELS = {
    "no_signal": "No GPS signal at this location (dense cover/indoors)",
    "device_issue": "Device GPS not working",
    "other": "Other",
}


def fetch_all_submissions():
    if not TOKEN or not ASSET_UID:
        sys.exit("KOBO_API_TOKEN and KOBO_ASSET_UID must be set as environment variables.")

    headers = {"Authorization": f"Token {TOKEN}"}
    url = f"{SERVER}/api/v2/assets/{ASSET_UID}/data/?format=json&limit=1000"
    results = []

    while url:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        results.extend(payload.get("results", []))
        url = payload.get("next")

    return results


def clean_field(record, field):
    """Kobo prefixes field names with their group path, e.g. 'group_a1/date'.
    This finds a field by its bare name regardless of group nesting."""
    if field in record:
        return record[field]
    for key, value in record.items():
        if key == field or key.endswith("/" + field):
            return value
    return None


def build_summary(records):
    total = len(records)
    by_enumerator = Counter()
    by_lga = Counter()
    by_community = Counter()
    by_date = Counter()
    completed = 0

    gps_issues = []
    by_gps_reason = Counter()

    for r in records:
        enum_code = clean_field(r, ENUMERATOR_FIELD)
        lga = clean_field(r, LGA_FIELD)
        community = clean_field(r, COMMUNITY_FIELD)
        ward = clean_field(r, WARD_FIELD)
        date = clean_field(r, DATE_FIELD)
        outcome = clean_field(r, OUTCOME_FIELD)
        gps_status = clean_field(r, GPS_STATUS_FIELD)
        gps_reason = clean_field(r, GPS_REASON_FIELD)
        gps_reason_other = clean_field(r, GPS_REASON_OTHER_FIELD)

        if enum_code:
            by_enumerator[str(enum_code)] += 1
        if lga:
            by_lga[str(lga)] += 1
        if community:
            label = str(community)
            if ward:
                label = f"{community} ({ward})"
            by_community[label] += 1
        if date:
            by_date[str(date)[:10]] += 1

        # Count as "completed" if there's no outcome field (older versions),
        # or the outcome field explicitly says completed.
        if outcome is None or str(outcome).lower() == "completed":
            completed += 1

        if gps_status == "no":
            reason_label = GPS_REASON_LABELS.get(gps_reason, gps_reason or "Not specified")
            if gps_reason == "other" and gps_reason_other:
                reason_label = f"Other: {gps_reason_other}"
            by_gps_reason[reason_label] += 1
            gps_issues.append({
                "enumerator": str(enum_code) if enum_code else "Unknown",
                "date": str(date)[:10] if date else "Unknown",
                "lga": str(lga) if lga else "Unknown",
                "community": str(community) if community else "Unknown",
                "reason": reason_label,
            })

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_submissions": total,
        "completed_submissions": completed,
        "by_enumerator": dict(sorted(by_enumerator.items())),
        "by_lga": dict(sorted(by_lga.items(), key=lambda kv: -kv[1])),
        "by_community": dict(sorted(by_community.items(), key=lambda kv: -kv[1])),
        "by_date": dict(sorted(by_date.items())),
        "gps_issue_count": len(gps_issues),
        "by_gps_reason": dict(sorted(by_gps_reason.items(), key=lambda kv: -kv[1])),
        "gps_issues": sorted(gps_issues, key=lambda x: x["date"]),
    }
    return summary


def main():
    records = fetch_all_submissions()
    summary = build_summary(records)

    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "summary.json")
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote summary for {summary['total_submissions']} submissions to {out_path}")


if __name__ == "__main__":
    main()
