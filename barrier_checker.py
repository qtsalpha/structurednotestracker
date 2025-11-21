"""
Barrier Checker for Structured Notes
Automatically detects KO/KI events based on current prices
Implements conversion logic for KI notes
"""

from datetime import date
from typing import Dict, List, Tuple


def check_ko_barrier(note: Dict, underlyings: List[Dict], today: date = None) -> Tuple[bool, str]:
    """
    Check if note has hit KO barrier
    
    KO Logic: ALL underlyings must exceed their KO prices
    
    Returns:
        Tuple of (ko_occurred, message)
    """
    if today is None:
        today = date.today()
    
    # Only check if in observation period
    if note['current_status'] not in ['Alive', 'Not Observed Yet']:
        return False, "Note not in observation period"
    
    # Check if all underlyings have KO prices
    underlyings_with_ko = [u for u in underlyings if u['ko_price'] and u['ko_price'] > 0]
    
    if not underlyings_with_ko:
        return False, "No KO barriers defined"
    
    # Check if all underlyings have current prices
    underlyings_with_prices = [u for u in underlyings_with_ko if u['last_close_price']]
    
    if len(underlyings_with_prices) < len(underlyings_with_ko):
        return False, "Not all underlyings have current prices"
    
    # Check KO condition: ALL underlyings must be >= KO price
    all_above_ko = True
    ko_details = []
    
    for u in underlyings_with_prices:
        if u['last_close_price'] >= u['ko_price']:
            ko_details.append(f"{u['underlying_ticker']}: ${u['last_close_price']:.2f} >= ${u['ko_price']:.2f} ✅")
        else:
            ko_details.append(f"{u['underlying_ticker']}: ${u['last_close_price']:.2f} < ${u['ko_price']:.2f} ❌")
            all_above_ko = False
    
    if all_above_ko:
        return True, "KO triggered! All underlyings above KO barriers"
    else:
        return False, "KO not triggered"


def check_ki_barrier(note: Dict, underlyings: List[Dict], today: date = None) -> Tuple[bool, str, str]:
    """
    Check if note has hit KI barrier
    
    KI Logic: ANY ONE underlying at or below KI price
    
    Returns:
        Tuple of (ki_occurred, which_underlying, message)
    """
    if today is None:
        today = date.today()
    
    # Only check if in observation period or Alive
    if note['current_status'] not in ['Alive', 'Not Observed Yet']:
        return False, None, "Note not in observation period"
    
    # Check if EKI (European Knock-In) - only check on final valuation date
    if note.get('ki_type') == 'EKI':
        from datetime import datetime
        try:
            final_val = datetime.strptime(note['final_valuation_date'], '%Y-%m-%d').date()
            if today != final_val:
                return False, None, "EKI: Only check on final valuation date"
        except:
            pass
    
    # Check if any underlyings have KI prices
    underlyings_with_ki = [u for u in underlyings if u['ki_price'] and u['ki_price'] > 0]
    
    if not underlyings_with_ki:
        return False, None, "No KI barriers defined"
    
    # Check if underlyings have current prices
    underlyings_with_prices = [u for u in underlyings_with_ki if u['last_close_price']]
    
    if len(underlyings_with_prices) < len(underlyings_with_ki):
        return False, None, "Not all underlyings have current prices"
    
    # Check KI condition: ANY ONE underlying at or below KI price
    for u in underlyings_with_prices:
        if u['last_close_price'] <= u['ki_price']:
            return True, u['underlying_ticker'], f"KI triggered by {u['underlying_ticker']}: ${u['last_close_price']:.2f} <= ${u['ki_price']:.2f}"
    
    return False, None, "KI not triggered"


