"""
Product-specific Excel templates for import
Separate templates for FCN and Phoenix notes
"""

import pandas as pd
from datetime import date, datetime


def get_ben_template() -> pd.DataFrame:
    """
    Excel template for BEN (Bonus Enhanced Note) products
    
    BEN Features:
    - No coupons
    - Boosted upside participation (capped)
    - Capital protection if no KI
    - Daily KI monitoring
    - Strike at 88% for conversion
    """
    template_data = {
        'customer_name': ['PT', 'SU LEI'],
        'custodian_bank': ['RBC', 'Barclays'],
        'type_of_structured_product': ['BEN', 'BEN'],
        'notional_amount': [2000000, 1000000],
        'isin': ['XS3135926858', 'XS3135926859'],
        'trade_date': ['2025-09-26', '2025-09-27'],
        'issue_date': ['2025-10-10', '2025-10-11'],
        'observation_start_date': ['2025-09-26', '2025-09-27'],
        'final_valuation_date': ['2026-01-12', '2026-01-13'],
        'coupon_payment_dates': [None, None],  # BEN has no coupons
        'coupon_per_annum': [0, 0],  # No coupons
        'ko_type': [None, None],  # BEN has no KO (no early redemption)
        'ki_type': ['Daily', 'Daily'],  # BEN always has Daily KI
        # Underlying 1
        'underlying_1_ticker': ['NEM UN', 'NVDA UW'],
        'underlying_1_spot_price': [50.00, 186.51],  # Initial Price (100%)
        'underlying_1_strike_price': [44.00, 164.13],  # Strike for conversion (88%)
        'underlying_1_ki_price': [39.00, 145.48],  # KI Barrier (78%)
        'underlying_1_last_close_price': [None, None],
        # Underlying 2
        'underlying_2_ticker': ['B UN', 'META UW'],
        'underlying_2_spot_price': [45.00, 608.84],
        'underlying_2_strike_price': [39.60, 535.78],  # 88%
        'underlying_2_ki_price': [35.10, 474.89],  # 78%
        'underlying_2_last_close_price': [None, None],
        # Underlying 3 (optional)
        'underlying_3_ticker': [None, None],
        'underlying_3_spot_price': [None, None],
        'underlying_3_strike_price': [None, None],
        'underlying_3_ki_price': [None, None],
        'underlying_3_last_close_price': [None, None],
        # Underlying 4 (optional)
        'underlying_4_ticker': [None, None],
        'underlying_4_spot_price': [None, None],
        'underlying_4_strike_price': [None, None],
        'underlying_4_ki_price': [None, None],
        'underlying_4_last_close_price': [None, None],
    }
    
    return pd.DataFrame(template_data)


def get_fcn_template() -> pd.DataFrame:
    """
    Excel template for FCN products
    
    FCN Features:
    - Simple KO/KI barriers (single price per underlying)
    - Regular coupon payments
    - No memory coupon
    - No step-down barriers
    """
    template_data = {
        'customer_name': ['PT', 'SU LEI'],
        'custodian_bank': ['RBC', 'UBS'],
        'type_of_structured_product': ['FCN', 'FCN'],
        'notional_amount': [500000, 1000000],
        'isin': ['XS3166798549', 'XS3166798550'],
        'trade_date': ['2025-11-04', '2025-11-05'],
        'issue_date': ['2025-11-12', '2025-11-13'],
        'observation_start_date': ['2025-12-12', '2025-12-13'],
        'final_valuation_date': ['2026-05-12', '2026-05-13'],
        'coupon_payment_dates': ['2025-12-19, 2026-01-20, 2026-02-20, 2026-03-19, 2026-04-20, 2026-05-19',
                                 '2026-01-20, 2026-02-20, 2026-03-20, 2026-04-20, 2026-05-20'],
        'coupon_per_annum': [13.0, 15.0],
        'ko_type': ['Daily', 'Daily'],
        'ki_type': ['EKI', 'EKI'],
        # Underlying 1
        'underlying_1_ticker': ['DELL UN', 'NVDA UW'],
        'underlying_1_spot_price': [155.67, 186.51],
        'underlying_1_strike_price': [155.67, 186.51],
        'underlying_1_ko_price': [155.67, 186.51],  # 100% for FCN
        'underlying_1_ki_price': [93.40, 121.23],  # 60% for this example
        'underlying_1_last_close_price': [None, None],
        # Underlying 2
        'underlying_2_ticker': ['STX UW', 'META UW'],
        'underlying_2_spot_price': [251.92, 608.84],
        'underlying_2_strike_price': [251.92, 608.84],
        'underlying_2_ko_price': [251.92, 608.84],
        'underlying_2_ki_price': [151.15, 395.74],
        'underlying_2_last_close_price': [None, None],
        # Underlying 3
        'underlying_3_ticker': ['ASML UW', 'TSLA UW'],
        'underlying_3_spot_price': [1038.08, 405.13],
        'underlying_3_strike_price': [1038.08, 405.13],
        'underlying_3_ko_price': [1038.08, 405.13],
        'underlying_3_ki_price': [622.85, 263.34],
        'underlying_3_last_close_price': [None, None],
        # Underlying 4 (optional)
        'underlying_4_ticker': [None, None],
        'underlying_4_spot_price': [None, None],
        'underlying_4_strike_price': [None, None],
        'underlying_4_ko_price': [None, None],
        'underlying_4_ki_price': [None, None],
        'underlying_4_last_close_price': [None, None],
    }
    
    return pd.DataFrame(template_data)


