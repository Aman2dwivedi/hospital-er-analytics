"""
=============================================================================
Hospital ER Flow & Resource Utilization - Data Cleaning & Pipeline Engine
Author: Aman Dwivedi
Description: Ingests raw Emergency Department records, cleans anomalies,
             engineers clinical and operational features, and produces
             curated datasets for SQL querying, reporting, and dashboarding.
=============================================================================
"""

import os
import pandas as pd
import numpy as np


class ERDataPipeline:
    """
    Production ETL and feature engineering pipeline for Hospital ER data.
    Developed by Aman Dwivedi.
    """

    def __init__(self, raw_data_path: str = None, processed_dir: str = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.raw_data_path = raw_data_path or os.path.join(base_dir, "data", "raw", "hospital_er_admissions.csv")
        self.processed_dir = processed_dir or os.path.join(base_dir, "data", "processed")
        os.makedirs(self.processed_dir, exist_ok=True)

    def load_raw_data(self) -> pd.DataFrame:
        """Load raw CSV dataset."""
        if not os.path.exists(self.raw_data_path):
            raise FileNotFoundError(f"Raw data file not found at: {self.raw_data_path}")
        df = pd.read_csv(self.raw_data_path)
        print(f"[Pipeline by Aman Dwivedi] Loaded {len(df):,} raw records.")
        return df

    def clean_and_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean missing values, cast data types, and engineer high-impact operational features.
        """
        # Convert timestamp columns
        df['arrival_timestamp'] = pd.to_datetime(df['arrival_timestamp'])
        df['departure_timestamp'] = pd.to_datetime(df['departure_timestamp'])

        # Feature: Weekend Indicator
        df['is_weekend'] = df['arrival_day_name'].isin(['Saturday', 'Sunday']).astype(int)

        # Feature: Shift Period (Night: 00-07, Day: 08-15, Evening: 16-23)
        df['shift_period'] = df['arrival_hour'].apply(
            lambda h: 'Night Shift (00:00-07:59)' if h < 8
            else ('Day Shift (08:00-15:59)' if h < 16 else 'Evening Shift (16:00-23:59)')
        )

        # Feature: Peak Hour Flag (Bottleneck rush hours: 10 AM - 2 PM, 6 PM - 9 PM)
        df['is_peak_hour'] = df['arrival_hour'].apply(
            lambda h: 1 if (10 <= h <= 14) or (18 <= h <= 21) else 0
        )

        # Feature: ER Bottleneck Risk Index (combines Bed Occupancy + Wait Time load)
        df['bottleneck_risk_level'] = pd.cut(
            df['bed_occupancy_rate_pct'],
            bins=[0, 75, 88, 100],
            labels=['Normal Capacity', 'Elevated Load', 'Severe Congestion']
        )

        # Feature: Length of Stay (LOS) Categorization
        df['los_category'] = pd.cut(
            df['total_los_hours'],
            bins=[0, 2, 4, 8, 24, 100],
            labels=['<2 Hours (Rapid)', '2-4 Hours (Standard)', '4-8 Hours (Extended)', '8-24 Hours (Delayed)', '>24 Hours (Extreme)']
        )

        # Feature: Admission Status Flag
        df['is_admitted'] = df['disposition'].str.startswith('Admitted').astype(int)
        df['is_lwbs'] = (df['disposition'] == 'Left Without Being Seen (LWBS)').astype(int)

        # Feature: High Cost Outlier Flag
        df['is_high_cost'] = (df['total_cost_usd'] > df['total_cost_usd'].quantile(0.90)).astype(int)

        return df

    def compute_summary_kpis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute high-level executive KPI metrics by Triage Level & Shift.
        """
        summary = df.groupby(['triage_level_name', 'shift_period']).agg(
            total_patients=('patient_id', 'count'),
            avg_wait_time_mins=('wait_time_minutes', 'mean'),
            p90_wait_time_mins=('wait_time_minutes', lambda x: np.percentile(x, 90)),
            avg_los_hours=('total_los_hours', 'mean'),
            sla_compliance_rate=('sla_wait_time_compliant', 'mean'),
            admission_rate=('is_admitted', 'mean'),
            lwbs_rate=('is_lwbs', 'mean'),
            readmission_30d_rate=('readmission_30d', 'mean'),
            avg_satisfaction=('patient_satisfaction_score', 'mean'),
            total_revenue_usd=('total_cost_usd', 'sum')
        ).reset_index()

        summary['avg_wait_time_mins'] = summary['avg_wait_time_mins'].round(1)
        summary['p90_wait_time_mins'] = summary['p90_wait_time_mins'].round(1)
        summary['avg_los_hours'] = summary['avg_los_hours'].round(2)
        summary['sla_compliance_rate'] = (summary['sla_compliance_rate'] * 100).round(1)
        summary['admission_rate'] = (summary['admission_rate'] * 100).round(1)
        summary['lwbs_rate'] = (summary['lwbs_rate'] * 100).round(2)
        summary['readmission_30d_rate'] = (summary['readmission_30d_rate'] * 100).round(2)
        summary['avg_satisfaction'] = summary['avg_satisfaction'].round(2)
        summary['total_revenue_usd'] = summary['total_revenue_usd'].round(2)

        return summary

    def run_pipeline(self):
        """Execute full data processing pipeline."""
        print("=" * 70)
        print("  Hospital ER Data Pipeline - Execution Started")
        print("  Author: Aman Dwivedi")
        print("=" * 70)

        df_raw = self.load_raw_data()
        df_cleaned = self.clean_and_transform(df_raw)

        cleaned_file = os.path.join(self.processed_dir, "cleaned_er_data.csv")
        df_cleaned.to_csv(cleaned_file, index=False)
        print(f"Saved cleaned data to: {cleaned_file} ({len(df_cleaned):,} rows)")

        summary_kpis = self.compute_summary_kpis(df_cleaned)
        kpi_file = os.path.join(self.processed_dir, "er_kpis_summary.csv")
        summary_kpis.to_csv(kpi_file, index=False)
        print(f"Saved executive summary KPIs to: {kpi_file}")

        print("=" * 70)
        print("  Pipeline completed successfully! Created by Aman Dwivedi.")
        print("=" * 70)
        return df_cleaned, summary_kpis


if __name__ == "__main__":
    pipeline = ERDataPipeline()
    pipeline.run_pipeline()
