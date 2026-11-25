"""House style for Of Particular Interest figures (dual-mode transparent serif register, Substack column width).

Import from a post's figure script:
    from plot_setup import PAL, figure, title_block, save

Charter ships with macOS; on other systems matplotlib falls back to Georgia or DejaVu Serif.
"""
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FONT = "Charter"
BASE_PT = 10.5
WIDTH_IN = 7.0  # saved at 200 dpi -> 1400 px, 2x Substack's column
SAVE_DPI = 200

PAL = dict(
    accent="#C8523B",     # focal series/bars (3.98:1 on #F6F2EC, 3.96:1 on #191919)
    accent2="#477AA8",    # secondary accent (4.08:1 on #F6F2EC, 3.87:1 on #191919)
    ink="#797671",        # primary text, spines, reference lines (4.06:1 on #F6F2EC, 3.89:1 on #191919)
    muted="#7A7772EB",    # subtitles, secondary labels, sources (3.50:1 on #F6F2EC, 3.55:1 on #191919)
    context="#6E7B85",    # comparison series/bars (3.89:1 on #F6F2EC, 4.05:1 on #191919)
    faint="#7A777238",    # gridlines, row rules, empty slots (~1.29:1 on both #F6F2EC and #191919)
)

# Neutral mid-grey RGB with alpha=0 prevents dark or light halos on anti-aliased edges.
_TRANSPARENT = (121 / 255, 118 / 255, 113 / 255, 0.0)

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": [FONT, "Georgia", "DejaVu Serif"],
    "font.size": BASE_PT,
    "text.color": PAL["ink"],
    "axes.facecolor": "none",
    "axes.labelsize": BASE_PT,
    "axes.labelcolor": PAL["ink"],
    "axes.edgecolor": PAL["ink"],
    "axes.linewidth": 0.65,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "grid.color": PAL["faint"],
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "axes.formatter.useoffset": False,
    "xtick.color": PAL["ink"],
    "ytick.color": PAL["ink"],
    "xtick.labelsize": BASE_PT * 0.9,
    "ytick.labelsize": BASE_PT * 0.9,
    "legend.frameon": False,
    "figure.dpi": 100,
    "savefig.dpi": SAVE_DPI,
    "figure.facecolor": _TRANSPARENT,
})


def figure(aspect=0.62, nrows=1, ncols=1, **kw):
    fig, axes = plt.subplots(nrows, ncols, figsize=(WIDTH_IN, WIDTH_IN * aspect), **kw)
    fig.patch.set_facecolor(_TRANSPARENT)
    return fig, axes


def title_block(fig, title, subtitle, source, top=0.965, left=0.035, subtitle_gap=None):
    """Assertive title, measurement subtitle and source line, all on one left edge."""
    gap = subtitle_gap if subtitle_gap is not None else (0.282 / fig.get_figheight())
    fig.text(left, top, title, ha="left", va="top", fontsize=BASE_PT * 1.45, weight="bold", color=PAL["ink"])
    fig.text(left, top - gap, subtitle, ha="left", va="top", fontsize=BASE_PT * 0.95, color=PAL["muted"])
    fig.text(left, 0.026, source, ha="left", va="bottom", fontsize=BASE_PT * 0.78, color=PAL["muted"])


def save(fig, path):
    fig.savefig(path, dpi=SAVE_DPI, facecolor=_TRANSPARENT, edgecolor="none", transparent=True)
    plt.close(fig)
