"""Figure 2: post-election department timeliness scorecard (departments with 10+ eligible consultations).

Usage: python3 -I scripts/figure_table.py data/departments_since_election.csv figures/fig2_departments.png
"""
import sys
from pathlib import Path

import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

_style_dir = Path(__file__).resolve().parents[1] / "figure_style"
if not _style_dir.is_dir():
    _style_dir = Path(__file__).resolve().parents[2] / "figure_style"
sys.path.insert(0, str(_style_dir))
from plot_setup import BASE_PT, PAL, figure, save, title_block  # noqa: E402

DISPLAY_NAMES = {
    "DESNZ/BEIS": "DESNZ",
    "BIST/DBT": "BIST / DBT",
    "MoJ": "Ministry of Justice",
}


def main(src, out):
    raw = pd.read_csv(src)
    d = raw[raw["closed"] >= 10].copy()
    d["exact_pct"] = 100 * d["within_12w"] / d["closed"]
    d["exact_no_resp"] = 100 * d["no_response"] / d["closed"]
    d = d.sort_values(["exact_pct", "exact_no_resp", "closed"], ascending=[False, True, False]).reset_index(drop=True)

    overall_closed = int(raw["closed"].sum())
    overall_w12 = int(raw["within_12w"].sum())
    overall_pct = round(100 * overall_w12 / overall_closed)
    small = raw[raw["closed"] < 10].sort_values("dept")
    small_note = ", ".join(f"{r['dept']} {int(r['within_12w'])}/{int(r['closed'])}" for _, r in small.iterrows())

    fig, ax = figure(aspect=0.88)
    ax.set_axis_off()
    ax.set_position([0, 0, 1, 1])

    top = 0.745
    step = 0.0435
    bar_x0, bar_w_max = 0.30, 0.22  # 0..50% track ends at 0.52; text sits cleanly at 0.535
    max_scale = 50.0

    # Column headers
    fig.text(0.035, top + 0.030, "Department", fontsize=BASE_PT * 0.84, color=PAL["muted"], weight="bold")
    fig.text(0.270, top + 0.030, "Closed\n(>12w)", fontsize=BASE_PT * 0.84, color=PAL["muted"], weight="bold", ha="right", va="bottom")
    fig.text(bar_x0, top + 0.030, "Responded within 12 weeks", fontsize=BASE_PT * 0.84, color=PAL["muted"], weight="bold")
    fig.text(0.815, top + 0.030, "No response\nyet", fontsize=BASE_PT * 0.84, color=PAL["muted"], weight="bold", ha="right", va="bottom")
    fig.text(0.965, top + 0.030, "Median\ndays*", fontsize=BASE_PT * 0.84, color=PAL["muted"], weight="bold", ha="right", va="bottom")
    fig.add_artist(Line2D([0.035, 0.965], [top + 0.021] * 2, color=PAL["ink"], lw=0.6))

    # Vertical dashed reference line behind the bars only (never crossing text labels)
    avg_x = bar_x0 + (overall_pct / max_scale) * bar_w_max
    y_bot = top - (len(d) - 0.5) * step
    fig.add_artist(Line2D([avg_x, avg_x], [y_bot, top + 0.021], color=PAL["ink"], lw=0.6, ls=(0, (2, 2)), zorder=1))
    fig.text(avg_x, y_bot - 0.011, f"Avg: {overall_pct}%", fontsize=BASE_PT * 0.78, color=PAL["muted"], ha="center", va="top")

    bar_h = step * 0.52
    for i, r in d.iterrows():
        y = top - i * step
        name = DISPLAY_NAMES.get(r["dept"], r["dept"])
        closed = int(r["closed"])
        w12 = int(r["within_12w"])
        nr = int(r["no_response"])
        pct_w12 = round(r["exact_pct"])
        pct_nr = round(r["exact_no_resp"])
        med = f"{r['median_days']:.1f}".rstrip("0").rstrip(".")

        fig.text(0.035, y, name, fontsize=BASE_PT * 0.89, va="center", color=PAL["ink"])
        fig.text(0.270, y, f"{closed}", fontsize=BASE_PT * 0.89, va="center", ha="right", color=PAL["muted"])

        fig.add_artist(Rectangle((bar_x0, y - bar_h / 2), bar_w_max, bar_h, facecolor=PAL["faint"], edgecolor="none", zorder=0))
        bw = (min(r["exact_pct"], max_scale) / max_scale) * bar_w_max
        if bw > 0:
            fig.add_artist(Rectangle((bar_x0, y - bar_h / 2), bw, bar_h, facecolor=PAL["accent"], edgecolor="none", zorder=2))
        fig.text(bar_x0 + bar_w_max + 0.015, y, f"{pct_w12}% ({w12})", fontsize=BASE_PT * 0.87, va="center", color=PAL["ink"])

        fig.text(0.815, y, f"{nr} ({pct_nr}%)", fontsize=BASE_PT * 0.87, va="center", ha="right", color=PAL["muted"])
        fig.text(0.965, y, med, fontsize=BASE_PT * 0.87, va="center", ha="right", color=PAL["muted"])
        fig.add_artist(Line2D([0.035, 0.965], [y - step / 2] * 2, color=PAL["faint"], lw=0.5))

    n_pre_texts = len(fig.texts)
    title_block(
        fig,
        "Department performance varies widely since the July 2024 election",
        "Consultations closed from 5 July 2024 and at least 12 weeks before 24 November 2026\n"
        "(14 departments with 10+ consultations; ordered by share answered within 12 weeks)",
        "Source: GOV.UK search and content APIs, 24 Nov 2026 (excludes holding/delay notices). *Median among answered.\n"
        f"Excludes <10-consultation depts ({small_note}); total N = {overall_closed} across 17 departments.",
    )
    fig.texts[n_pre_texts].set_fontsize(BASE_PT * 1.38)
    save(fig, out)


if __name__ == "__main__":
    main(*sys.argv[1:3])