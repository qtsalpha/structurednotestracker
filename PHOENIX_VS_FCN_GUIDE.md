# 📊 Phoenix vs FCN Product Logic Guide

## Overview

Your app now supports **product-specific logic** that automatically applies different rules based on the `type_of_structured_product` field.

---

## 🔵 FCN Products (Fixed Coupon Notes)

### Product Types Using FCN Logic:
- FCN
- WOFCN
- ACCU
- DECU
- DCN
- WOBEN
- TWINWIN

### FCN Barrier Logic:

#### **KO (Knock-Out):**
- **Condition:** **ALL** underlyings must be >= their KO prices
- **Example:** 
  - DELL >= $155.67 AND STX >= $251.92 AND ASML >= $1038.08
  - If ALL conditions met → Knocked Out

#### **KI (Knock-In):**
- **Condition:** **ANY ONE** underlying <= its KI price
- **Type:** Usually EKI (European - final date only)
- **Example:**
  - DELL <= $93.40 OR STX <= $151.15 OR ASML <= $622.85
  - If ANY condition met → Knocked In

#### **Conversion:**
- **Condition:** KI occurred AND (on final date) Worst Performing Share < Strike
- **Delivery:** Shares at Strike Price

### Database Fields for FCN:
```
spot_price = Initial Price (e.g., $155.67)
strike_price = Strike (usually same as spot)
ko_price = KO Barrier (e.g., $155.67 = 100%)
ki_price = KI Barrier (e.g., $93.40 = 60%)
```

---

## 🟡 Phoenix Products (Autocall with Memory Coupon)

### Product Types Using Phoenix Logic:
- Phoenix

### Phoenix Barrier Logic:

#### **KO (Autocall):**
- **Condition:** **Worst Performing Share (WPS)** >= KO Barrier
- **WPS:** Underlying with lowest (current_price / spot_price) ratio
- **Step-Down:** KO barrier decreases monthly
  - Month 1: 100% of initial
  - Month 2: 98%
  - Month 3: 96%
  - Month 6: 90%
- **Example:**
  - WPS is META at $580 (spot $608.84 = 95.2% performance)
  - Month 3 KO barrier: $584.48 (96%)
  - $580 < $584.48 → No KO

#### **KI (Knock-In):**
- **Condition:** **Worst Performing Share** <= KI Barrier
- **Type:** Always EKI (European - final date only)
- **Example:**
  - WPS on final date <= $395.74 → Knocked In

#### **Coupon (Memory):**
- **Condition:** **WPS** >= Coupon Barrier (e.g., 70%)
- **Logic:** Accumulates if not paid
- **Rates:** Cumulative (1.67%, 3.33%, 5%, 6.67%, 8.34%, 10%)
- **Example:**
  - Month 1: WPS < barrier → No payment (1.67% accumulates)
  - Month 2: WPS >= barrier → Pay 3.33% (accumulated)

#### **Conversion:**
- **Condition:** KI occurred AND (on final date) WPS < Put Strike
- **Put Strike:** Typically 74.86% level
- **Delivery:** Shares at Put Strike Price

### Database Fields for Phoenix:
```
spot_price = Initial Price (100% reference)
strike_price = Put Strike Price (e.g., $455.78 = 74.86%)
ko_price = Period 1 KO barrier (can be overridden by step-down)
ki_price = KI Barrier (e.g., $395.74 = 65%)
coupon_barrier = Coupon Barrier (e.g., $426.19 = 70%)

Phoenix-specific (optional):
ko_barriers_step_down = "1:608.84, 2:596.66, 3:584.48, ..."
memory_coupon_rates = "1.67, 3.33, 5.00, 6.67, 8.34, 10.00"
```

---

## 📥 Excel Import Templates

### **FCN Template** (`fcn_import_template.xlsx`)

**Columns:**
- Standard note fields (customer, dates, notional, etc.)
- `underlying_X_spot_price` - Initial price
- `underlying_X_strike_price` - Strike price
- `underlying_X_ko_price` - Single KO barrier
- `underlying_X_ki_price` - Single KI barrier

**Use for:** FCN, WOFCN, ACCU, DECU, etc.

### **Phoenix Template** (`phoenix_import_template.xlsx`)

**Additional Columns:**
- `coupon_barrier` - Coupon barrier price (dollar amount)
- `ko_barriers_step_down` - Monthly step-down barriers
- `memory_coupon_rates` - Cumulative coupon rates
- `underlying_X_strike_price` - Put Strike (conversion level)

**Use for:** Phoenix, Autocall products

---

## 🔄 How It Works

### **Barrier Checking:**

When you click **"🔄 Refresh All"**:

1. System reads `type_of_structured_product` field
2. Routes to appropriate logic:
   - **FCN** → `check_ko_barrier_fcn()` + `check_ki_barrier_fcn()`
   - **Phoenix** → `check_ko_barrier_phoenix()` + `check_ki_barrier_phoenix()`
3. Applies product-specific rules
4. Updates status automatically

### **Key Difference:**

| Check | FCN Logic | Phoenix Logic |
|-------|-----------|---------------|
| **KO** | ALL underlyings >= KO | WPS >= KO |
| **KI** | ANY ONE underlying <= KI | WPS <= KI |
| **Convert** | WPS < Strike | WPS < Put Strike |

---

## 💡 Best Practices

### **For FCN:**
1. Set same KO price for all periods (no step-down)
2. Use simple coupon schedule
3. Strike = Spot (usually 100%)

### **For Phoenix:**
1. Input step-down KO barriers if available
2. Input coupon barrier (typically 70%)
3. Strike = Put Strike (typically 74.86%)
4. Memory coupon rates if specified

---

## 🎯 Current Implementation Status:

### ✅ Fully Implemented:
- Product-type routing (FCN vs Phoenix)
- WPS calculation for Phoenix
- ALL underlyings check for FCN
- Separate Excel templates
- EKI support for both
- Conversion logic for both

### 🚧 Future Enhancements:
- Step-down KO barrier database storage
- Memory coupon tracking in database
- Automatic coupon payment calculations
- Month-by-month barrier checking

---

## 📝 How to Use:

1. **Download correct template** based on product type
2. **Fill in all prices** in dollars (no percentages)
3. **Import** - system auto-detects product type
4. **Update prices** - fetch from Yahoo Finance
5. **Refresh All** - system applies correct logic automatically

---

**Your app now intelligently handles both FCN and Phoenix products!** ✅

Created by: Benjamin Yong | Version 1.0 | November 2025

