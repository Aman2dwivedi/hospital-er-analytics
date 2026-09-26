"""
=============================================================================
Hospital ER Flow & Resource Utilization - Synthetic Data Generator
Author: Aman Dwivedi
Description: Generates realistic clinical & operational Emergency Department (ED)
             data with genuine temporal patterns, triage acuity distributions,
             operational bottlenecks, and financial/outcome metrics.
=============================================================================
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_hospital_er_dataset(num_records: int = 15000) -> pd.DataFrame:
    """
    Generate a high-fidelity synthetic Emergency Department dataset.
    
    Created by: Aman Dwivedi
    """
    print(f"Generating {num_records} hospital ER patient visit records...")

    start_date = datetime(2025, 1, 1, 0, 0, 0)
    records = []

    # Doctors and Staff
    doctors = [
        "Dr. David Evans (Trauma/Surg)",
        "Dr. Priya Patel (Internal Med)",
        "Dr. Marcus Miller (Cardiology)",
        "Dr. Sofia Rodriguez (Pediatrics)",
        "Dr. James Zhang (Emergency Med)",
        "Dr. Elena Goldberg (Neurology)",
        "Dr. Tariq Al-Mansoor (Emergency Med)",
        "Dr. Hannah Smith (Emergency Med)"
    ]

    complaints_pool = [
        ("Chest Pain", 0.14, [1, 2, 3]),
        ("Shortness of Breath", 0.13, [1, 2, 3]),
        ("Trauma / Fracture / MVA", 0.16, [1, 2, 3, 4]),
        ("Severe Abdominal Pain", 0.15, [2, 3, 4]),
        ("High Fever / Sepsis", 0.12, [2, 3, 4]),
        ("Headache / Neurological Alert", 0.10, [2, 3, 4]),
        ("Psychiatric / Crisis", 0.07, [2, 3, 4]),
        ("Minor Wound / Sprain / Rash", 0.13, [4, 5])
    ]
    complaints, complaint_weights, complaint_esi_map = zip(*complaints_pool)
    complaint_weights = np.array(complaint_weights) / sum(complaint_weights)

    insurance_types = ["Commercial / Private", "Medicare", "Medicaid", "Uninsured / Self-Pay"]
    insurance_weights = np.array([0.45, 0.28, 0.18, 0.09])
    insurance_weights = insurance_weights / insurance_weights.sum()

    # Generate records
    for i in range(1, num_records + 1):
        patient_id = f"PAT-{i:06d}"
        
        # Random arrival time across the year with realistic diurnal cycle
        day_offset = random.randint(0, 364)
        
        # Realistic diurnal probabilities (peaks at 11 AM and 7 PM, low at 4 AM)
        hour_weights = [
            0.015, 0.012, 0.010, 0.009, 0.011, 0.018, # 00-05
            0.028, 0.045, 0.062, 0.070, 0.075, 0.072, # 06-11
            0.068, 0.065, 0.062, 0.060, 0.064, 0.072, # 12-17
            0.078, 0.074, 0.058, 0.045, 0.030, 0.019  # 18-23
        ]
        hour_weights = np.array(hour_weights) / sum(hour_weights)
        hour = np.random.choice(range(24), p=hour_weights)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        arrival_time = start_date + timedelta(days=day_offset, hours=int(hour), minutes=minute, seconds=second)

        # Age distribution
        age = int(np.clip(np.random.normal(loc=46, scale=22), 1, 96))
        gender = random.choices(["Female", "Male", "Non-Binary"], weights=[0.51, 0.48, 0.01])[0]

        # Chief Complaint
        chief_complaint = random.choices(complaints, weights=complaint_weights)[0]
        matching_complaint_info = [c for c in complaints_pool if c[0] == chief_complaint][0]
        possible_esi = matching_complaint_info[2]

        # Triage Acuity (Emergency Severity Index: 1=Resuscitation to 5=Non-Urgent)
        if 1 in possible_esi and (age > 70 or chief_complaint in ["Chest Pain", "Trauma / Fracture / MVA"]):
            esi_probs = [0.08, 0.35, 0.42, 0.12, 0.03][:len(possible_esi)]
            triage_acuity = random.choices(possible_esi, weights=esi_probs)[0]
        else:
            triage_acuity = random.choice(possible_esi)

        # Arrival Mode
        if triage_acuity == 1:
            arrival_mode = random.choices(["Ambulance", "Helicopter / Transfer", "Walk-in"], weights=[0.75, 0.20, 0.05])[0]
        elif triage_acuity == 2:
            arrival_mode = random.choices(["Ambulance", "Walk-in", "Helicopter / Transfer"], weights=[0.55, 0.40, 0.05])[0]
        else:
            arrival_mode = random.choices(["Walk-in", "Ambulance"], weights=[0.85, 0.15])[0]

        # Initial Pain Score (0 - 10)
        if triage_acuity in [1, 2]:
            pain_score = int(np.clip(np.random.normal(8.2, 1.5), 4, 10))
        elif triage_acuity == 3:
            pain_score = int(np.clip(np.random.normal(6.5, 2.0), 1, 10))
        else:
            pain_score = int(np.clip(np.random.normal(3.5, 2.2), 0, 8))

        # Bed Occupancy at time of arrival (Simulated bottleneck: peak hours have 85-98% occupancy)
        if 10 <= hour <= 21:
            bed_occupancy_pct = round(float(np.clip(np.random.normal(88.5, 6.0), 65.0, 99.5)), 1)
        else:
            bed_occupancy_pct = round(float(np.clip(np.random.normal(71.0, 8.5), 45.0, 90.0)), 1)

        # Operational Times: Door-to-Triage & Door-to-Doctor (Wait Time)
        door_to_triage_mins = int(np.clip(np.random.gamma(shape=2.5, scale=2.5), 2, 25))
        
        # Wait time depends heavily on ESI acuity and ER Bed/Staff Occupancy
        load_multiplier = 1.0 + (bed_occupancy_pct - 70.0) / 50.0 if bed_occupancy_pct > 70 else 1.0
        
        if triage_acuity == 1:
            # Resuscitation - immediate attention
            wait_time_minutes = int(np.clip(np.random.exponential(scale=2.0), 0, 8))
        elif triage_acuity == 2:
            # Emergent - target < 15-20 mins
            wait_time_minutes = int(np.clip(np.random.normal(14.0 * load_multiplier, 5.0), 3, 45))
        elif triage_acuity == 3:
            # Urgent - target < 45-60 mins, but often faces bottlenecks
            wait_time_minutes = int(np.clip(np.random.normal(52.0 * load_multiplier, 22.0), 10, 180))
        elif triage_acuity == 4:
            # Less Urgent
            wait_time_minutes = int(np.clip(np.random.normal(95.0 * load_multiplier, 35.0), 20, 260))
        else:
            # Non-Urgent
            wait_time_minutes = int(np.clip(np.random.normal(120.0 * load_multiplier, 45.0), 25, 320))

        # Left Without Being Seen (LWBS) probability increases with long wait times (mostly ESI 4 & 5)
        lwbs = False
        if triage_acuity >= 4 and wait_time_minutes > 90 and random.random() < 0.18:
            lwbs = True
        elif triage_acuity == 3 and wait_time_minutes > 140 and random.random() < 0.05:
            lwbs = True

        # Treatment Time & Total Length of Stay (LOS)
        if lwbs:
            treatment_time_minutes = 0
            total_los_minutes = wait_time_minutes
            disposition = "Left Without Being Seen (LWBS)"
            admitted_department = "None"
            readmission_30d = 0
            patient_satisfaction = random.choice([1, 2])
        else:
            # Clinical Treatment Time
            if triage_acuity == 1:
                treatment_time_minutes = int(np.clip(np.random.normal(210, 60), 60, 480))
            elif triage_acuity == 2:
                treatment_time_minutes = int(np.clip(np.random.normal(175, 50), 45, 360))
            elif triage_acuity == 3:
                treatment_time_minutes = int(np.clip(np.random.normal(130, 40), 30, 280))
            else:
                treatment_time_minutes = int(np.clip(np.random.normal(65, 25), 15, 180))

            total_los_minutes = wait_time_minutes + treatment_time_minutes

            # Disposition Decision
            if triage_acuity == 1:
                disp_choices = ["Admitted - ICU", "Admitted - General Ward", "Expired / Deceased", "Transferred to Specialist"]
                disposition = random.choices(disp_choices, weights=[0.68, 0.18, 0.09, 0.05])[0]
            elif triage_acuity == 2:
                disp_choices = ["Admitted - General Ward", "Admitted - ICU", "Admitted - Cardiology", "Discharged Home", "Transferred to Specialist"]
                disposition = random.choices(disp_choices, weights=[0.45, 0.20, 0.15, 0.16, 0.04])[0]
            elif triage_acuity == 3:
                disp_choices = ["Discharged Home", "Admitted - General Ward", "Admitted - Orthopedics", "Admitted - Cardiology"]
                disposition = random.choices(disp_choices, weights=[0.65, 0.22, 0.08, 0.05])[0]
            else:
                disp_choices = ["Discharged Home", "Admitted - General Ward"]
                disposition = random.choices(disp_choices, weights=[0.94, 0.06])[0]

            # Department Assignment
            if "ICU" in disposition:
                admitted_department = "Intensive Care Unit (ICU)"
            elif "Cardiology" in disposition:
                admitted_department = "Cardiology Wing"
            elif "Orthopedics" in disposition:
                admitted_department = "Orthopedics / Trauma"
            elif "General Ward" in disposition:
                admitted_department = "General Medical Ward"
            elif "Transferred" in disposition:
                admitted_department = "External Transfer"
            else:
                admitted_department = "None (Outpatient Discharge)"

            # 30-Day Readmission Risk
            if disposition == "Expired / Deceased":
                readmission_30d = 0
            else:
                base_readmit_prob = 0.05
                if age > 65: base_readmit_prob += 0.08
                if triage_acuity in [1, 2]: base_readmit_prob += 0.09
                if "Admitted" in disposition: base_readmit_prob += 0.06
                readmission_30d = 1 if random.random() < base_readmit_prob else 0

            # Patient Satisfaction (1-5 Stars)
            if wait_time_minutes < 30:
                sat_probs = [0.02, 0.05, 0.10, 0.35, 0.48]
            elif wait_time_minutes < 75:
                sat_probs = [0.05, 0.12, 0.28, 0.38, 0.17]
            elif wait_time_minutes < 150:
                sat_probs = [0.22, 0.38, 0.25, 0.12, 0.03]
            else:
                sat_probs = [0.55, 0.30, 0.10, 0.04, 0.01]
            patient_satisfaction = random.choices([1, 2, 3, 4, 5], weights=sat_probs)[0]

        # Attending Staff
        attending_doctor = random.choice(doctors)

        # Diagnostics & Imaging
        if triage_acuity in [1, 2] and not lwbs:
            lab_ordered = 1
            imaging_ordered = random.choices(["CT Scan", "X-Ray", "MRI", "Ultrasound", "None"], weights=[0.42, 0.30, 0.12, 0.10, 0.06])[0]
        elif triage_acuity == 3 and not lwbs:
            lab_ordered = random.choices([1, 0], weights=[0.75, 0.25])[0]
            imaging_ordered = random.choices(["X-Ray", "CT Scan", "Ultrasound", "None"], weights=[0.45, 0.25, 0.15, 0.15])[0]
        else:
            lab_ordered = random.choices([1, 0], weights=[0.25, 0.75])[0]
            imaging_ordered = random.choices(["None", "X-Ray"], weights=[0.78, 0.22])[0]

        # Insurance Type
        if age >= 65:
            insurance_type = random.choices(["Medicare", "Commercial / Private"], weights=[0.82, 0.18])[0]
        else:
            insurance_type = random.choices(insurance_types, weights=insurance_weights)[0]

        # Financial Billing Calculation
        base_charge = 450.0
        acuity_fee = {1: 4200.0, 2: 2800.0, 3: 1400.0, 4: 650.0, 5: 350.0}[triage_acuity]
        lab_fee = 380.0 if lab_ordered else 0.0
        imaging_fee = {"None": 0.0, "X-Ray": 280.0, "Ultrasound": 450.0, "CT Scan": 1650.0, "MRI": 2400.0}[imaging_ordered]
        los_hourly_fee = (total_los_minutes / 60.0) * 120.0
        
        if lwbs:
            total_bill_usd = round(150.0 + random.uniform(20.0, 80.0), 2)
        else:
            noise = random.uniform(0.90, 1.15)
            total_bill_usd = round((base_charge + acuity_fee + lab_fee + imaging_fee + los_hourly_fee) * noise, 2)

        # Target Wait Time Compliance Flag (Emergency Standard: ESI 1=0m, ESI 2<=15m, ESI 3<=60m, ESI 4<=120m, ESI 5<=120m)
        sla_thresholds = {1: 2, 2: 15, 3: 60, 4: 120, 5: 120}
        sla_compliant = 1 if wait_time_minutes <= sla_thresholds[triage_acuity] and not lwbs else 0

        # Departure timestamp
        departure_time = arrival_time + timedelta(minutes=total_los_minutes)

        records.append({
            "patient_id": patient_id,
            "arrival_timestamp": arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            "departure_timestamp": departure_time.strftime("%Y-%m-%d %H:%M:%S"),
            "arrival_date": arrival_time.strftime("%Y-%m-%d"),
            "arrival_hour": arrival_time.hour,
            "arrival_day_name": arrival_time.strftime("%A"),
            "arrival_month": arrival_time.strftime("%B"),
            "age": age,
            "age_group": "<18" if age < 18 else ("18-39" if age <= 39 else ("40-64" if age <= 64 else "65+")),
            "gender": gender,
            "chief_complaint": chief_complaint,
            "triage_acuity_esi": triage_acuity,
            "triage_level_name": {
                1: "ESI 1 - Resuscitation",
                2: "ESI 2 - Emergent",
                3: "ESI 3 - Urgent",
                4: "ESI 4 - Less Urgent",
                5: "ESI 5 - Non-Urgent"
            }[triage_acuity],
            "arrival_mode": arrival_mode,
            "initial_pain_score": pain_score,
            "door_to_triage_minutes": door_to_triage_mins,
            "wait_time_minutes": wait_time_minutes,
            "treatment_time_minutes": treatment_time_minutes,
            "total_los_minutes": total_los_minutes,
            "total_los_hours": round(total_los_minutes / 60.0, 2),
            "bed_occupancy_rate_pct": bed_occupancy_pct,
            "sla_wait_time_compliant": sla_compliant,
            "disposition": disposition,
            "admitted_department": admitted_department,
            "attending_doctor": attending_doctor,
            "lab_ordered": lab_ordered,
            "imaging_ordered": imaging_ordered,
            "insurance_type": insurance_type,
            "total_cost_usd": total_bill_usd,
            "readmission_30d": readmission_30d,
            "patient_satisfaction_score": patient_satisfaction
        })

    df = pd.DataFrame(records)
    print(f"Dataset generated successfully with {len(df):,} records and {len(df.columns)} features.")
    return df


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    target_path = os.path.join(output_dir, "hospital_er_admissions.csv")
    
    df = generate_hospital_er_dataset(num_records=15000)
    df.to_csv(target_path, index=False)
    print(f"Saved dataset to: {target_path}")
    print("Hospital ER Data Generation Completed by Aman Dwivedi.")