def check_conversion(note: Dict, underlyings: List[Dict], today: date = None) -> Tuple[bool, str]:
    """
    Check if KI note should be converted to shares
    
    Conversion Logic:
    - ONLY check on Final Valuation Date (not before)
    - Note must be Knocked In (KI event occurred during tenor)
    - Lowest Performing Share < Strike Price on final date
    - Shares delivered at Strike Price (not KI price)
    
    Returns:
        Tuple of (should_convert, message)
    """
    if today is None:
        today = date.today()
    
    # Must be Knocked In first
    if note['current_status'] != 'Knocked In':
        return False, "Not a Knocked In note"
    
    # IMPORTANT: Only check on final valuation date (not before/after)
    from datetime import datetime
    try:
        final_val = datetime.strptime(note['final_valuation_date'], '%Y-%m-%d').date()
        if today != final_val:  # Must be exactly on final date
            return False, "Conversion only checked on final valuation date"
    except:
        return False, "Invalid final valuation date"
    
    # Find the worst performing underlying (lowest % of strike)
    underlyings_with_prices = [u for u in underlyings if u['last_close_price'] and u['strike_price']]
    
    if not underlyings_with_prices:
        return False, "No underlyings with complete price data"
    
    # Calculate performance for each underlying
    worst_performance = float('inf')
    worst_underlying = None
    
    for u in underlyings_with_prices:
        performance = u['last_close_price'] / u['strike_price']
        if performance < worst_performance:
            worst_performance = performance
            worst_underlying = u
    
    if not worst_underlying:
        return False, "Could not determine worst performing underlying"
    
    # Check if worst performing is below strike price
    # Conversion happens at strike price (shares = notional / strike)
    if worst_underlying['last_close_price'] < worst_underlying['strike_price']:
        return True, f"Converted: LPS {worst_underlying['underlying_ticker']} at ${worst_underlying['last_close_price']:.2f} < Strike ${worst_underlying['strike_price']:.2f} → Physical delivery at strike"
    else:
        return False, f"Cash settlement: LPS {worst_underlying['underlying_ticker']} at ${worst_underlying['last_close_price']:.2f} >= Strike ${worst_underlying['strike_price']:.2f}"


def check_all_barriers(conn) -> Tuple[int, int, int, List[str]]:
    """
    Check all notes for barrier breaches and conversions
    
    Returns:
        Tuple of (ko_count, ki_count, converted_count, details_list)
    """
    cursor = conn.cursor()
    
    # Get all notes
    cursor.execute('SELECT * FROM structured_notes')
    rows = cursor.fetchall()
    notes = [dict(row) for row in rows]
    
    ko_count = 0
    ki_count = 0
    converted_count = 0
    details = []
    
    for note in notes:
        note_id = int(note['id'])
        isin = note.get('isin', 'No ISIN')
        
        # Get underlyings for this note
        try:
            if hasattr(conn, 'get_backend_pid'):
                cursor.execute('SELECT * FROM note_underlyings WHERE note_id = %s', (note_id,))
            else:
                cursor.execute('SELECT * FROM note_underlyings WHERE note_id = ?', (note_id,))
        except:
            cursor.execute('SELECT * FROM note_underlyings WHERE note_id = ?', (note_id,))
        
        underlyings = [dict(row) for row in cursor.fetchall()]
        
        # Check for conversion first (KI notes at maturity)
        should_convert, conv_msg = check_conversion(note, underlyings)
        if should_convert:
            # Update to Converted status
            try:
                if hasattr(conn, 'get_backend_pid'):
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', ('Converted', note_id))
                else:
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', ('Converted', note_id))
                conn.commit()
                converted_count += 1
                details.append(f"✅ {isin}: {conv_msg}")
            except Exception as e:
                details.append(f"❌ {isin}: Failed to convert - {str(e)}")
            continue
        
        # Skip if already KO, KI, or Ended
        if note['current_status'] not in ['Alive', 'Not Observed Yet']:
            continue
        
        # Check KO barrier
        ko_triggered, ko_msg = check_ko_barrier(note, underlyings)
        if ko_triggered:
            try:
                if hasattr(conn, 'get_backend_pid'):
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = %s, ko_event_occurred = 1, ko_event_date = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', ('Knocked Out', note_id))
                else:
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = ?, ko_event_occurred = 1, ko_event_date = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', ('Knocked Out', note_id))
                conn.commit()
                ko_count += 1
                details.append(f"🔴 KO: {isin} - {ko_msg}")
            except Exception as e:
                details.append(f"❌ {isin}: Failed to update KO - {str(e)}")
            continue
        
        # Check KI barrier
        ki_triggered, which_underlying, ki_msg = check_ki_barrier(note, underlyings)
        if ki_triggered:
            try:
                if hasattr(conn, 'get_backend_pid'):
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = %s, ki_event_occurred = 1, ki_event_date = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', ('Knocked In', note_id))
                else:
                    cursor.execute('''
                        UPDATE structured_notes
                        SET current_status = ?, ki_event_occurred = 1, ki_event_date = CURRENT_DATE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', ('Knocked In', note_id))
                conn.commit()
                ki_count += 1
                details.append(f"🟠 KI: {isin} - {ki_msg}")
            except Exception as e:
                details.append(f"❌ {isin}: Failed to update KI - {str(e)}")
    
    return ko_count, ki_count, converted_count, details

