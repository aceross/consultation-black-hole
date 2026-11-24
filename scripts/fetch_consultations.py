"""Download every GOV.UK consultation (open, closed, outcome) from the search API.

Usage: python3 -I scripts/fetch_consultations.py data/raw/consultations.json
"""
import json
import sys
import time
import urllib.request

API = "https://www.gov.uk/api/search.json"
TYPES = ["open_consultation", "closed_consultation", "consultation_outcome"]
FIELDS = ["title", "link", "public_timestamp", "start_date", "end_date", "organisations",
          "content_store_document_type", "first_published_at", "government_name", "is_historic"]


def fetch(doc_type):
    rows, start = [], 0
    while True:
        q = f"{API}?filter_content_store_document_type={doc_type}&count=1000&start={start}&order=-public_timestamp"
        q += "".join(f"&fields={f}" for f in FIELDS)
        with urllib.request.urlopen(q, timeout=120) as r:
            d = json.load(r)
        rows += d["results"]
        start += 1000
        if start >= d["total"]:
            return rows
        time.sleep(0.5)


def main(out):
    allrows = []
    for t in TYPES:
        rows = fetch(t)
        for r in rows:
            r["doc_type"] = t
        print(t, len(rows))
        allrows += rows
    with open(out, "w") as f:
        json.dump(allrows, f)


if __name__ == "__main__":
    main(sys.argv[1])
