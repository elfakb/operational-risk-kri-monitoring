import numpy as np
import pandas as pd

from config import *

RAW_DIR.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)

DESCRIPTIONS = {
    "Payment Errors": ["Duplicate payment posted", "Payment rejected by gateway", "Wrong beneficiary account", "Payment batch partially processed"],
    "System Outages": ["Core banking slowdown", "Payment gateway unavailable", "Database failover event", "Channel application outage"],
    "Data Entry Errors": ["Incorrect amount keyed", "Customer data mismatch", "Wrong product code entered", "Missing mandatory field"],
    "Process Breaches": ["Approval step skipped", "Limit exceeded without authorisation", "Segregation of duties violation", "Procedure not followed"],
    "Unauthorized Transaction Attempts": ["Suspicious login and transfer attempt", "Unauthorised limit override attempt", "Blocked fraudulent transfer", "Credential misuse attempt"],
    "Reconciliation Breaks": ["Nostro account mismatch", "Unmatched settlement item", "Ledger and sub-ledger difference", "Card settlement discrepancy"],
}

months = pd.period_range(START_MONTH, periods=N_MONTHS, freq="M")
m_no = {str(p): i for i, p in enumerate(months, start=1)}

vol_rows, lookup = [], {}
for u in BUSINESS_UNITS:
    for p in months:
        i = m_no[str(p)]
        season = {11: 1.10, 12: 1.15}.get(p.month, 1.0)
        tx = int(BASE_TX[u] * (1.01 ** i) * season * rng.normal(1, 0.03))
        pay = int(tx * PAYMENT_SHARE[u])
        lookup[(u, str(p))] = (tx, pay)
        vol_rows.append({"business_unit": u, "month": str(p), "transactions": tx, "payments": pay, "data_label": DATA_LABEL})
volume = pd.DataFrame(vol_rows)


def multiplier(unit, cat, m):
    mult = 1.0
    if unit == "Retail Banking" and cat == "Payment Errors" and 20 <= m <= 25:
        mult *= 3.5
    if unit == "Payments" and cat == "System Outages" and 26 <= m <= 29:
        mult *= 3.0
    if unit == "Operations" and cat == "Data Entry Errors" and m >= 18:
        mult *= 1 + 0.05 * (m - 17)
    if unit == "Corporate Banking" and cat == "Process Breaches" and 14 <= m <= 16:
        mult *= 2.5
    if cat == "Reconciliation Breaks" and m % 12 == 0:
        mult *= 1.5
    return mult


def severity_of(loss, downtime):
    sev = "Critical"
    for limit, name in SEVERITY_BANDS:
        if loss < limit:
            sev = name
            break
    if downtime >= 120 and sev in ("Low", "Medium"):
        sev = "High"
    return sev


rows = []
for u in BUSINESS_UNITS:
    for p in months:
        m = m_no[str(p)]
        tx, pay = lookup[(u, str(p))]
        vf = tx / BASE_TX[u]
        for cat in CATEGORIES:
            lam = BASE_INCIDENTS[u] * CATEGORY_WEIGHTS[u][cat] * vf * multiplier(u, cat, m)
            for _ in range(rng.poisson(lam)):
                day = int(rng.integers(1, p.days_in_month + 1))
                date = pd.Timestamp(p.year, p.month, day)

                code_no = int(rng.integers(1, RC_COUNT + 1))
                if u == "Retail Banking" and cat == "Payment Errors" and 20 <= m <= 25 and rng.random() < 0.6:
                    code_no = 7
                if u == "Corporate Banking" and cat == "Process Breaches" and 14 <= m <= 16 and rng.random() < 0.5:
                    code_no = 3

                zero_p, mu, sigma = LOSS_PARAMS[cat]
                loss = 0.0 if rng.random() < zero_p else round(float(rng.lognormal(mu, sigma)), 2)

                downtime = 0.0
                if cat == "System Outages":
                    scale = 1.5 if (u == "Payments" and 26 <= m <= 29) else 1.0
                    downtime = round(float(rng.lognormal(np.log(6), 0.8)) * scale, 1)

                failed = 0
                if cat == "Payment Errors" and pay > 0:
                    failed = max(1, int(round(pay * rng.lognormal(np.log(0.0002), 0.6))))

                rows.append({
                    "incident_date": date, "month": str(p), "risk_category": cat, "business_unit": u,
                    "description": str(rng.choice(DESCRIPTIONS[cat])), "loss_amount": loss,
                    "downtime_min": downtime, "failed_payments": failed,
                    "severity": severity_of(loss, downtime),
                    "root_cause_code": f"RC-{CATEGORY_CODE[cat]}-{code_no:02d}",
                    "data_label": DATA_LABEL,
                })

inc = pd.DataFrame(rows).sort_values("incident_date").reset_index(drop=True)
inc.insert(0, "incident_id", [f"INC-{i:06d}" for i in range(1, len(inc) + 1)])

data_end = months[-1].end_time.normalize()
act_rows = []
for r in inc.itertuples():
    if rng.random() > ACTION_PROB[r.severity]:
        continue
    opened = r.incident_date + pd.Timedelta(days=int(rng.integers(1, 6)))
    if opened > data_end:
        continue
    due_days = ACTION_DAYS[r.severity]
    factor = rng.lognormal(np.log(0.55), 0.45)
    if r.business_unit == "Operations" and m_no[r.month] >= 20:
        factor *= 1.8
    closed = opened + pd.Timedelta(days=int(round(due_days * factor)))
    if rng.random() < 0.005 or closed > data_end:
        closed = pd.NaT
    act_rows.append({
        "incident_id": r.incident_id, "opened_date": opened,
        "due_date": opened + pd.Timedelta(days=due_days), "closed_date": closed,
        "status": "Open" if pd.isna(closed) else "Closed", "data_label": DATA_LABEL,
    })

actions = pd.DataFrame(act_rows)
actions.insert(0, "action_id", [f"CA-{i:06d}" for i in range(1, len(actions) + 1)])

for col in ["opened_date", "due_date", "closed_date"]:
    actions[col] = actions[col].dt.strftime("%Y-%m-%d")
inc["incident_date"] = inc["incident_date"].dt.strftime("%Y-%m-%d")

inc.to_csv(RAW_DIR / "incidents.csv", index=False)
volume.to_csv(RAW_DIR / "monthly_volume.csv", index=False)
actions.to_csv(RAW_DIR / "corrective_actions.csv", index=False)

print(f"Incidents: {len(inc)}, actions: {len(actions)}")
print(inc["risk_category"].value_counts())
print(inc["severity"].value_counts())