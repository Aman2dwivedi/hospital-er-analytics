-- =============================================================================
-- Hospital ER Flow & Resource Utilization - Advanced Operational Analytics
-- Author: Aman Dwivedi
-- Purpose: Executive KPIs, queueing bottlenecks, physician efficiency, 
--          and clinical quality insights.
-- =============================================================================

-- =============================================================================
-- QUERY 1: Executive KPI Scorecard by Triage Acuity (ESI 1 to 5)
-- Business Context: Evaluate patient volume, average wait time, LOS, and SLA compliance.
-- =============================================================================
SELECT 
    triage_acuity_esi,
    triage_level_name,
    COUNT(*) AS total_patients,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS volume_share_pct,
    ROUND(AVG(wait_time_minutes), 1) AS avg_wait_time_mins,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY wait_time_minutes), 1) AS p90_wait_time_mins,
    ROUND(AVG(total_los_hours), 2) AS avg_los_hours,
    ROUND(AVG(sla_wait_time_compliant) * 100.0, 1) AS sla_compliance_pct,
    ROUND(AVG(CASE WHEN disposition LIKE 'Admitted%' THEN 1.0 ELSE 0.0 END) * 100.0, 1) AS admission_rate_pct,
    ROUND(AVG(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN 1.0 ELSE 0.0 END) * 100.0, 2) AS lwbs_rate_pct,
    ROUND(AVG(patient_satisfaction_score), 2) AS avg_satisfaction_score,
    ROUND(SUM(total_cost_usd), 2) AS total_department_revenue_usd
FROM er_patient_visits
GROUP BY triage_acuity_esi, triage_level_name
ORDER BY triage_acuity_esi ASC;


-- =============================================================================
-- QUERY 2: Diurnal Hourly Demand vs Bed Occupancy & Bottleneck Analysis
-- Business Context: Pinpoint exact hours where patient arrivals overwhelm ER capacity.
-- =============================================================================
SELECT 
    arrival_hour,
    COUNT(*) AS total_arrivals,
    ROUND(AVG(bed_occupancy_rate_pct), 1) AS avg_bed_occupancy_pct,
    ROUND(AVG(wait_time_minutes), 1) AS avg_wait_mins,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY wait_time_minutes), 1) AS p90_wait_mins,
    SUM(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN 1 ELSE 0 END) AS total_lwbs_patients,
    ROUND(AVG(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN 1.0 ELSE 0.0 END) * 100.0, 2) AS lwbs_rate_pct,
    CASE 
        WHEN AVG(bed_occupancy_rate_pct) >= 85.0 THEN 'CRITICAL CONGESTION'
        WHEN AVG(bed_occupancy_rate_pct) >= 75.0 THEN 'MODERATE STRAIN'
        ELSE 'OPTIMAL FLOW'
    END AS er_operational_status
FROM er_patient_visits
GROUP BY arrival_hour
ORDER BY arrival_hour ASC;


-- =============================================================================
-- QUERY 3: Left Without Being Seen (LWBS) Root-Cause & Financial Opportunity Loss
-- Business Context: Calculate estimated revenue loss and wait-time triggers for walkouts.
-- =============================================================================
WITH lwbs_summary AS (
    SELECT 
        chief_complaint,
        triage_level_name,
        COUNT(*) AS total_visits,
        SUM(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN 1 ELSE 0 END) AS lwbs_cases,
        ROUND(AVG(wait_time_minutes), 1) AS avg_wait_time,
        ROUND(AVG(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN wait_time_minutes ELSE NULL END), 1) AS avg_wait_before_leaving,
        -- Opportunity loss: estimated average billing fee lost per patient walkout
        ROUND(SUM(CASE WHEN disposition = 'Left Without Being Seen (LWBS)' THEN 1250.0 ELSE 0 END), 2) AS estimated_lost_revenue_usd
    FROM er_patient_visits
    GROUP BY chief_complaint, triage_level_name
)
SELECT 
    chief_complaint,
    triage_level_name,
    total_visits,
    lwbs_cases,
    ROUND(lwbs_cases * 100.0 / NULLIF(total_visits, 0), 2) AS lwbs_rate_pct,
    avg_wait_time,
    avg_wait_before_leaving,
    estimated_lost_revenue_usd
