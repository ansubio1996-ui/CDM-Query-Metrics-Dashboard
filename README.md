# CDM Query Metrics & Dashboard

A Python analytics tool for clinical data query management — analyzes query volume, turnaround time, aging, status distribution, site performance, and domain-level breakdowns. Generates an interactive self-contained HTML dashboard with embedded charts and CSV summaries.

## Features

- **KPI Dashboard** — total queries, open/closed counts, average turnaround time, closed rate, high-priority open queries
- **7 Chart Visualizations**:
  - Query status pie chart
  - Query volume by site (bar)
  - Query aging distribution (histogram)
  - Queries by SDTM domain (bar)
  - Query types breakdown (horizontal bar)
  - Priority vs status (stacked bar)
  - Turnaround trend over time (line + bar combo)
- **Site Performance Report** — per-site query counts, open/closed, average days open
- **Domain Breakdown** — query distribution across DM, AE, LB, PD, DS domains
- **Self-Contained HTML** — charts embedded as base64, no external dependencies

## Project Structure

```
cdm-query-metrics/
├── data/
│   ├── queries.csv          # Synthetic query management data
│   └── dm.csv               # Demographics for site mapping
├── src/
│   └── query_dashboard.py   # Main analytics engine
├── results/                  # Generated dashboard + CSVs + charts
│   └── charts/               # Individual chart PNGs
├── requirements.txt
└── README.md
```

## Quick Start

```bash
pip install -r requirements.txt

python src/query_dashboard.py --data-dir data/ --output-dir results/

open results/query_dashboard.html
```

## Sample Output

```
==================================================
  QUERY METRICS SUMMARY
==================================================
  total_queries: 243
  open: 73
  closed: 97
  avg_turnaround_days: 7.2
  closed_rate_pct: 39.9%
  high_priority_open: 11
  queries_per_site: 24.3
==================================================
```

## Demo Data

All datasets are **100% synthetic** — 243 queries across 10 sites and 5 SDTM domains.

## Author

**Ansuman Mohapatra** — Clinical Data Specialist | 6+ years CDM experience at IQVIA
- LinkedIn: [ansuman-mohapatra9b663116](https://linkedin.com/in/ansuman-mohapatra9b663116)

## License

MIT License
