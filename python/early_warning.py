import numpy as np
import pandas as pd

from config import *

kri = pd.read_csv(PROCESSED_DIR / "kri_monthly.csv", usecols=lambda c: c != "trend_watch")
kri = kri.sort_values(["business_unit", "kri", "month_no"])
inc = pd.read_csv(RAW_DIR / "incidents.csv")


def add_watch(g):
    g = g.copy()
    v = g["value"]
    rising = (v.diff() > 0).astype(int).rolling(WATCH_RISES).sum() == WATCH_RISES
    near = v >= WATCH_RATIO * g["amber_threshold"]
    g["trend_watch"] = (rising & near & (g["status"] == "green")).astype(int)
    return g


kri = pd.concat([add_watch(g) for _, g in kri.groupby(["business_unit", "kri"])], ignore_index=True)
kri.to_csv(PROCESSED_DIR / "kri_monthly.csv", index=False)


def find_runs(flags):
    runs, start = [], None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        if not f and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(flags) - 1))
    return runs


def dominant_category(unit, kri_name, m_from, m_to):
    s = inc[(inc["business_unit"] == unit) & (inc["month"] >= m_from) & (inc["month"] <= m_to)]
    if s.empty:
        return "n/a"
    if kri_name == "loss_amount":
        return s.groupby("risk_category")["loss_amount"].sum().idxmax()
    return s["risk_category"].value_counts().index[0]


rows = []
for (unit, name), g in kri.groupby(["business_unit", "kri"]):
    g = g[g["period"] == "test"].sort_values("month_no").reset_index(drop=True)
    breach_runs = find_runs(g["status"].isin(["amber", "red"]).tolist())
    watch_runs = find_runs((g["trend_watch"] == 1).tolist())

    prev_close_no = None
    for s, e in breach_runs:
        seg = g.iloc[s:e + 1]
        closed = e + 1 < len(g)
        start_no = int(seg["month_no"].iloc[0])
        close_no = int(g["month_no"].iloc[e + 1]) if closed else None
        recurring = int(prev_close_no is not None and start_no - prev_close_no <= RECURRENCE_MONTHS)
        lead = g[(g["month_no"] >= start_no - 3) & (g["month_no"] < start_no)]
        category = KRI_CATEGORY.get(name) or dominant_category(unit, name, seg["month"].iloc[0], seg["month"].iloc[-1])
        rows.append({
            "business_unit": unit, "kri": name, "risk_category": category,
            "level": "red" if (seg["status"] == "red").any() else "amber",
            "start_month": seg["month"].iloc[0],
            "end_month": g["month"].iloc[e + 1] if closed else np.nan,
            "duration_months": len(seg), "status": "closed" if closed else "open",
            "months_to_close": len(seg) if closed else np.nan,
            "recurring": recurring, "preceded_by_watch": int(lead["trend_watch"].sum() > 0),
            "peak_value": seg["value"].max(), "amber_threshold": seg["amber_threshold"].iloc[0],
        })
        prev_close_no = close_no

    for s, e in watch_runs:
        seg = g.iloc[s:e + 1]
        closed = e + 1 < len(g)
        category = KRI_CATEGORY.get(name) or dominant_category(unit, name, seg["month"].iloc[0], seg["month"].iloc[-1])
        rows.append({
            "business_unit": unit, "kri": name, "risk_category": category, "level": "watch",
            "start_month": seg["month"].iloc[0],
            "end_month": g["month"].iloc[e + 1] if closed else np.nan,
            "duration_months": len(seg), "status": "closed" if closed else "open",
            "months_to_close": len(seg) if closed else np.nan,
            "recurring": 0, "preceded_by_watch": 0,
            "peak_value": seg["value"].max(), "amber_threshold": seg["amber_threshold"].iloc[0],
        })

alerts = pd.DataFrame(rows).sort_values(["start_month", "business_unit", "kri"]).reset_index(drop=True)
alerts.insert(0, "alert_id", [f"AL-{i:04d}" for i in range(1, len(alerts) + 1)])
alerts.round(6).to_csv(PROCESSED_DIR / "alerts.csv", index=False)

print(alerts.groupby(["level", "status"]).size())
breach = alerts[alerts["level"].isin(["amber", "red"])]
if len(breach):
    print("Breach alerts preceded by a watch signal:", round(breach["preceded_by_watch"].mean(), 2))
    print("Recurring breach alerts:", int(breach["recurring"].sum()))
    print("Mean months to close:", round(breach["months_to_close"].mean(), 2))