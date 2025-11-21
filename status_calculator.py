"""
Status Calculator for Structured Notes
Automatically calculates note status based on dates and KO/KI events
"""

from datetime import datetime, date
from typing import Dict, List


def get_placeholder(conn) -> str:
    """
    Get the correct SQL placeholder for the database type
    Returns '%s' for PostgreSQL, '?' for SQLite
    """
    try:
        # Check if it's a PostgreSQL connection
        if hasattr(conn, 'get_backend_pid'):
            return '%s'
    except:
        pass
    return '?'


def calculate_note_status(note: Dict, today: date = None) -> str:
    """
    Calculate the current status of a structured note
    
    Status hierarchy:
    1. Not Observed Yet: today < observation_start_date
    2. Alive: observation_start_date <= today <= final_valuation_date (and no KO/KI)
    3. Knocked Out: During Alive phase, KO event occurred
    4. Knocked In: During Alive phase, KI event occurred
    5. Ended: today > final_valuation_date
    
    Args:
        note: Dictionary containing note data
        today: Date to check against (defaults to today)
    
    Returns:
        Status string: 'Not Observed Yet', 'Alive', 'Knocked Out', 'Knocked In', 'Ended'
    """
    if today is None:
        today = date.today()
    
    # Parse dates
    obs_start = parse_date(note.get('observation_start_date'))
    final_val = parse_date(note.get('final_valuation_date'))
    
    if not obs_start or not final_val:
        return 'Unknown'
    
    # 1. Check if observation hasn't started yet
    if today < obs_start:
        return 'Not Observed Yet'
    
    # 5. Check if note has ended
    if today > final_val:
        return 'Ended'
    
    # During observation period (Alive phase)
    # Check for KO event
    if note.get('ko_event_occurred') == 1 or note.get('ko_event_occurred') == True:
        return 'Knocked Out'
    
    # Check for KI event
    if note.get('ki_event_occurred') == 1 or note.get('ki_event_occurred') == True:
        return 'Knocked In'
    
    # 2. Default: Alive (during observation, no events)
    return 'Alive'


def parse_date(date_value):
    """Parse date from various formats"""
    if date_value is None:
        return None
    
    if isinstance(date_value, date):
        return date_value
    
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except:
            try:
                return datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S').date()
            except:
                return None
    
    return None


def update_note_status(conn, note_id: int) -> str:
    """
    Update and return the current status of a note
    
    Args:
        conn: Database connection
        note_id: Note ID to update
    
    Returns:
        Updated status
    """
    cursor = conn.cursor()
    placeholder = get_placeholder(conn)
    
    # Get note data
    query = f'SELECT * FROM structured_notes WHERE id = {placeholder}'
    cursor.execute(query, (note_id,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    # Convert to dict
    note = dict(row)
    
    # Calculate status
    new_status = calculate_note_status(note)
    
    # Update in database
    query = f'''
        UPDATE structured_notes
        SET current_status = {placeholder}, updated_at = CURRENT_TIMESTAMP
        WHERE id = {placeholder}
    '''
    cursor.execute(query, (new_status, note_id))
    
    conn.commit()
    
    return new_status


def update_all_statuses(conn, progress_callback=None) -> tuple[int, list]:
    """
    Update status for all notes in database
    
    Args:
        conn: Database connection
        progress_callback: Optional callback function(current, total, isin, status) for progress updates
    
    Returns:
        Tuple of (updated_count, failed_isins)
    """
    cursor = conn.cursor()
    
    # Get all notes with their ISINs
    cursor.execute('SELECT id, isin FROM structured_notes')
    rows = cursor.fetchall()
    
    # Handle both SQLite (tuple) and PostgreSQL (dict) row types
    notes_data = []
    for row in rows:
        if isinstance(row, dict):
            notes_data.append((row['id'], row.get('isin', 'No ISIN')))
        else:
            notes_data.append((row[0], row[1] if row[1] else 'No ISIN'))
    
    total = len(notes_data)
    updated_count = 0
    failed_isins = []
    
    for idx, (note_id, isin) in enumerate(notes_data):
        try:
            update_note_status(conn, note_id)
            updated_count += 1
            
            if progress_callback:
                progress_callback(idx + 1, total, isin, "✅ Updated")
        except Exception as e:
            failed_isins.append(f"{isin} - {str(e)}")
            
            if progress_callback:
                progress_callback(idx + 1, total, isin, f"❌ Failed")
    
    return updated_count, failed_isins


if __name__ == "__main__":
    # Test status calculation
    from datetime import timedelta
    
    today = date.today()
    
    test_cases = [
        {
            'name': 'Not yet started',
            'note': {
                'observation_start_date': str(today + timedelta(days=10)),
                'final_valuation_date': str(today + timedelta(days=100)),
                'ko_event_occurred': 0,
                'ki_event_occurred': 0
            },
            'expected': 'Not Observed Yet'
        },
        {
            'name': 'Active and alive',
            'note': {
                'observation_start_date': str(today - timedelta(days=10)),
                'final_valuation_date': str(today + timedelta(days=100)),
                'ko_event_occurred': 0,
                'ki_event_occurred': 0
            },
            'expected': 'Alive'
        },
        {
            'name': 'Knocked out',
            'note': {
                'observation_start_date': str(today - timedelta(days=10)),
                'final_valuation_date': str(today + timedelta(days=100)),
                'ko_event_occurred': 1,
                'ki_event_occurred': 0
            },
            'expected': 'Knocked Out'
        },
        {
            'name': 'Already ended',
            'note': {
                'observation_start_date': str(today - timedelta(days=100)),
                'final_valuation_date': str(today - timedelta(days=10)),
                'ko_event_occurred': 0,
                'ki_event_occurred': 0
            },
            'expected': 'Ended'
        }
    ]
    
    print("Testing Status Calculation Logic")
    print("="*60)
    
    for test in test_cases:
        result = calculate_note_status(test['note'])
        status = "✅" if result == test['expected'] else "❌"
        print(f"{status} {test['name']}: {result} (expected: {test['expected']})")

