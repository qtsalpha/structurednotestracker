"""
Coupon Calculator for Structured Notes
Calculates expected coupon amounts and accumulated coupons
"""

from datetime import datetime, date
from typing import List, Tuple


def parse_coupon_payment_dates(payment_dates_str: str) -> List[date]:
    """
    Parse coupon payment dates from string
    
    Args:
        payment_dates_str: Comma-separated dates (e.g., "2025-12-15, 2026-03-15, 2026-06-15")
    
    Returns:
        List of date objects
    """
    if not payment_dates_str:
        return []
    
    dates = []
    for date_str in payment_dates_str.split(','):
        date_str = date_str.strip()
        if date_str:
            try:
                # Try YYYY-MM-DD format
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                dates.append(parsed_date)
            except ValueError:
                try:
                    # Try MM/DD/YYYY format
                    parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                    dates.append(parsed_date)
                except ValueError:
                    continue
    
    return sorted(dates)


def calculate_expected_coupon(notional_amount: float, coupon_per_annum: float, 
                              payment_dates_str: str) -> float:
    """
    Calculate expected total coupon amount
    
    For monthly/periodic payments:
    - Each payment = Notional × (Coupon p.a. / Payments per year)
    - Total = Notional × Coupon p.a. × (Number of payments / Payments per year)
    
    Example: 12% p.a., 12 monthly payments over 1 year
    - Total = $1M × 12% = $120,000 (correct!)
    
    Example: 15% p.a., 24 monthly payments over 2 years
    - Total = $1M × 15% × 2 = $300,000 (correct!)
    
    Args:
        notional_amount: Notional amount invested
        coupon_per_annum: Annual coupon rate as decimal (e.g., 0.12 for 12%)
        payment_dates_str: Comma-separated payment dates
    
    Returns:
        Expected total coupon amount
    """
    if not notional_amount or not coupon_per_annum:
        return 0.0
    
    # Parse payment dates
    payment_dates = parse_coupon_payment_dates(payment_dates_str)
    num_payments = len(payment_dates)
    
    if num_payments == 0:
        return 0.0
    
    # Calculate time period from first to last payment
    if num_payments >= 2:
        first_payment = payment_dates[0]
        last_payment = payment_dates[-1]
        
        # Calculate years between first and last payment
        days_between = (last_payment - first_payment).days
        years = days_between / 365.25
        
        # Add one payment period to account for the full term
        # (e.g., 12 monthly payments spans 11 months, but covers 1 full year)
        payment_freq_days = days_between / (num_payments - 1) if num_payments > 1 else 30
        years += (payment_freq_days / 365.25)
        
        # Total expected coupon = Notional × Annual Coupon × Years
        expected_total = notional_amount * coupon_per_annum * years
    else:
        # Single payment - assume it's for 1 year
        expected_total = notional_amount * coupon_per_annum
    
    return expected_total


def calculate_accumulated_coupon(notional_amount: float, coupon_per_annum: float,
                                 payment_dates_str: str, as_of_date: date = None) -> Tuple[float, int, int]:
    """
    Calculate accumulated coupon received so far
    
    Counts how many payment dates have passed and calculates total received
    
    Args:
        notional_amount: Notional amount invested
        coupon_per_annum: Annual coupon rate as decimal (e.g., 0.12 for 12%)
        payment_dates_str: Comma-separated payment dates
        as_of_date: Date to calculate as of (defaults to today)
    
    Returns:
        Tuple of (accumulated_amount, payments_made, total_payments)
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    if not notional_amount or not coupon_per_annum:
        return 0.0, 0, 0
    
    # Parse payment dates
    payment_dates = parse_coupon_payment_dates(payment_dates_str)
    total_payments = len(payment_dates)
    
    if total_payments == 0:
        return 0.0, 0, 0
    
    # Count how many payments have occurred (payment date <= today)
    payments_made = sum(1 for pd in payment_dates if pd <= as_of_date)
    
    # Calculate accumulated coupon
    # Assumption: Each payment is equal (total annual coupon / number of payments)
    per_payment_amount = (notional_amount * coupon_per_annum) / total_payments
    accumulated_amount = per_payment_amount * payments_made
    
    return accumulated_amount, payments_made, total_payments


if __name__ == "__main__":
    # Test calculations
    from datetime import timedelta
    
    today = date.today()
    
    # Test expected coupon
    print("Testing Expected Coupon Calculation:")
    print("="*60)
    
    expected = calculate_expected_coupon(
        notional_amount=500000,
        coupon_per_annum=0.12,
        payment_dates_str="2025-12-15, 2026-03-15, 2026-06-15, 2026-09-15"
    )
    print(f"Notional: $500,000")
    print(f"Coupon: 12% per annum")
    print(f"Payment dates: 4 dates")
    print(f"Expected Total Coupon: ${expected:,.2f}")
    
    # Test accumulated coupon
    print("\n\nTesting Accumulated Coupon Calculation:")
    print("="*60)
    
    # Create test dates: 2 in the past, 2 in the future
    past_date_1 = str(today - timedelta(days=60))
    past_date_2 = str(today - timedelta(days=30))
    future_date_1 = str(today + timedelta(days=30))
    future_date_2 = str(today + timedelta(days=60))
    
    test_dates = f"{past_date_1}, {past_date_2}, {future_date_1}, {future_date_2}"
    
    accumulated, paid, total = calculate_accumulated_coupon(
        notional_amount=500000,
        coupon_per_annum=0.12,
        payment_dates_str=test_dates
    )
    
    print(f"Notional: $500,000")
    print(f"Coupon: 12% per annum")
    print(f"Payment dates: {test_dates}")
    print(f"Payments made: {paid} out of {total}")
    print(f"Accumulated Coupon So Far: ${accumulated:,.2f}")
    print(f"Per payment: ${accumulated/paid:,.2f}" if paid > 0 else "Per payment: N/A")

