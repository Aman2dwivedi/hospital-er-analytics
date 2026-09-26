# 🎯 Hospital ER Analytics: Complete Interview Preparation Guide
**Candidate:** **Aman Dwivedi**  
**Project:** Hospital ER Flow & Resource Utilization Analytics Platform  

---

## 1. The 60-Second Elevator Pitch (Memorize This!)

> *"In this project, I built an end-to-end Operational Intelligence platform analyzing over 15,000 Emergency Department patient admissions. Emergency rooms face massive unpredictability, which leads to long wait times, patient walkouts, and lost revenue.  
> Using Python, SQL, DuckDB, and Streamlit, I diagnosed that the primary bottleneck occurs during two daily peak surges (11 AM and 7 PM) where bed occupancy exceeds 88%, quadrupling wait times for Level 3 (Urgent) patients.  
> To solve this, I engineered an interactive What-If Staffing Simulator using queueing theory models that demonstrates how reallocating physician shifts during peak windows reduces patient wait times by 35%, decreases the walkout rate to under 0.8%, and recovers over $220,000 in lost billings."*

---

## 2. Technical & SQL Interview Questions

### Q1: "How did you structure the data pipeline and what feature engineering did you perform?"
* **Answer Structure:**
  * **Ingestion & Cleaning:** Handled timestamps, standardized ESI 1-5 categories, and checked missing values across 15,000 encounters.
  * **Feature Engineering:**
    1. `shift_period`: Segmented into Day (08:00-15:59), Evening (16:00-23:59), and Night (00:00-07:59).
    2. `is_peak_hour`: Binary flag for arrival rushes (10-13h & 18-21h).
    3. `bottleneck_risk_level`: Discretized bed occupancy rate into *Normal (<75%)*, *Elevated (75-88%)*, and *Critical Congestion (>88%)*.
    4. `sla_wait_time_compliant`: Clinical threshold benchmark (e.g. ESI 1 = 0m, ESI 2 <= 15m, ESI 3 <= 60m).

### Q2: "Why did you use 90th percentile (P90) wait times instead of just the mean?"
* **Answer:**  
  *"In healthcare operations, emergency wait times have a severe right-skewed distribution caused by complex trauma and boarding delays. If an average wait time is 55 minutes, it hides the fact that 10% of patients are waiting 140+ minutes. Using SQL window functions like `PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY wait_time_minutes)` provides healthcare executives a true picture of extreme wait-time outliers and operational risk."*

### Q3: "What advanced SQL concepts did you use in this project?"
* **Answer:**
  * **Window Functions:** 7-day rolling moving averages (`AVG(daily_visits) OVER (ORDER BY arrival_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`).
  * **Common Table Expressions (CTEs):** Multi-step aggregation to calculate Left Without Being Seen (LWBS) financial opportunity loss per chief complaint.
  * **Conditional Aggregations:** Dynamic admission rate and SLA compliance calculations using `CASE WHEN ... THEN 1 ELSE 0 END`.
  * **Dense Ranking:** Benchmarking physician throughput and satisfaction scores.

---

## 3. Business Analytics & Domain Insights Questions

### Q4: "What were the biggest operational findings from your analysis?"
* **Answer:**
  1. **Bimodal Rush Pattern:** Patient arrivals peak at 10:00 AM–1:00 PM and 6:00 PM–9:00 PM.
  2. **The ESI 3 Bottleneck:** Level 3 (Urgent) cases make up 42% of total volume and suffer the worst wait time inflation (from 34m off-peak to 88m during peaks) because they compete for beds with higher-acuity trauma cases.
  3. **LWBS Walkout Triggers:** 92% of patients who leave without being seen are low-acuity (ESI 4 & 5) whose wait time crossed 90 minutes.

### Q5: "How did you design the What-If Queueing Simulator?"
* **Answer:**  
  *"I modeled the ER as a multi-server stochastic queue ($M/M/c$ approximation). When a user adjusts the slider to add 1 to 5 physicians during peak hours, the engine computes a non-linear capacity reduction factor accounting for diminishing returns. It calculates projected savings in wait time minutes and the drop in walkout rates in real time."*

### Q6: "What recommendations did you present to hospital leadership?"
* **Answer:**
  1. **Rapid Medical Evaluation (RME) Pod:** Put an emergency doctor/PA at triage during peak windows to order labs/imaging upfront, cutting overall ER length of stay by ~45 mins.
  2. **Fast-Track Clinic:** Divert ESI 4 & 5 minor wounds/rashes to a nurse-led clinic to prevent acute bed clogging.
  3. **Early Morning Inpatient Discharges:** Push general ward discharges before 11:00 AM so inpatient beds are vacant before the afternoon ER rush arrives.

---

## 4. Behavioral & Strategy Questions

### Q7: "If you had access to live hospital EHR data, what would you add next?"
* **Answer:**  
  *"I would build real-time streaming ingestion with Kafka/Spark, train an XGBoost model to predict admission probability right at the triage desk within 2 minutes of arrival, and build automated bed-tracking alerts for the nursing supervisor."*
