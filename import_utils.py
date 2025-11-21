"""
Import utilities for bulk uploading structured notes from Excel
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional


def validate_excel_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that Excel file has required columns
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    required_columns = [
        'customer_name',
        'type_of_structured_product',
        'notional_amount',
        'trade_date',
        'issue_date',
        'observation_start_date',
        'final_valuation_date',
        'coupon_per_annum',
        'coupon_payment_dates'
    ]
    
    # Check for required columns (case insensitive)
    df_columns_lower = [col.lower().strip() for col in df.columns]
    missing_columns = []
    
    for req_col in required_columns:
        if req_col.lower() not in df_columns_lower:
            missing_columns.append(req_col)
    
    if missing_columns:
        return False, [f"Missing required columns: {', '.join(missing_columns)}"]
    
    return True, []


def parse_date(date_value) -> Optional[str]:
    """Parse date from various formats to YYYY-MM-DD string"""
    if pd.isna(date_value):
        return None
    
    if isinstance(date_value, str):
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_value.strip(), fmt).strftime('%Y-%m-%d')
            except:
                continue
        return None
    
    # If it's already a datetime
    if isinstance(date_value, (datetime, pd.Timestamp)):
        return date_value.strftime('%Y-%m-%d')
    
    return None


def parse_excel_to_notes(df: pd.DataFrame) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Parse Excel DataFrame into structured notes and underlyings
    
    Returns:
        Tuple of (notes_list, underlyings_list, errors_list)
    """
    notes = []
    all_underlyings = []
    errors = []
    
    # Normalize column names (lowercase, strip spaces)
    df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row number (header is row 1)
        
        try:
            # Required fields validation
            if pd.isna(row.get('customer_name')):
                errors.append(f"Row {row_num}: Missing customer_name")
                continue
            
            if pd.isna(row.get('type_of_structured_product')):
                errors.append(f"Row {row_num}: Missing type_of_structured_product")
                continue
            
            # Parse dates
            trade_date = parse_date(row.get('trade_date'))
            issue_date = parse_date(row.get('issue_date'))
            obs_start = parse_date(row.get('observation_start_date'))
            final_val = parse_date(row.get('final_valuation_date'))
            
            if not all([trade_date, issue_date, obs_start, final_val]):
                errors.append(f"Row {row_num}: Invalid or missing date(s)")
                continue
            
            # Parse coupon per annum (convert to decimal if needed)
            coupon = row.get('coupon_per_annum', 0)
            if pd.notna(coupon):
                coupon = float(coupon)
                # If it's a percentage (>1), convert to decimal
                if coupon > 1:
                    coupon = coupon / 100.0
            else:
                coupon = 0.0
            
            # Create note data
            note_data = {
                'customer_name': str(row['customer_name']).strip(),
                'custodian_bank': str(row.get('custodian_bank', '')).strip() if pd.notna(row.get('custodian_bank')) else None,
                'type_of_structured_product': str(row['type_of_structured_product']).strip(),
                'notional_amount': float(row.get('notional_amount', 0)) if pd.notna(row.get('notional_amount')) else 0,
                'isin': str(row.get('isin', '')).strip() if pd.notna(row.get('isin')) else None,
                'trade_date': trade_date,
                'issue_date': issue_date,
                'observation_start_date': obs_start,
                'final_valuation_date': final_val,
                'coupon_payment_dates': str(row.get('coupon_payment_dates', '')).strip() if pd.notna(row.get('coupon_payment_dates')) else None,
                'coupon_per_annum': coupon,
                'coupon_barrier': float(row.get('coupon_barrier')) if pd.notna(row.get('coupon_barrier')) else None,
                'ko_type': str(row.get('ko_type', 'Daily')).strip() if pd.notna(row.get('ko_type')) else 'Daily',
                'ko_observation_frequency': str(row.get('ko_observation_frequency', '')).strip() if pd.notna(row.get('ko_observation_frequency')) else None,
                'ki_type': str(row.get('ki_type', 'Daily')).strip() if pd.notna(row.get('ki_type')) else 'Daily',
                'row_number': row_num
            }
            
            # Parse underlyings (up to 4)
            underlyings = []
            for i in range(1, 5):
                ticker_col = f'underlying_{i}_ticker'
                last_close_col = f'underlying_{i}_last_close_price'
                
                ticker = row.get(ticker_col)
                if pd.notna(ticker) and str(ticker).strip():
                    # Get last close price from Excel if provided
                    last_close = row.get(last_close_col)
                    last_close_price = float(last_close) if pd.notna(last_close) else None
                    
                    underlying = {
                        'sequence': i,
                        'underlying_ticker': str(ticker).strip(),
                        'underlying_name': str(ticker).strip(),  # Use ticker as name
                        'spot_price': float(row.get(f'underlying_{i}_spot_price')) if pd.notna(row.get(f'underlying_{i}_spot_price')) else None,
                        'strike_price': float(row.get(f'underlying_{i}_strike_price')) if pd.notna(row.get(f'underlying_{i}_strike_price')) else None,
                        'ko_price': float(row.get(f'underlying_{i}_ko_price')) if pd.notna(row.get(f'underlying_{i}_ko_price')) else None,
                        'ki_price': float(row.get(f'underlying_{i}_ki_price')) if pd.notna(row.get(f'underlying_{i}_ki_price')) else None,
                        'last_close_price': last_close_price
                    }
                    underlyings.append(underlying)
            
            if not underlyings:
                errors.append(f"Row {row_num}: No underlyings specified")
                continue
            
            notes.append(note_data)
            all_underlyings.append(underlyings)
            
        except Exception as e:
            errors.append(f"Row {row_num}: Error parsing - {str(e)}")
            continue
    
    return notes, all_underlyings, errors


