import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

from config import *

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

inc = pd.read_csv(RAW_DIR / "incidents.csv")
kri = pd.read_csv(PROCESSED_DIR / "kri_monthly.csv")
matrix = pd.read_csv(PROCESSED_DIR / "risk_matrix.csv")
act = pd.read_csv(RAW_DIR / "corrective_actions.csv", parse_dates=["opened_date", "due_date", "closed_date"])

STATUS_COLORS = {"green": "#4c9f70", "watch": "#3a86c8", "amber": "#f0a202", "red": "#d1495b", "n/m": "#cccccc"}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, dpi=150)
    plt.close(fig)


loss = inc.groupby("risk_category")["loss_amount"].sum().sort_values()
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(loss.index, loss.values / 1e6, color="#33658a")
ax.set_xlabel("Total realised loss (TRY million)")
ax.set_title("Loss by risk category (synthetic data)")
save(fig, "1_loss_by_category.png")

inc["quarter"] = pd.to_datetime(inc["month"]).dt.to_period("Q").astype(str)
q = inc.pivot_table(index="quarter", columns="business_unit", values="incident_id", aggfunc="count", fill_value=0)
fig, ax = plt.subplots(figsize=(9, 4.5))
q.plot(ax=ax, marker="o")
ax.set_ylabel("Incidents per quarter")
ax.set_xlabel("")
ax.set_title("Incident trend by business unit (synthetic data)")
ax.tick_params(axis="x", rotation=45)
save(fig, "2_incident_trend_by_unit.png")

last = kri["month_no"].max()
cur = kri[kri["month_no"] == last].copy()
cur["display"] = cur["status"]
cur.loc[(cur["status"] == "green") & (cur["trend_watch"] == 1), "display"] = "watch"
mat = cur.pivot(index="business_unit", columns="kri", values="display")
order = ["green", "watch", "amber", "red", "n/m"]
codes = mat.apply(lambda col: col.map({s: i for i, s in enumerate(order)}))
fig, ax = plt.subplots(figsize=(11, 4))
ax.imshow(codes.values, cmap=ListedColormap([STATUS_COLORS[s] for s in order]), vmin=0, vmax=len(order) - 1, aspect="auto")
ax.set_xticks(range(len(mat.columns)))
ax.set_xticklabels(mat.columns, rotation=30, ha="right")
ax.set_yticks(range(len(mat.index)))
ax.set_yticklabels(mat.index)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.text(j, i, mat.iloc[i, j], ha="center", va="center", color="white", fontsize=8)
ax.set_title(f"KRI status, {cur['month'].iloc[0]} (synthetic data)")
save(fig, "3_kri_status_latest.png")

me = pd.Period(sorted(inc["month"].unique())[-1]).end_time.normalize()
a = act.merge(inc[["incident_id", "business_unit", "severity"]], on="incident_id")
is_open = (a["opened_date"] <= me) & (a["closed_date"].isna() | (a["closed_date"] > me))
od = a[is_open & (a["due_date"] < me)]
if len(od):
    p = od.pivot_table(index="business_unit", columns="severity", values="action_id", aggfunc="count", fill_value=0)
    p = p.reindex(columns=[c for c in ["Low", "Medium", "High", "Critical"] if c in p.columns])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    p.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Overdue open actions")
    ax.set_xlabel("")
    ax.set_title("Overdue corrective actions by unit and severity (synthetic data)")
    ax.tick_params(axis="x", rotation=20)
    save(fig, "4_overdue_actions.png")


def rating_color(s):
    return {"Low": "#9bc995", "Medium": "#f6e27f", "High": "#f4a261", "Critical": "#e76f51"}[score_rating(s)]


fig, ax = plt.subplots(figsize=(8, 6))
for l in range(1, 6):
    for i in range(1, 6):
        ax.add_patch(Rectangle((i - 0.5, l - 0.5), 1, 1, facecolor=rating_color(l * i), edgecolor="white"))
for (l, i), g in matrix.groupby(["likelihood", "impact"]):
    ax.text(i, l, "\n".join(g["risk_category"]), ha="center", va="center", fontsize=7)
ax.set_xlim(0.5, 5.5)
ax.set_ylim(0.5, 5.5)
ax.set_xticks(range(1, 6))
ax.set_yticks(range(1, 6))
ax.set_xlabel("Impact (95th percentile loss band)")
ax.set_ylabel("Likelihood (mean monthly incidents band)")
ax.set_title("Risk matrix (synthetic data)")
save(fig, "5_risk_matrix.png")


def plot_kri(unit, name, ylabel, scale, fname):
    g = kri[(kri["business_unit"] == unit) & (kri["kri"] == name)].sort_values("month_no")
    x = range(len(g))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(x, g["value"] * scale, marker="o", color="#33658a", label="value")
    ax.plot(x, g["amber_threshold"] * scale, "--", color=STATUS_COLORS["amber"], label="amber threshold")
    ax.plot(x, g["red_threshold"] * scale, "--", color=STATUS_COLORS["red"], label="red threshold")
    ax.axvline(BASELINE_MONTHS - 0.5, color="grey", linestyle=":")
    ax.text(BASELINE_MONTHS - 0.3, ax.get_ylim()[1] * 0.95, "test period", fontsize=8, va="top")
    ax.set_xticks(list(x)[::3])
    ax.set_xticklabels(g["month"].iloc[::3], rotation=45)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{unit}: {name} (synthetic data)")
    ax.legend()
    save(fig, fname)


plot_kri("Retail Banking", "payment_failure_rate", "Payment failure rate (%)", 100, "6_retail_payment_failure_rate.png")
plot_kri("Payments", "outage_minutes", "Outage minutes per month", 1, "7_payments_outage_minutes.png")

print(f"Figures saved to {FIGURES_DIR}")