def get_phoenix_template() -> pd.DataFrame:
    """
    Excel template for Phoenix/Autocall products
    
    Phoenix Features:
    - Step-down KO barriers (6 monthly levels)
    - Memory coupon with coupon barrier
    - Put Strike for conversion
    - Cumulative coupon rates
    """
    template_data = {
        'customer_name': ['PT', 'SU LEI'],
        'custodian_bank': ['RBC', 'UBS'],
        'type_of_structured_product': ['Phoenix', 'Phoenix'],
        'notional_amount': [1000000, 500000],
        'isin': ['XS3208121353', 'XS3208121354'],
        'trade_date': ['2025-11-13', '2025-11-14'],
        'issue_date': ['2025-11-28', '2025-11-29'],
        'observation_start_date': ['2025-12-29', '2025-12-30'],
        'final_valuation_date': ['2026-05-28', '2026-05-29'],
        'coupon_payment_dates': ['2025-12-31, 2026-01-30, 2026-03-04, 2026-04-01, 2026-04-30, 2026-06-01',
                                 '2026-01-31, 2026-02-28, 2026-03-31, 2026-04-30, 2026-05-31, 2026-06-30'],
        'coupon_per_annum': [10.0, 12.0],  # Total annual equivalent
        'coupon_barrier': [426.19, 300.00],  # Coupon barrier price (70% level)
        'ko_type': ['Period-End', 'Period-End'],
        'ko_observation_frequency': ['Monthly', 'Monthly'],
        'ki_type': ['EKI', 'EKI'],
        # Step-down KO barriers (6 levels)
        'ko_barriers_step_down': ['1:608.84, 2:596.66, 3:584.48, 4:572.31, 5:560.13, 6:547.95',
                                  '1:450.00, 2:441.00, 3:432.00, 4:423.00, 5:414.00, 6:405.00'],
        # Memory coupon cumulative rates (%)
        'memory_coupon_rates': ['1.67, 3.33, 5.00, 6.67, 8.34, 10.00',
                                '2.00, 4.00, 6.00, 8.00, 10.00, 12.00'],
        # Underlying 1
        'underlying_1_ticker': ['META UW', 'NVDA UW'],
        'underlying_1_spot_price': [608.84, 450.00],  # Initial Price (100%)
        'underlying_1_strike_price': [455.78, 337.50],  # Put Strike (74.86%)
        'underlying_1_ki_price': [395.74, 292.50],  # KI Barrier (65%)
        'underlying_1_last_close_price': [None, None],
        # Underlying 2
        'underlying_2_ticker': ['NVDA UW', 'META UW'],
        'underlying_2_spot_price': [186.51, 600.00],
        'underlying_2_strike_price': [139.62, 450.00],
        'underlying_2_ki_price': [121.23, 390.00],
        'underlying_2_last_close_price': [None, None],
        # Underlying 3
        'underlying_3_ticker': ['TSLA UW', 'TSLA UW'],
        'underlying_3_spot_price': [405.13, 400.00],
        'underlying_3_strike_price': [303.28, 300.00],
        'underlying_3_ki_price': [263.34, 260.00],
        'underlying_3_last_close_price': [None, None],
        # Underlying 4 (optional)
        'underlying_4_ticker': [None, None],
        'underlying_4_spot_price': [None, None],
        'underlying_4_strike_price': [None, None],
        'underlying_4_ki_price': [None, None],
        'underlying_4_last_close_price': [None, None],
    }
    
    return pd.DataFrame(template_data)


def calculate_current_payment_period(issue_date_str: str, today: date = None) -> int:
    """
    Calculate which payment period we're currently in (1-6 for Phoenix)
    
    Args:
        issue_date_str: Issue date as string
        today: Current date
    
    Returns:
        Payment period number (1-6)
    """
    if today is None:
        today = date.today()
    
    try:
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        months_elapsed = ((today.year - issue_date.year) * 12 + 
                         (today.month - issue_date.month))
        
        # Phoenix typically has 6 monthly periods
        period = min(max(months_elapsed + 1, 1), 6)
        return period
    except:
        return 1

