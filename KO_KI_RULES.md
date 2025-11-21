# Knock-Out (KO) and Knock-In (KI) Business Rules

## Overview
KO/KI status is **automatically calculated** based on price observations and barrier rules. Users do NOT manually set the status.

---

## 🔴 Knock-Out (KO) Rules

### Rule: **ALL underlyings must exceed their KO prices**

### Type 1: Daily KO
- **Monitoring Period**: Every day from Observation Start Date to Final Valuation Date
- **KO Trigger**: If on ANY day, ALL underlyings' closing prices exceed their respective KO prices
- **Once KO'd**: Note remains knocked out for the rest of tenor
- **Example**: 
  - Note has TSLA (KO: $300), NVDA (KO: $150), META (KO: $600)
  - KO occurs if TSLA > $300 AND NVDA > $150 AND META > $600 on same day

### Type 2: Period-End KO
- **Monitoring Period**: Specific intervals from Observation Start Date
- **Observation Frequency**: Daily, Weekly, Monthly, Quarterly, Semi-Annually
- **KO Trigger**: If at the end of any observation period, ALL underlyings exceed their KO prices
- **Example** (Monthly):
  - Observation Start: Jan 1, 2025
  - Check on: Jan 31, Feb 28, Mar 31, etc.
  - KO if all exceed KO prices on these specific dates

---

## 🔵 Knock-In (KI) Rules

### Rule: **ANY ONE underlying at or below its KI price**

### Type 1: Daily KI
- **Monitoring Period**: Every day from Observation Start Date to Final Valuation Date
- **KI Trigger**: If on ANY day, ANY ONE underlying's closing price is at or below its KI price
- **Once KI'd**: Note remains knocked in for the rest of tenor (permanent)
- **Example**:
  - Note has TSLA (KI: $200), NVDA (KI: $100), META (KI: $400)
  - KI occurs if TSLA ≤ $200 OR NVDA ≤ $100 OR META ≤ $400 on any day

### Type 2: EKI (European Knock-In)
- **Monitoring Period**: Only on Final Valuation Date
- **KI Trigger**: If on Final Valuation Date, ANY ONE underlying is at or below its KI price
- **Example**:
  - Only check on final date (e.g., Dec 31, 2025)
  - KI if any underlying ≤ KI price on that specific date only
  - Prices on other days don't matter

---

## 💻 Implementation Logic

### Daily Monitoring (Daily KO or Daily KI):
```python
for each_day in range(observation_start_date, final_valuation_date):
    prices = get_closing_prices(each_day)
    
    # Check Daily KO
    if all(price > ko_price for price in prices):
        ko_status = "Knocked Out"
        ko_date = each_day
        break
    
    # Check Daily KI
    if any(price <= ki_price for price in prices):
        ki_status = "Knocked In"
        ki_date = each_day
        # KI is permanent once triggered
```

### Period-End Monitoring (Period-End KO):
```python
observation_dates = calculate_period_ends(
    observation_start_date, 
    final_valuation_date, 
    frequency='Monthly'
)

for obs_date in observation_dates:
    prices = get_closing_prices(obs_date)
    
    # Check Period-End KO
    if all(price > ko_price for price in prices):
        ko_status = "Knocked Out"
        ko_date = obs_date
        break
```

### EKI Monitoring:
```python
# Only check on final valuation date
final_prices = get_closing_prices(final_valuation_date)

if any(price <= ki_price for price in final_prices):
    ki_status = "Knocked In"
    ki_date = final_valuation_date
```

---

## 📊 Database Fields

### New Fields Added:
- **ko_type**: 'Daily' or 'Period-End'
- **ko_observation_frequency**: 'Daily', 'Weekly', 'Monthly', 'Quarterly', etc. (only for Period-End)
- **ki_type**: 'Daily' or 'EKI'
- **ko_status**: 'Alive' or 'Knocked Out' (auto-calculated)
- **ko_date**: Date when KO occurred (NULL if still Alive)
- **ki_status**: 'Alive' or 'Knocked In' (auto-calculated)
- **ki_date**: Date when KI occurred (NULL if still Alive)

---

## ⚙️ Auto-Calculation Trigger

KO/KI status will be recalculated when:
1. **Prices are updated** from Yahoo Finance
2. **User manually triggers** status check
3. **Daily scheduled job** (future enhancement)

---

## 🎯 Form Changes

### What Users Input:
✅ KO Type (Daily / Period-End)
✅ KO Observation Frequency (if Period-End)
✅ KI Type (Daily / EKI)

### What System Calculates:
🤖 KO Status (Alive / Knocked Out)
🤖 KO Date (when it happened)
🤖 KI Status (Alive / Knocked In)
🤖 KI Date (when it happened)

