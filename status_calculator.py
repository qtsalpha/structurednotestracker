"""
Status Calculator for Structured Notes
Automatically calculates note status based on dates and KO/KI events
"""

from datetime import datetime, date
from typing import Dict, List


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
    
    # Get note data - use %s for PostgreSQL, ? for SQLite
    try:
        # Try PostgreSQL syntax first
        cursor.execute('SELECT * FROM structured_notes WHERE id = %s', (note_id,))
    except:
        # Fall back to SQLite syntax
        cursor.execute('SELECT * FROM structured_notes WHERE id = ?', (note_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return None
    
    # Convert to dict
    note = dict(row)
    
    # Calculate status
    new_status = calculate_note_status(note)
    
    # Update in database
    try:
        # Try PostgreSQL syntax first
        cursor.execute('''
            UPDATE structured_notes
            SET current_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (new_status, note_id))
    except:
        # Fall back to SQLite syntax
        cursor.execute('''
            UPDATE structured_notes
            SET current_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, note_id))
    
    conn.commit()
    
    return new_status


def update_all_statuses(conn) -> int:
    """
    Update status for all notes in database
    
    Returns:
        Number of notes updated
    """
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM structured_notes')
    rows = cursor.fetchall()
    
    # Handle both SQLite (tuple) and PostgreSQL (dict) row types
    note_ids = []
    for row in rows:
        if isinstance(row, dict):
            note_ids.append(row['id'])
        else:
            note_ids.append(row[0])
    
    count = 0
    for note_id in note_ids:
        update_note_status(conn, note_id)
        count += 1
    
    return count


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

