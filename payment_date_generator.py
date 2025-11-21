"""
Payment Date Generator for Structured Notes
Auto-generates coupon payment dates based on frequency
"""

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import List


def generate_payment_dates(first_payment_date: date, 
                           final_date: date,
                           frequency: str) -> List[date]:
    """
    Generate payment dates based on frequency
    
    Args:
        first_payment_date: Date of first coupon payment
        final_date: Final valuation/maturity date
        frequency: 'Monthly', 'Quarterly', 'Semi-Annually', 'Annually', 'At Maturity'
    
    Returns:
        List of payment dates
    """
    payment_dates = []
    
    if frequency == 'At Maturity':
        # Single payment at maturity
        return [final_date]
    
    # Determine interval
    if frequency == 'Monthly':
        delta = relativedelta(months=1)
    elif frequency == 'Quarterly':
        delta = relativedelta(months=3)
    elif frequency == 'Semi-Annually':
        delta = relativedelta(months=6)
    elif frequency == 'Annually':
        delta = relativedelta(years=1)
    else:
        # Default to monthly
        delta = relativedelta(months=1)
    
    # Generate dates
    current_date = first_payment_date
    
    while current_date <= final_date:
        payment_dates.append(current_date)
        current_date = current_date + delta
    
    return payment_dates


def format_dates_for_storage(dates: List[date]) -> str:
    """
    Format list of dates for database storage
    
    Args:
        dates: List of date objects
    
    Returns:
        Comma-separated dates in YYYY-MM-DD format
    """
    return ', '.join([d.strftime('%Y-%m-%d') for d in dates])


def format_dates_for_display(dates: List[date], format_str: str = '%d/%m/%Y') -> str:
    """
    Format list of dates for display
    
    Args:
        dates: List of date objects
        format_str: Date format string (default: DD/MM/YYYY)
    
    Returns:
        Comma-separated dates in specified format
    """
    return ', '.join([d.strftime(format_str) for d in dates])


def parse_manual_dates(date_string: str) -> List[date]:
    """
    Parse manually entered dates supporting multiple formats
    
    Supports:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - MM/DD/YYYY
    
    Args:
        date_string: Comma-separated dates
    
    Returns:
        List of parsed date objects
    """
    if not date_string:
        return []
    
    dates = []
    
    for date_str in date_string.split(','):
        date_str = date_str.strip()
        if not date_str:
            continue
        
        # Try different formats
        formats = [
            '%d/%m/%Y',  # DD/MM/YYYY (your preferred format)
            '%Y-%m-%d',  # YYYY-MM-DD
            '%m/%d/%Y',  # MM/DD/YYYY
            '%d-%m-%Y',  # DD-MM-YYYY
        ]
        
        parsed = False
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                dates.append(parsed_date)
                parsed = True
                break
            except ValueError:
                continue
        
        if not parsed:
            print(f"⚠️ Could not parse date: {date_str}")
    
    return sorted(dates)


if __name__ == "__main__":
    # Test date generation
    from datetime import date
    
    print("Testing Payment Date Generator")
    print("="*60)
    
    first_payment = date(2025, 12, 15)
    final_date = date(2026, 9, 15)
    
    # Test different frequencies
    frequencies = ['Monthly', 'Quarterly', 'Semi-Annually', 'Annually', 'At Maturity']
    
    for freq in frequencies:
        dates = generate_payment_dates(first_payment, final_date, freq)
        print(f"\n{freq}:")
        print(f"  First payment: {first_payment.strftime('%d/%m/%Y')}")
        print(f"  Final date: {final_date.strftime('%d/%m/%Y')}")
        print(f"  Generated {len(dates)} payment dates:")
        for d in dates:
            print(f"    - {d.strftime('%d/%m/%Y')}")
    
    # Test manual date parsing
    print("\n" + "="*60)
    print("Testing Manual Date Parsing:")
    
    test_inputs = [
        "15/12/2025, 15/03/2026, 15/06/2026",  # DD/MM/YYYY
        "2025-12-15, 2026-03-15, 2026-06-15",  # YYYY-MM-DD
        "12/15/2025, 03/15/2026, 06/15/2026"   # MM/DD/YYYY
    ]
    
    for test_input in test_inputs:
        print(f"\nInput: {test_input}")
        parsed = parse_manual_dates(test_input)
        print(f"Parsed {len(parsed)} dates:")
        for d in parsed:
            print(f"  - {d.strftime('%d/%m/%Y')}")





