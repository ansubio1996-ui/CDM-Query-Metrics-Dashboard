"""
Clinical Data Management — Query Metrics & Dashboard.

Analyzes query management data from clinical trials: query volume, turnaround
time, aging, status distribution, site performance, and domain-level breakdowns.
Generates an interactive HTML dashboard with charts and a CSV summary.

Usage:
    python src/query_dashboard.py --data-dir data/ --output-dir results/
"""

import argparse
import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


class QueryMetricsAnalyzer:
    """Analyzes clinical data query metrics and generates dashboard."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.queries = None
        self.dm = None
        self.charts = {}

    def load_data(self):
        q_path = self.data_dir / "queries.csv"
        dm_path = self.data_dir / "dm.csv"
        if q_path.exists():
            self.queries = pd.read_csv(q_path, parse_dates=["OPEN_DATE", "CLOSE_DATE"])
            print(f"  Loaded queries: {len(self.queries)} records")
        if dm_path.exists():
            self.dm = pd.read_csv(dm_path)
            print(f"  Loaded DM: {len(self.dm)} records")

    # ── chart generation ─────────────────────
    def _save_chart(self, name, fig):
        path = os.path.join(self.chart_dir, f"{name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        self.charts[name] = path
        print(f"    Chart saved: {name}.png")

    def chart_query_status(self):
        """Pie chart — query status distribution."""
        counts = self.queries["QUERY_STATUS"].value_counts()
        fig, ax = plt.subplots(figsize=(7, 5))
        colors = {"OPEN": "#e53e3e", "ANSWERED": "#dd6b20", "CLOSED": "#38a169", "CANCELLED": "#a0aec0"}
        pie_colors = [colors.get(s, "#ccc") for s in counts.index]
        ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", colors=pie_colors,
               startangle=90, textprops={"fontsize": 12})
        ax.set_title("Query Status Distribution", fontsize=14, fontweight="bold")
        self._save_chart("query_status", fig)

    def chart_queries_by_site(self):
        """Bar chart — queries by site."""
        site_counts = self.queries.groupby("SITEID").size().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(range(len(site_counts)), site_counts.values, color="#3182ce")
        ax.set_xticks(range(len(site_counts)))
        ax.set_xticklabels(site_counts.index, rotation=45, ha="right", fontsize=9)
        ax.set_xlabel("Site")
        ax.set_ylabel("Number of Queries")
        ax.set_title("Query Volume by Site", fontsize=14, fontweight="bold")
        ax.bar_label(bars, padding=3, fontsize=8)
        self._save_chart("queries_by_site", fig)

    def chart_query_aging(self):
        """Histogram — query aging (days open)."""
        fig, ax = plt.subplots(figsize=(8, 5))
        open_queries = self.queries[self.queries["QUERY_STATUS"] == "OPEN"]
        closed_queries = self.queries[self.queries["QUERY_STATUS"] == "CLOSED"]
        bins = [0, 1, 3, 5, 7, 10, 15, 30, 60]
        ax.hist([closed_queries["DAYS_OPEN"].clip(0, 60), open_queries["DAYS_OPEN"].clip(0, 60)],
                bins=bins, label=["Closed", "Open"], color=["#38a169", "#e53e3e"], edgecolor="white")
        ax.set_xlabel("Days Open")
        ax.set_ylabel("Number of Queries")
        ax.set_title("Query Aging Distribution", fontsize=14, fontweight="bold")
        ax.legend()
        self._save_chart("query_aging", fig)

    def chart_queries_by_domain(self):
        """Bar chart — queries by SDTM domain."""
        domain_counts = self.queries.groupby("DOMAIN").size().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.bar(domain_counts.index, domain_counts.values, color="#805ad5")
        ax.set_xlabel("Domain")
        ax.set_ylabel("Queries")
        ax.set_title("Queries by Domain", fontsize=14, fontweight="bold")
        ax.bar_label(bars, padding=3, fontsize=10)
        self._save_chart("queries_by_domain", fig)

    def chart_queries_by_type(self):
        """Horizontal bar — query types."""
        type_counts = self.queries["QUERY_TYPE"].value_counts()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(range(len(type_counts)), type_counts.values, color="#319795")
        ax.set_yticks(range(len(type_counts)))
        ax.set_yticklabels(type_counts.index, fontsize=10)
        ax.set_xlabel("Number of Queries")
        ax.set_title("Query Types Breakdown", fontsize=14, fontweight="bold")
        ax.invert_yaxis()
        self._save_chart("queries_by_type", fig)

    def chart_priority_breakdown(self):
        """Stacked bar — priority vs status."""
        pivot = self.queries.groupby(["QUERY_PRIORITY", "QUERY_STATUS"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(7, 4))
        colors = {"OPEN": "#e53e3e", "ANSWERED": "#dd6b20", "CLOSED": "#38a169", "CANCELLED": "#a0aec0"}
        bottom = [0] * len(pivot)
        for status in ["OPEN", "ANSWERED", "CLOSED", "CANCELLED"]:
            if status in pivot.columns:
                ax.bar(pivot.index, pivot[status], bottom=bottom, label=status,
                       color=colors.get(status, "#ccc"))
                bottom = [b + v for b, v in zip(bottom, pivot[status])]
        ax.set_xlabel("Priority")
        ax.set_ylabel("Queries")
        ax.set_title("Query Priority vs Status", fontsize=14, fontweight="bold")
        ax.legend()
        self._save_chart("priority_breakdown", fig)

    def chart_turnaround_trend(self):
        """Line chart — average turnaround time by month."""
        self.queries["OPEN_MONTH"] = self.queries["OPEN_DATE"].dt.to_period("M").astype(str)
        monthly = self.queries.groupby("OPEN_MONTH").agg(
            avg_days=("DAYS_OPEN", "mean"),
            count=("QUERYID", "count")
        ).reset_index()
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(monthly["OPEN_MONTH"], monthly["avg_days"], marker="o", color="#e53e3e", linewidth=2)
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Avg Days Open", color="#e53e3e")
        ax1.tick_params(axis="x", rotation=45)
        ax1.tick_params(axis="y", labelcolor="#e53e3e")
        ax2 = ax1.twinx()
        ax2.bar(monthly["OPEN_MONTH"], monthly["count"], alpha=0.3, color="#3182ce")
        ax2.set_ylabel("Query Volume", color="#3182ce")
        ax2.tick_params(axis="y", labelcolor="#3182ce")
        ax1.set_title("Query Turnaround Trend", fontsize=14, fontweight="bold")
        self._save_chart("turnaround_trend", fig)

    # ── metrics computation ───────────────────
    def compute_metrics(self):
        """Compute summary metrics."""
        q = self.queries
        open_q = q[q["QUERY_STATUS"] == "OPEN"]
        closed_q = q[q["QUERY_STATUS"] == "CLOSED"]
        high_priority_open = open_q[open_q["QUERY_PRIORITY"] == "HIGH"]
        return {
            "total_queries": len(q),
            "open": len(open_q),
            "closed": len(closed_q),
            "answered": len(q[q["QUERY_STATUS"] == "ANSWERED"]),
            "cancelled": len(q[q["QUERY_STATUS"] == "CANCELLED"]),
            "avg_turnaround_days": round(closed_q["DAYS_OPEN"].mean(), 1) if len(closed_q) else 0,
            "max_days_open": int(q["DAYS_OPEN"].max()),
            "high_priority_open": len(high_priority_open),
            "queries_per_site": round(len(q) / q["SITEID"].nunique(), 1),
            "closed_rate_pct": round(len(closed_q) / len(q) * 100, 1),
        }

    def generate_csv_summary(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        m = self.compute_metrics()
        # Save metrics
        metrics_df = pd.DataFrame(list(m.items()), columns=["Metric", "Value"])
        metrics_df.to_csv(os.path.join(output_dir, "query_metrics_summary.csv"), index=False)
        # Save site performance
        site_perf = self.queries.groupby("SITEID").agg(
            total_queries=("QUERYID", "count"),
            open=("QUERY_STATUS", lambda x: (x == "OPEN").sum()),
            closed=("QUERY_STATUS", lambda x: (x == "CLOSED").sum()),
            avg_days_open=("DAYS_OPEN", "mean"),
        ).round(1).sort_values("total_queries", ascending=False)
        site_perf.to_csv(os.path.join(output_dir, "site_performance.csv"))
        # Save domain breakdown
        domain_perf = self.queries.groupby("DOMAIN").agg(
            total=("QUERYID", "count"),
            open=("QUERY_STATUS", lambda x: (x == "OPEN").sum()),
            closed=("QUERY_STATUS", lambda x: (x == "CLOSED").sum()),
        )
        domain_perf.to_csv(os.path.join(output_dir, "domain_breakdown.csv"))
        print(f"  CSV summaries saved to {output_dir}/")

    def generate_html_dashboard(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        m = self.compute_metrics()

        # Embed charts as base64 for a self-contained HTML
        import base64
        chart_tags = {}
        for name, path in self.charts.items():
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            chart_tags[name] = f"data:image/png;base64,{encoded}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CDM Query Metrics Dashboard</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px; background: #f5f7fa; color: #333; }}
  h1 {{ color: #1a3a5c; border-bottom: 3px solid #1a3a5c; padding-bottom: 10px; margin-top: 0; }}
  .kpi-row {{ display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; }}
  .kpi {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-width: 140px; text-align: center; }}
  .kpi .value {{ font-size: 1.8em; font-weight: bold; color: #1a3a5c; }}
  .kpi .label {{ font-size: 0.85em; color: #718096; margin-top: 5px; }}
  .kpi.red .value {{ color: #e53e3e; }}
  .kpi.green .value {{ color: #38a169; }}
  .kpi.orange .value {{ color: #dd6b20; }}
  .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }}
  .chart-box {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
  .chart-box img {{ width: 100%; height: auto; }}
  .chart-box h3 {{ color: #2c5282; margin-top: 0; }}
  .footer {{ margin-top: 40px; color: #a0aec0; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>Query Metrics Dashboard</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Study: DEMO-STUDY01</p>

<div class="kpi-row">
  <div class="kpi"><div class="value">{m['total_queries']}</div><div class="label">Total Queries</div></div>
  <div class="kpi red"><div class="value">{m['open']}</div><div class="label">Open</div></div>
  <div class="kpi green"><div class="value">{m['closed']}</div><div class="label">Closed</div></div>
  <div class="kpi orange"><div class="value">{m['avg_turnaround_days']}</div><div class="label">Avg Turnaround (days)</div></div>
  <div class="kpi"><div class="value">{m['closed_rate_pct']}%</div><div class="label">Closed Rate</div></div>
  <div class="kpi red"><div class="value">{m['high_priority_open']}</div><div class="label">High Priority Open</div></div>
</div>

<div class="chart-grid">
  <div class="chart-box"><h3>Query Status</h3><img src="{chart_tags['query_status']}"></div>
  <div class="chart-box"><h3>Query Volume by Site</h3><img src="{chart_tags['queries_by_site']}"></div>
  <div class="chart-box"><h3>Query Aging</h3><img src="{chart_tags['query_aging']}"></div>
  <div class="chart-box"><h3>Queries by Domain</h3><img src="{chart_tags['queries_by_domain']}"></div>
  <div class="chart-box"><h3>Query Types</h3><img src="{chart_tags['queries_by_type']}"></div>
  <div class="chart-box"><h3>Priority vs Status</h3><img src="{chart_tags['priority_breakdown']}"></div>
  <div class="chart-box" style="grid-column: span 2;"><h3>Turnaround Trend</h3><img src="{chart_tags['turnaround_trend']}"></div>
</div>

<div class="footer">CDM Query Metrics Dashboard | Demo data for portfolio | Generated with Python + Matplotlib</div>
</body>
</html>"""
        path = os.path.join(output_dir, "query_dashboard.html")
        with open(path, "w") as f:
            f.write(html)
        print(f"  HTML dashboard: {path}")

    def run(self, output_dir):
        self.chart_dir = os.path.join(output_dir, "charts")
        os.makedirs(self.chart_dir, exist_ok=True)
        print("\n  Generating charts...")
        self.chart_query_status()
        self.chart_queries_by_site()
        self.chart_query_aging()
        self.chart_queries_by_domain()
        self.chart_queries_by_type()
        self.chart_priority_breakdown()
        self.chart_turnaround_trend()
        self.generate_csv_summary(output_dir)
        self.generate_html_dashboard(output_dir)

        m = self.compute_metrics()
        print(f"\n{'='*50}")
        print(f"  QUERY METRICS SUMMARY")
        print(f"{'='*50}")
        for k, v in m.items():
            print(f"  {k}: {v}")
        print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="CDM Query Metrics Dashboard")
    parser.add_argument("--data-dir", default="data/")
    parser.add_argument("--output-dir", default="results/")
    args = parser.parse_args()
    analyzer = QueryMetricsAnalyzer(args.data_dir)
    analyzer.load_data()
    analyzer.run(args.output_dir)
    print("\nDashboard generation complete. Check results/ directory.\n")


if __name__ == "__main__":
    main()
