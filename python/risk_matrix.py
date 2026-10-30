import pandas as pd

from config import *

inc = pd.read_csv(RAW_DIR / "incidents.csv")
alerts = pd.read_csv(PROCESSED_DIR / "alerts.csv")
months = sorted(pd.read_csv(RAW_DIR / "monthly_volume.csv")["month"].unique())
window = months[-MATRIX_WINDOW_MONTHS:]

w = inc[inc["month"].isin(window)]
total_loss_all = w["loss_amount"].sum()

rows = []
for cat in CATEGORIES:
    c = w[w["risk_category"] == cat]
    freq = len(c) / len(window)
    p95 = float(c["loss_amount"].quantile(0.95)) if len(c) else 0.0
    likelihood = 1 + sum(freq >= b for b in LIKELIHOOD_BANDS)
    impact = 1 + sum(p95 >= b for b in IMPACT_BANDS)
    score = likelihood * impact
    n_alerts = len(alerts[(alerts["risk_category"] == cat)
                          & (alerts["level"].isin(["amber", "red"]))
                          & (alerts["start_month"].isin(window))])
    rows.append({
        "risk_category": cat, "window_start": window[0], "window_end": window[-1],
        "mean_monthly_incidents": round(freq, 2), "total_loss": round(c["loss_amount"].sum(), 0),
        "mean_loss": round(c["loss_amount"].mean(), 0) if len(c) else 0,
        "p95_loss": round(p95, 0),
        "loss_share_pct": round(100 * c["loss_amount"].sum() / total_loss_all, 1) if total_loss_all else 0,
        "likelihood": likelihood, "impact": impact, "score": score,
        "rating": score_rating(score), "alerts_in_window": n_alerts,
    })

matrix = pd.DataFrame(rows).sort_values(["score", "total_loss"], ascending=False).reset_index(drop=True)
matrix["priority_rank"] = range(1, len(matrix) + 1)
matrix.to_csv(PROCESSED_DIR / "risk_matrix.csv", index=False)
print(matrix[["risk_category", "mean_monthly_incidents", "p95_loss", "likelihood", "impact", "score", "rating", "alerts_in_window"]])