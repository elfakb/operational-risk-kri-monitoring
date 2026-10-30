from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = BASE_DIR / "data" / "risk.db"

SEED = 42
START_MONTH = "2022-01"
N_MONTHS = 36
BASELINE_MONTHS = 12
DATA_LABEL = "SYNTHETIC"

BUSINESS_UNITS = ["Retail Banking", "Corporate Banking", "Payments", "Treasury", "Operations"]
CATEGORIES = [
    "Payment Errors", "System Outages", "Data Entry Errors",
    "Process Breaches", "Unauthorized Transaction Attempts", "Reconciliation Breaks",
]
ERROR_CATEGORIES = ["Payment Errors", "Data Entry Errors", "Reconciliation Breaks", "Process Breaches"]
CATEGORY_CODE = {
    "Payment Errors": "PE", "System Outages": "SO", "Data Entry Errors": "DE",
    "Process Breaches": "PB", "Unauthorized Transaction Attempts": "UA",
    "Reconciliation Breaks": "RB",
}
RC_COUNT = 40

BASE_TX = {"Retail Banking": 40000, "Corporate Banking": 6000, "Payments": 60000, "Treasury": 2000, "Operations": 15000}
PAYMENT_SHARE = {"Retail Banking": 0.55, "Corporate Banking": 0.5, "Payments": 1.0, "Treasury": 0.0, "Operations": 0.0}
BASE_INCIDENTS = {"Retail Banking": 20, "Corporate Banking": 10, "Payments": 24, "Treasury": 6, "Operations": 16}

CATEGORY_WEIGHTS = {
    "Retail Banking": {"Payment Errors": 0.35, "System Outages": 0.08, "Data Entry Errors": 0.22,
                       "Process Breaches": 0.12, "Unauthorized Transaction Attempts": 0.08, "Reconciliation Breaks": 0.15},
    "Corporate Banking": {"Payment Errors": 0.25, "System Outages": 0.07, "Data Entry Errors": 0.25,
                          "Process Breaches": 0.20, "Unauthorized Transaction Attempts": 0.05, "Reconciliation Breaks": 0.18},
    "Payments": {"Payment Errors": 0.35, "System Outages": 0.10, "Data Entry Errors": 0.10,
                 "Process Breaches": 0.10, "Unauthorized Transaction Attempts": 0.10, "Reconciliation Breaks": 0.25},
    "Treasury": {"Payment Errors": 0.10, "System Outages": 0.10, "Data Entry Errors": 0.20,
                 "Process Breaches": 0.25, "Unauthorized Transaction Attempts": 0.10, "Reconciliation Breaks": 0.25},
    "Operations": {"Payment Errors": 0.10, "System Outages": 0.10, "Data Entry Errors": 0.35,
                   "Process Breaches": 0.20, "Unauthorized Transaction Attempts": 0.02, "Reconciliation Breaks": 0.23},
}

# (probability of zero loss / near miss, lognormal mu, lognormal sigma), amounts in TRY
LOSS_PARAMS = {
    "Payment Errors": (0.25, 8.5, 1.2),
    "System Outages": (0.30, 9.5, 1.4),
    "Data Entry Errors": (0.30, 7.5, 1.0),
    "Process Breaches": (0.25, 8.0, 1.3),
    "Unauthorized Transaction Attempts": (0.20, 10.0, 1.8),
    "Reconciliation Breaks": (0.25, 8.2, 1.1),
}

SEVERITY_BANDS = [(5_000, "Low"), (50_000, "Medium"), (250_000, "High")]
ACTION_DAYS = {"Low": 90, "Medium": 60, "High": 45, "Critical": 30}
ACTION_PROB = {"Low": 0.25, "Medium": 0.80, "High": 1.0, "Critical": 1.0}

REPEAT_WINDOW_DAYS = 90
MIN_INCIDENTS_FOR_RATE = 5
MIN_OPEN_FOR_RATE = 5
WATCH_RATIO = 0.8
WATCH_RISES = 3
RECURRENCE_MONTHS = 6

AVAILABILITY_SLA = 0.999
ALLOWED_DOWNTIME_MIN = 30 * 24 * 60 * (1 - AVAILABILITY_SLA)  # 43.2 minutes per month

