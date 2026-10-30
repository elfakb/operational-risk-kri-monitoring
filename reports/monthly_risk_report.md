# Monthly Operational Risk Report: 2024-12

All figures are based on synthetic data.

## 1. Headline
| Metric | 2024-12 | 2024-11 | 12m avg | vs 12m avg |
|---|---|---|---|---|
| Incidents | 126 | 117 | 120 | +5% |
| Realised loss (TRY) | 684,030 | 577,897 | 1,304,202 | -48% |
| Outage minutes | 65 | 88 | 108 | -40% |

## 2. KRI status
6 red, 8 amber and 0 watch signals among 35 unit-KRI combinations.

| Business unit | KRI | Status | Value | Amber threshold |
|---|---|---|---|---|
| Operations | open_actions | red | 25.00 | 10.00 |
| Payments | open_actions | red | 37.00 | 25.00 |
| Retail Banking | open_actions | red | 16.00 | 14.90 |
| Treasury | loss_amount | red | 178,614.51 | 59,588.29 |
| Treasury | open_actions | red | 8.00 | 4.90 |
| Treasury | repeat_rate | red | 35.29% | 17.67% |
| Operations | incidents_per_1000_tx | amber | 1.17 | 1.14 |
| Operations | overdue_action_rate | amber | 28.00% | 15.00% |
| Payments | overdue_action_rate | amber | 18.92% | 15.00% |
| Payments | payment_failure_rate | amber | 0.34% | 0.30% |
| Payments | repeat_rate | amber | 47.37% | 42.52% |
| Retail Banking | outage_minutes | amber | 38.40 | 34.56 |
| Retail Banking | overdue_action_rate | amber | 25.00% | 15.00% |
| Treasury | incidents_per_1000_tx | amber | 4.52 | 3.72 |

## 3. Active alerts
| alert_id | business_unit | kri | risk_category | level | start_month | months_active | recurring |
|---|---|---|---|---|---|---|---|
| AL-0037 | Operations | open_actions | Data Entry Errors | red | 2023-08 | 17 | 0 |
| AL-0081 | Operations | overdue_action_rate | Data Entry Errors | red | 2024-06 | 7 | 1 |
| AL-0096 | Payments | open_actions | Payment Errors | red | 2024-09 | 4 | 1 |
| AL-0090 | Retail Banking | open_actions | Payment Errors | red | 2024-08 | 5 | 1 |
| AL-0104 | Retail Banking | outage_minutes | System Outages | red | 2024-11 | 2 | 1 |
| AL-0094 | Treasury | open_actions | Reconciliation Breaks | red | 2024-08 | 5 | 1 |
| AL-0106 | Treasury | repeat_rate | Reconciliation Breaks | red | 2024-11 | 2 | 1 |
| AL-0109 | Treasury | loss_amount | Unauthorized Transaction Attempts | red | 2024-12 | 1 | 1 |
| AL-0107 | Operations | incidents_per_1000_tx | Data Entry Errors | amber | 2024-12 | 1 | 1 |
| AL-0101 | Payments | overdue_action_rate | Payment Errors | amber | 2024-11 | 2 | 1 |
| AL-0102 | Payments | payment_failure_rate | Payment Errors | amber | 2024-11 | 2 | 1 |
| AL-0103 | Payments | repeat_rate | Payment Errors | amber | 2024-11 | 2 | 1 |
| AL-0105 | Retail Banking | overdue_action_rate | Payment Errors | amber | 2024-11 | 2 | 1 |
| AL-0108 | Treasury | incidents_per_1000_tx | Reconciliation Breaks | amber | 2024-12 | 1 | 1 |

## 4. Corrective actions
19 open actions are past their due date.

| business_unit | overdue_actions | avg_days_overdue |
|---|---|---|
| Corporate Banking | 1 | 280.0 |
| Operations | 7 | 56.0 |
| Payments | 7 | 293.0 |
| Retail Banking | 4 | 281.0 |

Oldest overdue actions:

| action_id | business_unit | severity | risk_category | days_overdue |
|---|---|---|---|---|
| CA-000346 | Payments | Low | Data Entry Errors | 696 |
| CA-000481 | Payments | Medium | Payment Errors | 625 |
| CA-000541 | Retail Banking | Medium | Payment Errors | 575 |
| CA-000613 | Payments | Critical | System Outages | 546 |
| CA-000730 | Retail Banking | Medium | Payment Errors | 418 |
| CA-000935 | Corporate Banking | Low | Reconciliation Breaks | 280 |
| CA-001089 | Operations | Low | Data Entry Errors | 180 |
| CA-001280 | Payments | Medium | System Outages | 110 |
| CA-001269 | Retail Banking | Low | Payment Errors | 88 |
| CA-001346 | Operations | Medium | Data Entry Errors | 64 |

## 5. Risk matrix, top priorities
Matrix window: 2024-01 to 2024-12.

| priority_rank | risk_category | likelihood | impact | score | rating | total_loss | alerts_in_window |
|---|---|---|---|---|---|---|---|
| 1 | Unauthorized Transaction Attempts | 2 | 5 | 10 | High | 6979804.0 | 5 |
| 2 | Payment Errors | 5 | 2 | 10 | High | 2686140.0 | 15 |
| 3 | Reconciliation Breaks | 5 | 2 | 10 | High | 1594476.0 | 8 |

## 6. Recommended actions
| priority | business_unit | trigger | recommended_action | target_days |
|---|---|---|---|---|
| P1 | Operations | open_actions (red) | Review the backlog with action owners and reprioritise resources | 14 |
| P1 | Operations | overdue_action_rate (red) | Escalate overdue actions to the unit head and agree revised dates | 14 |
| P1 | Payments | open_actions (red) | Review the backlog with action owners and reprioritise resources | 14 |
| P1 | Retail Banking | open_actions (red) | Review the backlog with action owners and reprioritise resources | 14 |
| P1 | Retail Banking | outage_minutes (red) | Run a post-incident review, verify failover and capacity, report SLA breach to management | 14 |
| P1 | Treasury | open_actions (red) | Review the backlog with action owners and reprioritise resources | 14 |
| P1 | Treasury | repeat_rate (red) | Prioritise a permanent fix for repeated root causes and verify closed actions were effective | 14 |
| P1 | Treasury | loss_amount (red) | Review the largest loss events and assess control failures | 14 |
| P2 | All | risk matrix (High) | Review the control framework for Unauthorized Transaction Attempts and agree mitigation owners | 30 |
| P2 | All | risk matrix (High) | Review the control framework for Payment Errors and agree mitigation owners | 30 |
| P2 | All | risk matrix (High) | Review the control framework for Reconciliation Breaks and agree mitigation owners | 30 |
| P2 | Operations | incidents_per_1000_tx (amber) | Review top root causes of the unit and open a control improvement ticket | 30 |
| P2 | Payments | overdue_action_rate (amber) | Escalate overdue actions to the unit head and agree revised dates | 30 |
| P2 | Payments | payment_failure_rate (amber) | Start a root cause review of the payment flow and notify the payments operations lead | 30 |
| P2 | Payments | repeat_rate (amber) | Prioritise a permanent fix for repeated root causes and verify closed actions were effective | 30 |
| P2 | Retail Banking | overdue_action_rate (amber) | Escalate overdue actions to the unit head and agree revised dates | 30 |
| P2 | Treasury | incidents_per_1000_tx (amber) | Review top root causes of the unit and open a control improvement ticket | 30 |
