import numpy as np
import pandas as pd

from config import *

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

inc = pd.read_csv(RAW_DIR / "incidents.csv", parse_dates=["incident_date"])
vol = pd.read_csv(RAW_DIR / "monthly_volume.csv")
act = pd.read_csv(RAW_DIR / "corrective_actions.csv", parse_dates=["opened_date", "due_date", "closed_date"])

inc = inc.sort_values(["business_unit", "root_cause_code", "incident_date"])
gap = inc.groupby(["business_unit", "root_cause_code"])["incident_date"].diff().dt.days
inc["is_repeat"] = (gap <= REPEAT_WINDOW_DAYS).astype(int)
inc = inc.sort_values("incident_id")

saved = inc.copy()
saved["incident_date"] = saved["incident_date"].dt.strftime("%Y-%m-%d")
saved.to_csv(PROCESSED_DIR / "incidents_enriched.csv", index=False)

months = sorted(vol["month"].unique())
inc["is_error"] = inc["risk_category"].isin(ERROR_CATEGORIES).astype(int)

agg = inc.groupby(["business_unit", "month"]).agg(
    incidents=("incident_id", "count"),
    error_events=("is_error", "sum"),
    loss_amount=("loss_amount", "sum"),
    outage_minutes=("downtime_min", "sum"),
    failed_payments=("failed_payments", "sum"),
    repeats=("is_repeat", "sum"),
).reset_index()

df = vol[["business_unit", "month", "transactions", "payments"]].merge(agg, on=["business_unit", "month"], how="left")
for c in ["incidents", "error_events", "loss_amount", "outage_minutes", "failed_payments", "repeats"]:
    df[c] = df[c].fillna(0)
df = df.sort_values(["business_unit", "month"]).reset_index(drop=True)

act = act.merge(inc[["incident_id", "business_unit"]], on="incident_id")
month_ends = {m: pd.Period(m).end_time.normalize() for m in months}


def action_stats(unit, month):
    me = month_ends[month]
    a = act[act["business_unit"] == unit]
    is_open = (a["opened_date"] <= me) & (a["closed_date"].isna() | (a["closed_date"] > me))
    return int(is_open.sum()), int((is_open & (a["due_date"] < me)).sum())


stats = [action_stats(u, m) for u, m in zip(df["business_unit"], df["month"])]
df["open_actions"] = [s[0] for s in stats]
df["overdue_actions"] = [s[1] for s in stats]

df["incidents_per_1000_tx"] = df["error_events"] / df["transactions"] * 1000
df["payment_failure_rate"] = df["failed_payments"] / df["payments"].replace(0, np.nan)
df["overdue_action_rate"] = (df["overdue_actions"] / df["open_actions"].replace(0, np.nan)).where(df["open_actions"] >= MIN_OPEN_FOR_RATE)
df["repeat_rate"] = (df["repeats"] / df["incidents"].replace(0, np.nan)).where(df["incidents"] >= MIN_INCIDENTS_FOR_RATE)

df.round(6).to_csv(PROCESSED_DIR / "monthly_metrics.csv", index=False)

long = df.melt(id_vars=["business_unit", "month"], value_vars=list(KRI_RULES), var_name="kri", value_name="value")
long["month_no"] = long["month"].map({m: i for i, m in enumerate(months, start=1)})
long["period"] = np.where(long["month_no"] <= BASELINE_MONTHS, "baseline", "test")


def thresholds(kri, base):
    rule = KRI_RULES[kri]
    if rule["method"] == "fixed":
        return rule["amber"], rule["red"]
    base = base.dropna()
    if len(base) < 6:
        return np.nan, np.nan
    if rule["method"] == "std":
        mu, sd = base.mean(), base.std(ddof=1)
        return mu + rule["k"][0] * sd, mu + rule["k"][1] * sd
    a, r = np.percentile(base, rule["p"])
    return a, r


thr = {}
for (u, k), g in long.groupby(["business_unit", "kri"]):
    thr[(u, k)] = thresholds(k, g.loc[g["period"] == "baseline", "value"])

long["amber_threshold"] = [thr[(u, k)][0] for u, k in zip(long["business_unit"], long["kri"])]
long["red_threshold"] = [thr[(u, k)][1] for u, k in zip(long["business_unit"], long["kri"])]


def status(v, a, r):
    if pd.isna(v) or pd.isna(a):
        return "n/m"
    if a <= 0 and v <= 0:
        return "green"
    if v >= r:
        return "red"
    if v >= a:
        return "amber"
    return "green"


long["status"] = [status(v, a, r) for v, a, r in zip(long["value"], long["amber_threshold"], long["red_threshold"])]
long = long.sort_values(["business_unit", "kri", "month_no"])
long[["business_unit", "month", "month_no", "period", "kri", "value", "amber_threshold", "red_threshold", "status"]] \
    .round(6).to_csv(PROCESSED_DIR / "kri_monthly.csv", index=False)

pd.DataFrame(KRI_DEFINITIONS).to_csv(PROCESSED_DIR / "kri_definitions.csv", index=False)

print(long[long["period"] == "test"].groupby(["kri", "status"]).size().unstack(fill_value=0))