def get_excel_template_dataframe() -> pd.DataFrame:
    """
    Create a template DataFrame with example data for Excel import
    """
    template_data = {
        'customer_name': ['PT', 'SU LEI'],
        'custodian_bank': ['RBC', 'UBS'],
        'type_of_structured_product': ['FCN', 'Phoenix'],
        'notional_amount': [500000, 1000000],
        'isin': ['XS3039666410', 'XS3039666411'],
        'trade_date': ['2025-01-15', '2025-02-01'],
        'issue_date': ['2025-01-20', '2025-02-05'],
        'observation_start_date': ['2025-01-25', '2025-02-10'],
        'final_valuation_date': ['2026-01-25', '2026-02-10'],
        'coupon_payment_dates': ['2025-04-25, 2025-07-25, 2025-10-25, 2026-01-25', '2025-05-10, 2025-08-10, 2025-11-10, 2026-02-10'],
        'coupon_per_annum': [12.0, 15.5],
        'coupon_barrier': [None, 70.0],
        'ko_type': ['Daily', 'Period-End'],
        'ko_observation_frequency': [None, 'Monthly'],
        'ki_type': ['Daily', 'EKI'],
        'underlying_1_ticker': ['TSLA', 'NVDA'],
        'underlying_1_spot_price': [250.50, 850.75],
        'underlying_1_strike_price': [250.50, 850.75],
        'underlying_1_ko_price': [275.55, 935.83],
        'underlying_1_ki_price': [175.35, 595.53],
        'underlying_1_last_close_price': [None, None],  # Will be fetched from Yahoo Finance if empty
        'underlying_2_ticker': ['AAPL', 'MSFT'],
        'underlying_2_spot_price': [185.25, 425.30],
        'underlying_2_strike_price': [185.25, 425.30],
        'underlying_2_ko_price': [203.78, 467.83],
        'underlying_2_ki_price': [129.68, 297.71],
        'underlying_2_last_close_price': [None, None],  # Will be fetched from Yahoo Finance if empty
        'underlying_3_ticker': [None, 'AMZN'],
        'underlying_3_spot_price': [None, 175.50],
        'underlying_3_strike_price': [None, 175.50],
        'underlying_3_ko_price': [None, 193.05],
        'underlying_3_ki_price': [None, 122.85],
        'underlying_3_last_close_price': [None, None],  # Will be fetched from Yahoo Finance if empty
        'underlying_4_ticker': [None, None],
        'underlying_4_spot_price': [None, None],
        'underlying_4_strike_price': [None, None],
        'underlying_4_ko_price': [None, None],
        'underlying_4_ki_price': [None, None],
        'underlying_4_last_close_price': [None, None],  # Will be fetched from Yahoo Finance if empty
    }
    
    return pd.DataFrame(template_data)