FROM lwbs_summary
WHERE lwbs_cases > 0
ORDER BY estimated_lost_revenue_usd DESC;


-- =============================================================================
-- QUERY 4: Physician Efficiency & Patient Throughput Benchmark
-- Business Context: Compare doctor workload, treatment duration, and readmission rates.
-- =============================================================================
SELECT 
    attending_doctor,
    COUNT(*) AS total_patients_treated,
    ROUND(AVG(treatment_time_minutes), 1) AS avg_treatment_time_mins,
    ROUND(AVG(total_los_hours), 2) AS avg_los_hours,
    ROUND(AVG(readmission_30d) * 100.0, 2) AS readmission_30d_rate_pct,
    ROUND(AVG(patient_satisfaction_score), 2) AS avg_satisfaction_score,
    ROUND(SUM(total_cost_usd), 2) AS total_revenue_generated_usd,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS throughput_rank,
    DENSE_RANK() OVER (ORDER BY AVG(patient_satisfaction_score) DESC) AS satisfaction_rank
FROM er_patient_visits
WHERE disposition != 'Left Without Being Seen (LWBS)'
GROUP BY attending_doctor
ORDER BY total_patients_treated DESC;


-- =============================================================================
-- QUERY 5: Inpatient Bed Allocation & Boarding Length of Stay (LOS)
-- Business Context: Analyze which hospital departments receive the highest ER volume.
-- =============================================================================
SELECT 
    admitted_department,
    COUNT(*) AS total_admissions,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total_admissions,
    ROUND(AVG(total_los_hours), 2) AS avg_er_los_hours,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_los_hours), 2) AS p95_er_los_hours,
    ROUND(AVG(total_cost_usd), 2) AS avg_encounter_cost_usd,
    ROUND(SUM(total_cost_usd), 2) AS total_department_cost_usd
FROM er_patient_visits
WHERE admitted_department != 'None (Outpatient Discharge)'
GROUP BY admitted_department
ORDER BY total_admissions DESC;


-- =============================================================================
-- QUERY 6: 30-Day Readmission Risk Matrix by Age Cohort & Triage Level
-- Business Context: Identify vulnerable patient groups for post-discharge follow-up.
-- =============================================================================
SELECT 
    age_group,
    triage_level_name,
    COUNT(*) AS total_encounters,
    SUM(readmission_30d) AS readmitted_patients,
    ROUND(AVG(readmission_30d) * 100.0, 2) AS readmission_rate_pct,
    ROUND(AVG(total_cost_usd), 2) AS avg_visit_cost_usd
FROM er_patient_visits
WHERE disposition NOT IN ('Expired / Deceased', 'Left Without Being Seen (LWBS)')
GROUP BY age_group, triage_level_name
ORDER BY readmission_rate_pct DESC;


-- =============================================================================
-- QUERY 7: 7-Day Rolling Moving Average for ER Volume & Operational Strain
-- Business Context: Smooth daily volume swings to observe macro seasonal surges.
-- =============================================================================
WITH daily_agg AS (
    SELECT 
        arrival_date,
        COUNT(*) AS daily_visits,
        AVG(wait_time_minutes) AS daily_avg_wait_mins,
        AVG(bed_occupancy_rate_pct) AS daily_avg_bed_occupancy
    FROM er_patient_visits
    GROUP BY arrival_date
)
SELECT 
    arrival_date,
    daily_visits,
    ROUND(AVG(daily_visits) OVER (
        ORDER BY arrival_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_7day_avg_visits,
    ROUND(daily_avg_wait_mins, 1) AS daily_avg_wait_mins,
    ROUND(AVG(daily_avg_wait_mins) OVER (
        ORDER BY arrival_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_7day_avg_wait_mins,
    ROUND(daily_avg_bed_occupancy, 1) AS daily_avg_bed_occupancy
FROM daily_agg
ORDER BY arrival_date ASC;

-- Analysis Created and Curated by Aman Dwivedi.
