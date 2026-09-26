-- =============================================================================
-- Hospital ER Flow & Resource Utilization - Database Schema Definition
-- Author: Aman Dwivedi
-- Dialect: ANSI SQL / PostgreSQL / DuckDB / SQLite compatible
-- =============================================================================

CREATE TABLE IF NOT EXISTS er_patient_visits (
    patient_id VARCHAR(20) PRIMARY KEY,
    arrival_timestamp TIMESTAMP NOT NULL,
    departure_timestamp TIMESTAMP NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_hour INT NOT NULL CHECK (arrival_hour BETWEEN 0 AND 23),
    arrival_day_name VARCHAR(15) NOT NULL,
    arrival_month VARCHAR(15) NOT NULL,
    age INT NOT NULL CHECK (age >= 0),
    age_group VARCHAR(15) NOT NULL,
    gender VARCHAR(15) NOT NULL,
    chief_complaint VARCHAR(100) NOT NULL,
    triage_acuity_esi INT NOT NULL CHECK (triage_acuity_esi BETWEEN 1 AND 5),
    triage_level_name VARCHAR(50) NOT NULL,
    arrival_mode VARCHAR(50) NOT NULL,
    initial_pain_score INT CHECK (initial_pain_score BETWEEN 0 AND 10),
    door_to_triage_minutes INT NOT NULL,
    wait_time_minutes INT NOT NULL,
    treatment_time_minutes INT NOT NULL,
    total_los_minutes INT NOT NULL,
    total_los_hours DECIMAL(6, 2) NOT NULL,
    bed_occupancy_rate_pct DECIMAL(5, 2) NOT NULL,
    sla_wait_time_compliant INT NOT NULL CHECK (sla_wait_time_compliant IN (0, 1)),
    disposition VARCHAR(100) NOT NULL,
    admitted_department VARCHAR(100) NOT NULL,
    attending_doctor VARCHAR(100) NOT NULL,
    lab_ordered INT NOT NULL CHECK (lab_ordered IN (0, 1)),
    imaging_ordered VARCHAR(50) NOT NULL,
    insurance_type VARCHAR(50) NOT NULL,
    total_cost_usd DECIMAL(10, 2) NOT NULL,
    readmission_30d INT NOT NULL CHECK (readmission_30d IN (0, 1)),
    patient_satisfaction_score INT NOT NULL CHECK (patient_satisfaction_score BETWEEN 1 AND 5),
    is_weekend INT NOT NULL CHECK (is_weekend IN (0, 1)),
    shift_period VARCHAR(50) NOT NULL,
    is_peak_hour INT NOT NULL CHECK (is_peak_hour IN (0, 1)),
    bottleneck_risk_level VARCHAR(50) NOT NULL,
    los_category VARCHAR(50) NOT NULL
);

-- Recommended Indices for High-Throughput Analytics
CREATE INDEX idx_er_arrival ON er_patient_visits (arrival_timestamp);
CREATE INDEX idx_er_triage ON er_patient_visits (triage_acuity_esi);
CREATE INDEX idx_er_disposition ON er_patient_visits (disposition);
CREATE INDEX idx_er_doctor ON er_patient_visits (attending_doctor);
