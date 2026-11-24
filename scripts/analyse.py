"""How long GOV.UK consultations take to get a published response, and how many never do.

Usage: python3 -I scripts/analyse.py data/raw/consultations.json data/raw/content.jsonl data
Writes data/consultations_since_2019.csv (one row per consultation closed since 1 Jan 2019).

The response date is the first change-history entry after the closing date whose note mentions a
response, outcome, feedback or summary (excluding pure delay/holding notices); failing that, the
first non-delay entry after closing on a page whose type is consultation_outcome.
Snapshot date is 24 November 2026.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

SNAPSHOT = pd.Timestamp("2026-11-24", tz="UTC")
RESPONSE_NOTE = re.compile(r"respon|outcome|feedback|summary|government reply|conclusion|decision", re.I)

# Holding / delay notices explain why a response is not yet published without publishing one.
DELAY_CUE = re.compile(
    r"delay(?:ed|ing)?\s+(?:the\s+)?(?:publication|summary|response|outcome)|"
    r"delay\s+to\s+(?:publishing|interim\s+response)|"
    r"(?:consultation\s+response|government\s+response|summary\s+of\s+responses)\s+(?:is|has been|are being)\s+delayed|"
    r"summary\s+of\s+responses(?:\s+and\s+(?:the\s+)?government\s+response)?\s+have\s+been\s+delayed|"
    r"holding note|still analys|currently analys|are analysing|we['’]re still analys|"
    r"when we have analysed|further analysis.*will provide further updates|"
    r"evaluating the feedback.*will provide|"
    r"expect to (?:will )?publish|will publish (?:a |the )?(?:summary|government|consultation|full|single)?\s*(?:response|outcome)|"
    r"(?:summary of responses|government response|consultation response|outcome)\s+will be (?:published|added)|"
    r"postponed the publication|added response summary to say expected|"
    r"opening paragraph added highlighting that a response will be published|"
    r"clarifying that the consultation outcome will be added|"
    r"page updated to provide details on when|updated with information on when|"
    r"added (?:a )?note (?:on|to|about) (?:the )?(?:how many|number of|explain|set out|indicate)|"
    r"added an update about the number of responses|update with number of responses|"
    r"added the number of responses received|"
    r"received (?:a large number of |[\d,]+ )?responses.*?(?:analysing|delay|will publish|expect to|in due course|later|20\d\d|portal)|"
    r"published (?:a )?summary of the total number of responses|"
    r"updated to reflect that we expect to publish|"
    r"responses to this consultation are being considered.*will be published",
    re.I,
)
EXACT_HOLDING = {
    "added detail of feedback received.",
    "added details of feedback received.",
    "information has been added about the consultation response.",
    "we've added details on the number of responses received and the next steps that are planned.",
}
ACTUAL_PUBLISH = re.compile(
    r"(?:^|[.;]\s*)(?:added|published|we(?:'ve| have) (?:added|published))\s+(?:the\s+)?(?:initial\s+|early\s+partial\s+|partial\s+)?"
    r"(?:government|consultation)\s+response\b|"
    r"(?:government|consultation)\s+response\s+(?:to\s+the\s+consultation\s+element\s+)?(?:has\s+been\s+)?(?:published|added)\b|"
    r"final\s+outcome\s+of\s+the\s+consultation|"
    r"summary\s+(?:of|or)\s+responses\s+and\s+(?:the\s+)?government\s+response\s+(?:including\s+new\s+policy\s+)?(?:added|published)\b",
    re.I,
)


def is_delay_note(note: str) -> bool:
    """Return True if a change-history note is a holding/delay notice rather than a response."""
    if not note:
        return False
    nl = " ".join(note.strip().lower().split())
    if nl in EXACT_HOLDING:
        return True
    return bool(DELAY_CUE.search(note) and not ACTUAL_PUBLISH.search(note))


def parse_opening_date(c: dict) -> pd.Timestamp:
    """Parse opening_date, falling back to first_public_at when missing or pre-1990 typo."""
    raw = c.get("opening_date")
    if not raw or raw[:4] < "1990":
        raw = c.get("first_public_at")
    return pd.to_datetime(raw, utc=True, errors="coerce")


def main(listing_json, content_jsonl, outdir):
    listing = {r["link"]: r for r in json.load(open(listing_json))}
    rows = []
    for line in open(content_jsonl):
        c = json.loads(line)
        if "error" in c:
            continue
        lst = listing[c["link"]]
        close = pd.to_datetime(c.get("closing_date") or lst.get("end_date"), utc=True, errors="coerce")
        hist = sorted(c.get("change_history") or [], key=lambda h: h["public_timestamp"])
        after = [h for h in hist if pd.Timestamp(h["public_timestamp"]) > close]
        delay_notes = [h for h in after if is_delay_note(h.get("note", ""))]
        non_delay_after = [h for h in after if not is_delay_note(h.get("note", ""))]
        flagged = [h for h in non_delay_after if RESPONSE_NOTE.search(h.get("note", ""))]
        is_outcome = c["document_type"] == "consultation_outcome"
        resp = None
        if flagged:
            resp = pd.Timestamp(flagged[0]["public_timestamp"])
        elif is_outcome and non_delay_after:
            resp = pd.Timestamp(non_delay_after[0]["public_timestamp"])
        orgs = lst.get("organisations") or []
        lead = (orgs[0].get("acronym") or orgs[0].get("title")) if orgs else ""
        rows.append({
            "link": c["link"],
            "title": lst.get("title"),
            "lead_org": lead,
            "doc_type": c["document_type"],
            "opened": parse_opening_date(c),
            "closed": close,
            "response_date": resp,
            "response_from_note": bool(flagged),
            "closed_page_mentions_response": (not is_outcome) and bool(flagged),
            "has_delay_note": bool(delay_notes),
            "delay_note_date": pd.Timestamp(delay_notes[0]["public_timestamp"]) if delay_notes else pd.NaT,
            "government": lst.get("government_name"),
        })
    d = pd.DataFrame(rows)
    d = d[d["closed"].notna() & (d["closed"] < SNAPSHOT)].copy()
    d["days_to_response"] = (d["response_date"] - d["closed"]).dt.days
    d["weeks_since_close"] = (SNAPSHOT - d["closed"]).dt.days / 7
    d["responded"] = d["response_date"].notna()
    d["within_12w"] = d["days_to_response"] <= 84
    d["overdue"] = ~d["responded"] & (d["weeks_since_close"] > 12)
    d["cohort"] = pd.cut(
        d["closed"],
        pd.to_datetime(["2019-01-01", "2022-01-01", "2024-07-05", "2025-07-05", "2026-11-24"], utc=True),
        labels=["2019-21", "2022 to election", "first year after election", "since July 2025"],
        right=False,
    )
    d.to_csv(Path(outdir) / "consultations_since_2019.csv", index=False)

    print("Consultations closed 1 Jan 2019 to 23 Nov 2026:", len(d))
    print(d["doc_type"].value_counts().to_string())
    print("Outcome pages with no datable response:", (d["doc_type"].eq("consultation_outcome") & ~d["responded"]).sum())
    print("Closed (no-outcome) pages whose history mentions a response after closing:", d["closed_page_mentions_response"].sum())
    print(d.loc[d["closed_page_mentions_response"], ["title", "lead_org", "closed"]].head(15).to_string())
    print("Pages with a post-closing holding/delay note:", int(d["has_delay_note"].sum()))
    print("  by doc_type:", d.loc[d["has_delay_note"], "doc_type"].value_counts().to_dict())
    print("  of which still unanswered:", int((d["has_delay_note"] & ~d["responded"]).sum()))

    def summary(g):
        eligible = g[g["weeks_since_close"] > 12]
        return pd.Series({
            "closed": len(g),
            "closed_12w_ago": len(eligible),
            "response_within_12w": int(eligible["within_12w"].sum()),
            "pct_within_12w": round(100 * eligible["within_12w"].mean(), 0) if len(eligible) else None,
            "no_response_yet": int(eligible["overdue"].sum()),
            "pct_no_response": round(100 * eligible["overdue"].mean(), 0) if len(eligible) else None,
            "median_days_if_responded": g.loc[g["responded"], "days_to_response"].median(),
        })

    print("\n== by closing cohort")
    print(d.groupby("cohort", observed=True).apply(summary, include_groups=False).to_string())

    since = d[d["closed"] >= pd.Timestamp("2024-07-05", tz="UTC")]
    print("\n== closed since 5 July 2024, by lead organisation (10+ consultations)")
    t = since.groupby("lead_org").apply(summary, include_groups=False)
    print(t[t["closed"] >= 10].sort_values("pct_within_12w").to_string())
    print("\nAll since election:", summary(since).to_dict())

    print("\n== oldest unanswered since the election")
    print(since[since["overdue"]].sort_values("closed")[["title", "lead_org", "closed"]].head(12).to_string())

    print("\n== longest-outstanding overall (closed since 2019)")
    print(d[d["overdue"]].sort_values("closed")[["title", "lead_org", "closed"]].head(8).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:4])
