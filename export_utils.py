"""
Data Export Utilities for Structured Notes Tracker
Supports CSV and Excel export formats
"""

import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import List, Dict


def prepare_notes_for_export(notes: List[Dict]) -> pd.DataFrame:
    """
    Prepare notes data for export with formatted columns
    """
    if not notes:
        return pd.DataFrame()
    
    df = pd.DataFrame(notes)
    
    # Select and rename columns for export
    export_columns = {
        'id': 'Note ID',
        'customer_name': 'Customer Name',
        'custodian_bank': 'Custodian Bank',
        'type_of_structured_product': 'Product Type',
        'notional_amount': 'Notional Amount',
        'isin': 'ISIN',
        'trade_date': 'Trade Date',
        'issue_date': 'Issue Date',
        'observation_start_date': 'Observation Start',
        'final_valuation_date': 'Final Valuation Date',
        'coupon_per_annum': 'Coupon p.a. (%)',
        'coupon_barrier': 'Coupon Barrier',
        'ko_type': 'KO Type',
        'ki_type': 'KI Type',
        'current_status': 'Current Status',
        'ko_event_date': 'KO Event Date',
        'ki_event_date': 'KI Event Date',
        'created_at': 'Created At',
        'updated_at': 'Updated At'
    }
    
    # Filter to only existing columns
    available_columns = {k: v for k, v in export_columns.items() if k in df.columns}
    df = df[list(available_columns.keys())]
    df = df.rename(columns=available_columns)
    
    # Format percentage
    if 'Coupon p.a. (%)' in df.columns:
        df['Coupon p.a. (%)'] = df['Coupon p.a. (%)'].apply(
            lambda x: f"{x*100:.2f}" if pd.notna(x) else ""
        )
    
    return df


def export_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export dataframe to CSV format
    """
    return df.to_csv(index=False).encode('utf-8')


def export_to_excel(df: pd.DataFrame, sheet_name: str = "Structured Notes") -> bytes:
    """
    Export dataframe to Excel format with formatting
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Get the worksheet
        worksheet = writer.sheets[sheet_name]
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Style header row
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
    
    output.seek(0)
    return output.getvalue()


def get_export_filename(format: str = "csv") -> str:
    """
    Generate timestamped filename for export
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"structured_notes_export_{timestamp}.{format}"


def export_notes_with_underlyings(db, notes: List[Dict]) -> pd.DataFrame:
    """
    Export notes with their underlyings in a detailed format
    """
    detailed_data = []
    
    for note in notes:
        note_id = note['id']
        note_details = db.get_note_with_underlyings(note_id)
        
        # Get base note info
        base_info = {
            'Note ID': note_id,
            'Customer': note_details['customer_name'],
            'Product Type': note_details['type_of_structured_product'],
            'Notional': note_details['notional_amount'],
            'ISIN': note_details.get('isin', ''),
            'Status': note_details['current_status'],
            'Trade Date': note_details['trade_date'],
            'Maturity': note_details['final_valuation_date'],
        }
        
        # Add each underlying as a separate row
        if note_details['underlyings']:
            for u in note_details['underlyings']:
                row = base_info.copy()
                row.update({
                    'Underlying': u['underlying_name'],
                    'Ticker': u['underlying_ticker'],
                    'Spot Price': u['spot_price'],
                    'Strike Price': u['strike_price'],
                    'KO Price': u['ko_price'],
                    'KI Price': u['ki_price'],
                    'Last Close': u['last_close_price'],
                    'Last Updated': u['last_price_update']
                })
                detailed_data.append(row)
        else:
            detailed_data.append(base_info)
    
    return pd.DataFrame(detailed_data)




