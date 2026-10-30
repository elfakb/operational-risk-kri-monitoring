DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS monthly_volume;
DROP TABLE IF EXISTS corrective_actions;
DROP TABLE IF EXISTS kri_monthly;
DROP TABLE IF EXISTS kri_definitions;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS risk_matrix;

CREATE TABLE incidents (
    incident_id TEXT PRIMARY KEY,
    incident_date TEXT,
    month TEXT,
    risk_category TEXT,
    business_unit TEXT,
    description TEXT,
    loss_amount REAL,
    downtime_min REAL,
    failed_payments INTEGER,
    severity TEXT,
    root_cause_code TEXT,
    data_label TEXT,
    is_repeat INTEGER
);

CREATE TABLE monthly_volume (
    business_unit TEXT,
    month TEXT,
    transactions INTEGER,
    payments INTEGER,
    data_label TEXT,
    PRIMARY KEY (business_unit, month)
);

CREATE TABLE corrective_actions (
    action_id TEXT PRIMARY KEY,
    incident_id TEXT,
    opened_date TEXT,
    due_date TEXT,
    closed_date TEXT,
    status TEXT,
    data_label TEXT
);

CREATE TABLE kri_monthly (
    business_unit TEXT,
    month TEXT,
    month_no INTEGER,
    period TEXT,
    kri TEXT,
    value REAL,
    amber_threshold REAL,
    red_threshold REAL,
    status TEXT,
    trend_watch INTEGER,
    PRIMARY KEY (business_unit, kri, month)
);

CREATE TABLE kri_definitions (
    kri TEXT PRIMARY KEY,
    definition TEXT,
    calculation TEXT,
    data_source TEXT,
    frequency TEXT,
    threshold_basis TEXT,
    action TEXT
);

CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    business_unit TEXT,
    kri TEXT,
    risk_category TEXT,
    level TEXT,
    start_month TEXT,
    end_month TEXT,
    duration_months INTEGER,
    status TEXT,
    months_to_close REAL,
    recurring INTEGER,
    preceded_by_watch INTEGER,
    peak_value REAL,
    amber_threshold REAL
);

CREATE TABLE risk_matrix (
    risk_category TEXT PRIMARY KEY,
    window_start TEXT,
    window_end TEXT,
    mean_monthly_incidents REAL,
    total_loss REAL,
    mean_loss REAL,
    p95_loss REAL,
    loss_share_pct REAL,
    likelihood INTEGER,
    impact INTEGER,
    score INTEGER,
    rating TEXT,
    alerts_in_window INTEGER,
    priority_rank INTEGER
);