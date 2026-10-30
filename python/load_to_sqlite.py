import sqlite3

import pandas as pd

from config import *

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

if DB_PATH.exists():
    DB_PATH.unlink()

con = sqlite3.connect(DB_PATH)
con.executescript((SQL_DIR / "create_tables.sql").read_text())

sources = {
    "incidents": PROCESSED_DIR / "incidents_enriched.csv",
    "monthly_volume": RAW_DIR / "monthly_volume.csv",
    "corrective_actions": RAW_DIR / "corrective_actions.csv",
    "kri_monthly": PROCESSED_DIR / "kri_monthly.csv",
    "kri_definitions": PROCESSED_DIR / "kri_definitions.csv",
    "alerts": PROCESSED_DIR / "alerts.csv",
    "risk_matrix": PROCESSED_DIR / "risk_matrix.csv",
}
for table, path in sources.items():
    pd.read_csv(path).to_sql(table, con, if_exists="append", index=False)

text = (SQL_DIR / "analysis_queries.sql").read_text()
for block in [b for b in text.split("-- name:") if b.strip()]:
    name, _, query = block.partition("\n")
    print(f"\n=== {name.strip()} ===")
    print(pd.read_sql(query.strip().rstrip(";"), con).to_string(index=False))

con.close()