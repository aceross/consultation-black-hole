"""Figure 1: share of department consultations with a published response, by weeks since closing.

Usage: python3 -I scripts/figure.py data/consultations_since_2019.csv figures/fig1_response_curves.png
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
_style_dir = Path(__file__).resolve().parents[1] / "figure_style"
if not _style_dir.is_dir():
    _style_dir = Path(__file__).resolve().parents[2] / "figure_style"
sys.path.insert(0, str(_style_dir))
from departments import DEPARTMENTS, SNAPSHOT, km_cumulative  # noqa: E402
from plot_setup import BASE_PT, PAL, figure, save, title_block  # noqa: E402

COHORTS = [
    ("2019-01-01", "2022-01-01", "2019 to 2021", PAL["context"], (0, (4, 2)), 1.65),
    ("2022-01-01", "2024-07-05", "2022 to July 2024", PAL["ink"], "-", 1.65),
    ("2024-07-05", "2026-11-24", "Since the July 2024 election", PAL["accent"], "-", 2.35),
]


def main(src, out):
    d = pd.read_csv(src, parse_dates=["closed", "response_date"])
    d = d[(d["doc_type"] != "redirect") & d["lead_org"].map(DEPARTMENTS).notna()].copy()
    elapsed = (SNAPSHOT - d["closed"]).dt.days
    d["t"] = np.where(d["responded"], d["days_to_response"].clip(lower=0), elapsed)
    weeks = np.arange(0, 105)

    fig, ax = figure(aspect=0.66)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.755, bottom=0.215)
    ends = []
    for start, end, label, colour, ls, lw in COHORTS:
        g = d[(d["closed"] >= pd.Timestamp(start, tz="UTC")) & (d["closed"] < pd.Timestamp(end, tz="UTC"))]
        cum = 100 * km_cumulative(g["t"].values, g["event"].values if "event" in g else g["responded"].values, weeks * 7)
        if start == "2024-07-05":
            ax.step(weeks[:83], cum[:83], where="post", color=colour, ls=ls, lw=lw)
            ax.step(weeks[82:], cum[82:], where="post", color=colour, ls=(0, (1.5, 2)), lw=2.05)
        else:
            ax.step(weeks, cum, where="post", color=colour, ls=ls, lw=lw)
        last = np.nanmax(np.where(~np.isnan(cum))[0])
        ends.append((cum[last], f"{label} ({len(g)})", colour, ls, lw))
    # The curves overlap, so a compact key in the empty lower-right corner beats end labels.
    ax.text(62, 42, "Consultations that closed:", fontsize=BASE_PT * 0.85, color=PAL["muted"], va="center")
    for i, (_, text, colour, ls, lw) in enumerate(reversed(ends)):
        y = 34 - i * 8
        ax.plot([62, 68], [y, y], color=colour, ls=ls, lw=lw)
        ax.text(70, y, text, va="center", fontsize=BASE_PT * 0.85,
                color=colour if colour == PAL["accent"] else PAL["ink"])
    ax.axvline(12, color=PAL["ink"], lw=0.75, ls=(0, (2, 2)))
    ax.text(13, 96, "12-week target", fontsize=BASE_PT * 0.85, va="top", color=PAL["ink"])
    ax.set_xlim(0, 104)
    ax.set_ylim(0, 100)
    ax.set_xticks([0, 12, 26, 52, 78, 104], ["0", "12", "26", "52", "78", "104 weeks"])
    ax.set_yticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100%"])
    ax.grid(axis="y")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Weeks since the consultation closed")

    title_block(
        fig,
        "Four in five recent consultations miss the 12-week target",
        "Share of ministerial department and HMRC consultations with a recorded response on the\n"
        "consultation page, by weeks since closing (dotted tail: fewer than 20 remaining under observation)",
        "Source: GOV.UK search and content APIs, 24 November 2026. Recorded response date is the first substantive\n"
        f"change-history entry after closing (excluding holding notices). {len(d):,} consultations closed Jan 2019–Nov 2026.",
    )
    save(fig, out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
