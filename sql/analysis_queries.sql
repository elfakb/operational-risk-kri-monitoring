-- name: loss_by_category
SELECT risk_category,
       COUNT(*) AS incidents,
       ROUND(SUM(loss_amount), 0) AS total_loss,
       ROUND(AVG(loss_amount), 0) AS avg_loss,
       ROUND(MAX(loss_amount), 0) AS max_loss,
       ROUND(100.0 * SUM(loss_amount) / (SELECT SUM(loss_amount) FROM incidents), 1) AS loss_share_pct
FROM incidents
GROUP BY risk_category
ORDER BY total_loss DESC;

-- name: incidents_by_unit_year
SELECT business_unit,
       SUBSTR(month, 1, 4) AS year,
       COUNT(*) AS incidents,
       ROUND(SUM(loss_amount), 0) AS total_loss
FROM incidents
GROUP BY business_unit, SUBSTR(month, 1, 4)
ORDER BY business_unit, year;

-- name: unit_yoy_change
WITH yearly AS (
    SELECT business_unit, SUBSTR(month, 1, 4) AS year, COUNT(*) AS incidents
    FROM incidents
    GROUP BY business_unit, SUBSTR(month, 1, 4)
)
SELECT business_unit, year, incidents,
       LAG(incidents) OVER w AS prev_year_incidents,
       ROUND(100.0 * (incidents - LAG(incidents) OVER w) / LAG(incidents) OVER w, 1) AS change_pct
FROM yearly
WINDOW w AS (PARTITION BY business_unit ORDER BY year)
ORDER BY business_unit, year;

-- name: rolling_3m_incidents
WITH m AS (
    SELECT business_unit, month, COUNT(*) AS incidents
    FROM incidents
    GROUP BY business_unit, month
)
SELECT business_unit, month, incidents,
       ROUND(AVG(incidents) OVER (PARTITION BY business_unit ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS rolling_3m_avg
FROM m
ORDER BY business_unit, month;

-- name: repeat_root_causes
SELECT business_unit, root_cause_code,
       COUNT(*) AS incidents,
       SUM(is_repeat) AS repeats,
       ROUND(SUM(loss_amount), 0) AS total_loss
FROM incidents
GROUP BY business_unit, root_cause_code
HAVING SUM(is_repeat) >= 5
ORDER BY repeats DESC
LIMIT 15;

-- name: repeat_flag_cross_check
WITH x AS (
    SELECT is_repeat,
           julianday(incident_date) - julianday(LAG(incident_date) OVER (PARTITION BY business_unit, root_cause_code ORDER BY incident_date, incident_id)) AS gap_days
    FROM incidents
)
SELECT SUM(is_repeat) AS python_repeats,
       SUM(CASE WHEN gap_days <= 90 THEN 1 ELSE 0 END) AS sql_repeats
FROM x;

-- name: overdue_actions_at_data_end
SELECT i.business_unit, i.severity,
       COUNT(*) AS overdue_actions,
       ROUND(AVG(julianday('2024-12-31') - julianday(a.due_date)), 0) AS avg_days_overdue
FROM corrective_actions a
JOIN incidents i ON i.incident_id = a.incident_id
WHERE a.status = 'Open' AND a.due_date < '2024-12-31'
GROUP BY i.business_unit, i.severity
ORDER BY overdue_actions DESC;

-- name: action_closure_performance
SELECT i.severity,
       COUNT(*) AS closed_actions,
       ROUND(AVG(julianday(a.closed_date) - julianday(a.opened_date)), 1) AS avg_days_to_close,
       ROUND(100.0 * SUM(CASE WHEN a.closed_date > a.due_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS closed_late_pct
FROM corrective_actions a
JOIN incidents i ON i.incident_id = a.incident_id
WHERE a.status = 'Closed'
GROUP BY i.severity;

-- name: kri_breach_months
SELECT business_unit, kri,
       SUM(CASE WHEN status = 'red' THEN 1 ELSE 0 END) AS red_months,
       SUM(CASE WHEN status = 'amber' THEN 1 ELSE 0 END) AS amber_months,
       SUM(trend_watch) AS watch_months
FROM kri_monthly
WHERE period = 'test'
GROUP BY business_unit, kri
HAVING red_months + amber_months > 0
ORDER BY red_months DESC, amber_months DESC;

-- name: alert_summary
SELECT level, status,
       COUNT(*) AS alerts,
       ROUND(AVG(duration_months), 1) AS avg_duration_months,
       SUM(recurring) AS recurring_alerts,
       SUM(preceded_by_watch) AS preceded_by_watch
FROM alerts
GROUP BY level, status
ORDER BY level, status;