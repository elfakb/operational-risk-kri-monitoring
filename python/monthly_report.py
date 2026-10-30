import sys

import pandas as pd

from config import *

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

metrics = pd.read_csv(PROCESSED_DIR / "monthly_metrics.csv")
kri = pd.read_csv(PROCESSED_DIR / "kri_monthly.csv")
alerts = pd.read_csv(PROCESSED_DIR / "alerts.csv")
matrix = pd.read_csv(PROCESSED_DIR / "risk_matrix.csv")
inc = pd.read_csv(RAW_DIR / "incidents.csv")
act = pd.read_csv(RAW_DIR / "corrective_actions.csv", parse_dates=["opened_date", "due_date", "closed_date"])

months = sorted(metrics["month"].unique())
cur = sys.argv[1] if len(sys.argv) > 1 else months[-1]
idx = months.index(cur)
prev = months[idx - 1]
trail = months[max(0, idx - 12):idx]
me = pd.Period(cur).end_time.normalize()

PCT = {"payment_failure_rate", "overdue_action_rate", "repeat_rate"}


def fmt(name, v):
    if pd.isna(v):
        return "n/m"
    return f"{v * 100:.2f}%" if name in PCT else f"{v:,.2f}"


def md_table(df):
    if df.empty:
        return "None."
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


bank = metrics.groupby("month")[["incidents", "loss_amount", "outage_minutes"]].sum()
head = []
for col, label in [("incidents", "Incidents"), ("loss_amount", "Realised loss (TRY)"), ("outage_minutes", "Outage minutes")]:
    c, p, t = bank.loc[cur, col], bank.loc[prev, col], bank.loc[trail, col].mean()
    head.append({"Metric": label, cur: f"{c:,.0f}", prev: f"{p:,.0f}", "12m avg": f"{t:,.0f}",
                 "vs 12m avg": f"{100 * (c - t) / t:+.0f}%" if t else "n/m"})
head = pd.DataFrame(head)

k = kri[kri["month"] == cur].copy()
n_red, n_amber = int((k["status"] == "red").sum()), int((k["status"] == "amber").sum())
n_watch = int(((k["status"] == "green") & (k["trend_watch"] == 1)).sum())
breaches = k[k["status"].isin(["amber", "red"])].copy()
breaches["order"] = breaches["status"].map({"red": 0, "amber": 1})
breaches = breaches.sort_values(["order", "business_unit"])
breach_tbl = pd.DataFrame({
    "Business unit": breaches["business_unit"], "KRI": breaches["kri"], "Status": breaches["status"],
    "Value": [fmt(n, v) for n, v in zip(breaches["kri"], breaches["value"])],
    "Amber threshold": [fmt(n, v) for n, v in zip(breaches["kri"], breaches["amber_threshold"])],
})

active = alerts[(alerts["start_month"] <= cur) & (alerts["end_month"].isna() | (alerts["end_month"] > cur))].copy()
active["months_active"] = [(pd.Period(cur) - pd.Period(s)).n + 1 for s in active["start_month"]]
active["order"] = active["level"].map({"red": 0, "amber": 1, "watch": 2})
active = active.sort_values(["order", "business_unit"])
alert_tbl = active[["alert_id", "business_unit", "kri", "risk_category", "level", "start_month", "months_active", "recurring"]]

a = act.merge(inc[["incident_id", "business_unit", "severity", "risk_category"]], on="incident_id")
is_open = (a["opened_date"] <= me) & (a["closed_date"].isna() | (a["closed_date"] > me))
od = a[is_open & (a["due_date"] < me)].copy()
od["days_overdue"] = (me - od["due_date"]).dt.days
od_unit = od.groupby("business_unit").agg(overdue_actions=("action_id", "count"),
                                          avg_days_overdue=("days_overdue", "mean")).round(0).reset_index()
od_top = od.sort_values("days_overdue", ascending=False).head(10)[
    ["action_id", "business_unit", "severity", "risk_category", "days_overdue"]]

top_matrix = matrix.sort_values("priority_rank").head(3)[
    ["priority_rank", "risk_category", "likelihood", "impact", "score", "rating", "total_loss", "alerts_in_window"]]

rec = []
for r in active.itertuples():
    rec.append({
        "priority": {"red": "P1", "amber": "P2", "watch": "P3"}[r.level],
        "business_unit": r.business_unit, "trigger": f"{r.kri} ({r.level})", "risk_category": r.risk_category,
        "recommended_action": KRI_ACTIONS[r.kri], "owner": f"{r.business_unit} Risk Owner",
        "target_days": {"red": 14, "amber": 30, "watch": 60}[r.level],
    })
for r in matrix[matrix["rating"].isin(["High", "Critical"])].itertuples():
    rec.append({
        "priority": "P1" if r.rating == "Critical" else "P2", "business_unit": "All",
        "trigger": f"risk matrix ({r.rating})", "risk_category": r.risk_category,
        "recommended_action": f"Review the control framework for {r.risk_category} and agree mitigation owners",
        "owner": "Head of Operational Risk", "target_days": 30,
    })
rec_df = pd.DataFrame(rec, columns=["priority", "business_unit", "trigger", "risk_category",
                                    "recommended_action", "owner", "target_days"])
rec_df = rec_df.sort_values(["priority", "business_unit"]).reset_index(drop=True)
rec_df.to_csv(REPORTS_DIR / "recommended_actions.csv", index=False)

report = f"""# Monthly Operational Risk Report: {cur}

All figures are based on synthetic data.

## 1. Headline
{md_table(head)}

## 2. KRI status
{n_red} red, {n_amber} amber and {n_watch} watch signals among {len(k)} unit-KRI combinations.

{md_table(breach_tbl)}

## 3. Active alerts
{md_table(alert_tbl)}

## 4. Corrective actions
{len(od)} open actions are past their due date.

{md_table(od_unit)}

Oldest overdue actions:

{md_table(od_top)}

## 5. Risk matrix, top priorities
Matrix window: {matrix['window_start'].iloc[0]} to {matrix['window_end'].iloc[0]}.

{md_table(top_matrix)}

## 6. Recommended actions
{md_table(rec_df[["priority", "business_unit", "trigger", "recommended_action", "target_days"]])}
"""
(REPORTS_DIR / "monthly_risk_report.md").write_text(report)
print(f"Report written for {cur}: {len(active)} active alerts, {len(od)} overdue actions, {len(rec_df)} recommended actions")