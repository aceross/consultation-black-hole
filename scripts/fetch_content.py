"""Fetch the GOV.UK content item for each consultation that closed on or after a cut-off date.

Usage: python3 -I scripts/fetch_content.py data/raw/consultations.json 2019-01-01 data/raw/content.jsonl [refresh_since]
Keeps only the fields needed: dates, change history, outcome attachments count and organisations.
Re-fetches missing/error links, document_type mismatches, and items with public_timestamp >= refresh_since
(default 2026-10-30), then rewrites the JSONL cleanly without duplicate slugs.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_REFRESH_SINCE = "2026-10-30"


def fetch_item(link):
    url = "https://www.gov.uk/api/content" + link
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                c = json.load(resp)
            det = c.get("details", {})
            return {
                "link": link,
                "document_type": c.get("document_type"),
                "first_public_at": det.get("first_public_at") or c.get("first_published_at"),
                "opening_date": det.get("opening_date"),
                "closing_date": det.get("closing_date"),
                "change_history": det.get("change_history", []),
                "n_final_outcome_attachments": len(det.get("final_outcome_attachments") or []),
                "has_final_outcome_detail": bool(det.get("final_outcome_detail")),
                "orgs": [o.get("title") for o in c.get("links", {}).get("organisations", [])],
            }
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            return {"link": link, "error": e.code}


def main(listing, cutoff, out, refresh_since=DEFAULT_REFRESH_SINCE):
    rows = json.load(open(listing))
    seen = set()
    todo = []
    for r in rows:
        if r["doc_type"] in ("closed_consultation", "consultation_outcome") and (r.get("end_date") or "") >= cutoff:
            if r["link"] not in seen:
                seen.add(r["link"])
                todo.append(r)

    outp = Path(out)
    by_link = {}
    if outp.exists():
        for line in outp.open():
            if line.strip():
                rec = json.loads(line)
                by_link[rec["link"]] = rec

    to_fetch = [
        r for r in todo
        if r["link"] not in by_link
        or "error" in by_link[r["link"]]
        or (r.get("public_timestamp") or "") >= refresh_since
        or by_link[r["link"]].get("document_type") != r["doc_type"]
    ]
    print(f"Total todo: {len(todo)}; cached kept: {len(todo) - len(to_fetch)}; fetching: {len(to_fetch)}", flush=True)

    for i, r in enumerate(to_fetch):
        by_link[r["link"]] = fetch_item(r["link"])
        if i % 50 == 0:
            print(i, len(to_fetch), flush=True)
        time.sleep(0.1)

    tmp = outp.with_suffix(".jsonl.tmp")
    with tmp.open("w") as f:
        for r in todo:
            f.write(json.dumps(by_link[r["link"]]) + "\n")
    tmp.replace(outp)


if __name__ == "__main__":
    main(*sys.argv[1:5])