KRI_RULES = {
    "incidents_per_1000_tx": {"method": "std", "k": (2, 3)},
    "payment_failure_rate": {"method": "fixed", "amber": 0.003, "red": 0.005},
    "outage_minutes": {"method": "fixed", "amber": 0.8 * ALLOWED_DOWNTIME_MIN, "red": ALLOWED_DOWNTIME_MIN},
    "open_actions": {"method": "percentile", "p": (90, 97.5)},
    "overdue_action_rate": {"method": "fixed", "amber": 0.15, "red": 0.30},
    "loss_amount": {"method": "std", "k": (2, 3)},
    "repeat_rate": {"method": "percentile", "p": (90, 97.5)},
}

KRI_CATEGORY = {"payment_failure_rate": "Payment Errors", "outage_minutes": "System Outages"}

KRI_DEFINITIONS = [
    {"kri": "incidents_per_1000_tx",
     "definition": "Operational error events per 1,000 transactions",
     "calculation": "error events (Payment Errors, Data Entry Errors, Reconciliation Breaks, Process Breaches) / transactions x 1000",
     "data_source": "incidents.csv, monthly_volume.csv", "frequency": "Monthly",
     "threshold_basis": "Baseline mean + 2 SD (amber) and + 3 SD (red), per business unit, first 12 months",
     "action": "Review top root causes of the unit and open a control improvement ticket"},
    {"kri": "payment_failure_rate",
     "definition": "Share of payments that failed because of operational incidents",
     "calculation": "failed payments / total payments",
     "data_source": "incidents.csv, monthly_volume.csv", "frequency": "Monthly",
     "threshold_basis": "Assumed service level: 0.30% amber, 0.50% red",
     "action": "Start a root cause review of the payment flow and notify the payments operations lead"},
    {"kri": "outage_minutes",
     "definition": "Total system downtime minutes per month",
     "calculation": "sum of downtime minutes of System Outages incidents",
     "data_source": "incidents.csv", "frequency": "Monthly",
     "threshold_basis": "Assumed 99.9% availability SLA = 43.2 min per month; amber at 80%, red at 100%",
     "action": "Run a post-incident review, verify failover and capacity, report SLA breach to management"},
    {"kri": "open_actions",
     "definition": "Corrective actions still open at month end",
     "calculation": "count of actions opened on or before month end and not closed by month end",
     "data_source": "corrective_actions.csv", "frequency": "Monthly",
     "threshold_basis": "Baseline P90 (amber) and P97.5 (red), per business unit",
     "action": "Review the backlog with action owners and reprioritise resources"},
    {"kri": "overdue_action_rate",
     "definition": "Share of open corrective actions past their due date",
     "calculation": "overdue open actions / open actions (n/m if fewer than 5 open)",
     "data_source": "corrective_actions.csv", "frequency": "Monthly",
     "threshold_basis": "Management assumption: 15% amber, 30% red",
     "action": "Escalate overdue actions to the unit head and agree revised dates"},
    {"kri": "loss_amount",
     "definition": "Total realised operational loss per month (TRY)",
     "calculation": "sum of loss_amount",
     "data_source": "incidents.csv", "frequency": "Monthly",
     "threshold_basis": "Baseline mean + 2 SD (amber) and + 3 SD (red), per business unit",
     "action": "Review the largest loss events and assess control failures"},
    {"kri": "repeat_rate",
     "definition": "Share of incidents repeating the same root cause in the same unit within 90 days",
     "calculation": "repeat incidents / incidents (n/m if fewer than 5 incidents)",
     "data_source": "incidents.csv", "frequency": "Monthly",
     "threshold_basis": "Baseline P90 (amber) and P97.5 (red), per business unit",
     "action": "Prioritise a permanent fix for repeated root causes and verify closed actions were effective"},
]
KRI_ACTIONS = {d["kri"]: d["action"] for d in KRI_DEFINITIONS}

MATRIX_WINDOW_MONTHS = 12
LIKELIHOOD_BANDS = [5, 10, 15, 20]  # mean incidents per month
IMPACT_BANDS = [20_000, 50_000, 120_000, 300_000]  # 95th percentile loss per incident (TRY)
RATING_BANDS = [(4, "Low"), (9, "Medium"), (14, "High")]


def score_rating(score):
    for limit, name in RATING_BANDS:
        if score <= limit:
            return name
    return "Critical"