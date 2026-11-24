"""Department-level tables and Kaplan-Meier response curves for the consultations draft.

Usage: python3 -I scripts/departments.py data/consultations_since_2019.csv data
Writes data/km_curves.csv, data/km_summary_3cohorts.csv and data/departments_since_election.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SNAPSHOT = pd.Timestamp("2026-11-24", tz="UTC")
ELECTION = pd.Timestamp("2024-07-05", tz="UTC")
# Ministerial departments under their current and predecessor names, plus HMRC.
# GOV.UK reassigned DBT's post-election Make Work Pay and trade consultations to BIST after July 2026.
DEPARTMENTS = {
    "Defra": "Defra", "DfT": "DfT", "HMRC": "HMRC", "DESNZ": "DESNZ/BEIS", "BEIS": "DESNZ/BEIS", "DfE": "DfE",
    "HMT": "HM Treasury", "DHSC": "DHSC", "Home Office": "Home Office", "MHCLG": "MHCLG", "DLUHC": "MHCLG",
    "Ministry of Housing, Communities & Local Government (2018 to 2021)": "MHCLG", "MOJ": "MoJ", "DWP": "DWP",
    "BIST": "BIST/DBT", "DBT": "BIST/DBT", "DIT": "BIST/DBT",
    "DCMS": "DCMS", "Department for Culture, Media and Sport": "DCMS",
    "Department for Digital, Culture, Media & Sport (2017 to 2023)": "DCMS", "MOD": "MoD", "DSIT": "DSIT",
    "Cabinet Office": "Cabinet Office", "NIO": "NIO", "FCDO": "FCDO", "AGO": "AGO", "UKEF": "UKEF",
}
COHORTS = [
    ("2019-01-01", "2022-01-01", "Closed 2019 to 2021"),
    ("2022-01-01", "2024-07-05", "Closed 2022 to July 2024 election"),
    ("2024-07-05", "2025-07-05", "Closed in the year after the election"),
    ("2025-07-05", "2026-11-24", "Closed since July 2025"),
]
COHORTS_3 = [
    ("2019-01-01", "2022-01-01", "Closed 2019 to 2021"),
    ("2022-01-01", "2024-07-05", "Closed 2022 to July 2024 election"),
    ("2024-07-05", "2026-11-24", "Since the July 2024 election"),
]


def km_cumulative(days, event, grid):
    """Kaplan-Meier estimate of the share with a published response by each day in grid."""
    order = np.argsort(days)
    days, event = np.asarray(days)[order], np.asarray(event)[order]
    surv, out, i, n = 1.0, [], 0, len(days)
    at_risk = n
    for t in grid:
        while i < n and days[i] <= t:
            same = days == days[i]
            d_events = int((same & event).sum())
            d_total = int(same.sum())
            if at_risk > 0:
                surv *= 1 - d_events / at_risk
            at_risk -= d_total
            i += d_total
        out.append(1 - surv if t <= days.max() else np.nan)
    return np.array(out)


def main(src, outdir):
    d = pd.read_csv(src, parse_dates=["closed", "response_date", "opened"])
    d = d[d["doc_type"] != "redirect"].copy()
    d["dept"] = d["lead_org"].map(DEPARTMENTS)
    dep = d[d["dept"].notna()].copy()
    elapsed = (SNAPSHOT - dep["closed"]).dt.days
    dep["t"] = np.where(dep["responded"], dep["days_to_response"].clip(lower=0), elapsed)
    dep["event"] = dep["responded"]
    print("Department consultations closed since 2019:", len(dep))

    grid = np.arange(0, 731)
    curves = []
    for start, end, label in COHORTS:
        g = dep[(dep["closed"] >= pd.Timestamp(start, tz="UTC")) & (dep["closed"] < pd.Timestamp(end, tz="UTC"))]
        cum = km_cumulative(g["t"].values, g["event"].values, grid)
        curves.append(pd.DataFrame({"cohort": label, "day": grid, "share_responded": cum, "n": len(g)}))
        at = {w: round(100 * cum[w * 7], 0) if w * 7 < len(cum) and not np.isnan(cum[w * 7]) else None for w in (12, 26, 52, 104)}
        print(f"{label}: n={len(g)}; responded by 12w {at[12]}%, 26w {at[26]}%, 52w {at[52]}%, 104w {at[104]}%")
    pd.concat(curves).to_csv(Path(outdir) / "km_curves.csv", index=False)

    print("\n== 3-cohort KM summary (matching Figure 1 and prose table)")
    summary_3 = []
    for start, end, label in COHORTS_3:
        g = dep[(dep["closed"] >= pd.Timestamp(start, tz="UTC")) & (dep["closed"] < pd.Timestamp(end, tz="UTC"))]
        cum = km_cumulative(g["t"].values, g["event"].values, grid)
        at = {w: round(100 * cum[w * 7], 0) if w * 7 < len(cum) and not np.isnan(cum[w * 7]) else None for w in (12, 26, 52, 104)}
        n_risk_104w = int((g["t"] >= 728).sum())
        summary_3.append({
            "cohort": label,
            "n": len(g),
            "n_at_risk_104w": n_risk_104w,
            "pct_12w": at[12],
            "pct_26w": at[26],
            "pct_52w": at[52],
            "pct_104w": at[104],
            "share_12w": round(float(cum[12 * 7]), 4) if not np.isnan(cum[12 * 7]) else None,
            "share_26w": round(float(cum[26 * 7]), 4) if not np.isnan(cum[26 * 7]) else None,
            "share_52w": round(float(cum[52 * 7]), 4) if not np.isnan(cum[52 * 7]) else None,
            "share_104w": round(float(cum[104 * 7]), 4) if not np.isnan(cum[104 * 7]) else None,
        })
        print(f"{label}: n={len(g)} (at risk 104w={n_risk_104w}); 12w {at[12]}% ({100*cum[84]:.1f}%), "
              f"26w {at[26]}% ({100*cum[182]:.1f}%), 52w {at[52]}% ({100*cum[364]:.1f}%), 104w {at[104]}% ({100*cum[728]:.1f}%)")
    pd.DataFrame(summary_3).to_csv(Path(outdir) / "km_summary_3cohorts.csv", index=False)

    since = dep[dep["closed"] >= ELECTION]
    elig = since[(SNAPSHOT - since["closed"]).dt.days > 84]
    print(f"\nDepartments, closed since election and more than 12 weeks ago: {len(elig)}; "
          f"response within 12 weeks: {elig['within_12w'].sum()} ({100 * elig['within_12w'].mean():.0f}%); "
          f"no response yet: {elig['overdue'].sum()} ({100 * elig['overdue'].mean():.0f}%)")
    pre = elig[elig["opened"] < ELECTION]
    print(f"Of those, opened before the election: {len(pre)}; no response yet: {pre['overdue'].sum()}")
    if "has_delay_note" in elig.columns:
        print(f"Of those, had a post-closing holding/delay note: {int(elig['has_delay_note'].sum())}; "
              f"still unanswered: {int((elig['has_delay_note'] & ~elig['responded']).sum())}")

    t = elig.groupby("dept").agg(
        closed=("link", "size"),
        within_12w=("within_12w", "sum"),
        no_response=("overdue", "sum"),
        median_days=("days_to_response", "median"),
        delay_notes=("has_delay_note", "sum") if "has_delay_note" in elig.columns else ("link", lambda s: 0),
    )
    t["pct_within_12w"] = (100 * t["within_12w"] / t["closed"]).round(0)
    t["pct_no_response"] = (100 * t["no_response"] / t["closed"]).round(0)
    t = t.sort_values("pct_within_12w")
    t.to_csv(Path(outdir) / "departments_since_election.csv")
    print(t.to_string())

    print("\n== department consultations closed since the election with no response, oldest first")
    print(elig[elig["overdue"]].sort_values("closed")[["title", "dept", "opened", "closed"]].head(25).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:3])
