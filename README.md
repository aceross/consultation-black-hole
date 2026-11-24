# "We are analysing your feedback" (updated 24 November 2026)

Companion code and data for *"We are analysing your feedback"* ([Of Particular Interest](https://ceross.substack.com)): how long GOV.UK consultations take to get a published response, 2019 to November 2026.

- Draft: `draft_20261031.md` · Figures: `figures/fig1_response_curves.png`, `figures/fig2_departments.png`
- Data: `data/consultations_since_2019.csv` (3,344 rows: 3,343 closed/outcome consultations and 1 redirect, with 2,657 datable responses and 687 unanswered), `data/departments_since_election.csv` (including `answered_later` and `explained_12w` Principle 10 counts), `data/km_curves.csv`, `data/km_summary_3cohorts.csv`, and console output (including the Principle 10 84-day breakdown) in `data/analysis_output.txt` and `data/departments_output.txt`
- Raw snapshot (24 November 2026): `data/raw/consultations.json` (GOV.UK search API listing, 7,550 items), `data/raw/content.jsonl` (GOV.UK content API extracts, 3,344 items)
- Closure log: `CLOSURE_LOG.md`

## Dependencies

Install packages from `requirements.txt` (`matplotlib>=3.11.2` is required on macOS for proper `Charter` Roman and Bold weights). `scripts/figure.py` and `scripts/figure_table.py` import the bundled house style module in `figure_style/plot_setup.py` (falling back to `../figure_style/plot_setup.py` when run inside the parent workspace).

## Reproduce from the 24 November 2026 snapshot

Using `uv` (Python 3.12 with `pandas`, `numpy` and `matplotlib>=3.11.2`):

```
uv run --offline --python 3.12 --with pandas --with matplotlib --with numpy python -I scripts/analyse.py data/raw/consultations.json data/raw/content.jsonl data > data/analysis_output.txt
uv run --offline --python 3.12 --with pandas --with matplotlib --with numpy python -I scripts/departments.py data/consultations_since_2019.csv data > data/departments_output.txt
uv run --offline --python 3.12 --with pandas --with matplotlib --with numpy python -I scripts/figure.py data/consultations_since_2019.csv figures/fig1_response_curves.png
uv run --offline --python 3.12 --with pandas --with matplotlib --with numpy python -I scripts/figure_table.py data/departments_since_election.csv figures/fig2_departments.png
```

Or in an activated Python 3 environment with `requirements.txt` installed:

```
python3 -I scripts/analyse.py data/raw/consultations.json data/raw/content.jsonl data > data/analysis_output.txt
python3 -I scripts/departments.py data/consultations_since_2019.csv data > data/departments_output.txt
python3 -I scripts/figure.py data/consultations_since_2019.csv figures/fig1_response_curves.png
python3 -I scripts/figure_table.py data/departments_since_election.csv figures/fig2_departments.png
```

## Optional live GOV.UK API refresh

To refresh `data/raw/` against the live GOV.UK APIs (which will include consultations closed or updated after 24 November 2026):

```
python3 -I scripts/fetch_consultations.py data/raw/consultations.json
python3 -I scripts/fetch_content.py data/raw/consultations.json 2019-01-01 data/raw/content.jsonl
```

## Licence and attribution

The raw extracts in `data/raw/` (`consultations.json` and `content.jsonl` from the GOV.UK Search API and Content API, covering consultations listed under the [GOV.UK Consultation Principles](https://www.gov.uk/government/publications/consultation-principles-guidance/consultation-principles-2018)) contain public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) (© Crown copyright).
