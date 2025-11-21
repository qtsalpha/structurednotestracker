"""
Database module for Structured Notes Tracking System
Handles database creation and operations
Supports both PostgreSQL (production) and SQLite (local development)
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict
import json

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class StructuredNotesDB:
    """Database manager for structured notes"""
    
    def __init__(self, db_path: str = "structured_notes_new.db"):
        self.db_path = db_path
        self.conn = None
        
        # Check for cloud database URL (Supabase, Railway, Render, etc.)
        self.database_url = os.getenv('DATABASE_URL')
        
        # Determine database type
        if self.database_url and POSTGRES_AVAILABLE:
            self.db_type = 'postgresql'
            # Fix Railway/Render postgres:// to postgresql://
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        else:
            self.db_type = 'sqlite'
            if self.database_url and not POSTGRES_AVAILABLE:
                print("⚠️ DATABASE_URL found but psycopg2 not installed. Falling back to SQLite.")
        
    def connect(self):
        """Create database connection"""
        if self.db_type == 'postgresql':
            try:
                # Close existing connection if any
                if self.conn:
                    try:
                        self.conn.close()
                    except:
                        pass
                
                # Create new connection with keepalive settings
                self.conn = psycopg2.connect(
                    self.database_url,
                    cursor_factory=RealDictCursor,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
                print("✅ Connected to PostgreSQL database")
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("\n⚠️ CRITICAL: Cloud database connection required!")
                print("Please check:")
                print("  1. DATABASE_URL is set correctly in .env file")
                print("  2. psycopg2-binary is installed: pip install psycopg2-binary")
                print("  3. Internet connection is working")
                print("  4. Supabase database is active")
                raise Exception(f"Failed to connect to PostgreSQL: {e}")
        else:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            print("✅ Connected to SQLite database")
        
        return self.conn
    
    def ensure_connection(self):
        """Ensure database connection is alive, reconnect if needed"""
        if self.db_type == 'postgresql':
            try:
                # Test connection
                cursor = self.conn.cursor()
                cursor.execute('SELECT 1')
                cursor.close()
            except:
                # Reconnect if connection is dead
                print("🔄 Reconnecting to database...")
                self.connect()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        if self.db_type == 'postgresql':
            # PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS structured_notes (
                    id SERIAL PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    custodian_bank TEXT,
                    type_of_structured_product TEXT NOT NULL,
                    notional_amount REAL,
                    isin TEXT,
                    trade_date DATE,
                    issue_date DATE,
                    observation_start_date DATE,
                    final_valuation_date DATE,
                    coupon_payment_dates TEXT,
                    coupon_per_annum REAL,
                    coupon_barrier REAL,
                    ko_type TEXT,
                    ko_observation_frequency TEXT,
                    ki_type TEXT,
                    current_status TEXT DEFAULT 'Not Observed Yet',
                    ko_event_occurred INTEGER DEFAULT 0,
                    ko_event_date DATE,
                    ki_event_occurred INTEGER DEFAULT 0,
                    ki_event_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_underlyings (
                    id SERIAL PRIMARY KEY,
                    note_id INTEGER NOT NULL,
                    underlying_sequence INTEGER NOT NULL,
                    underlying_name TEXT,
                    underlying_ticker TEXT,
                    spot_price REAL,
                    strike_price REAL,
                    ko_price REAL,
                    ki_price REAL,
                    last_close_price REAL,
                    last_price_update TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES structured_notes(id) ON DELETE CASCADE,
                    UNIQUE(note_id, underlying_sequence)
                )
            ''')
            
            # Create indexes for PostgreSQL
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_name ON structured_notes(customer_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_type ON structured_notes(type_of_structured_product)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_note_underlyings_note_id ON note_underlyings(note_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_underlying_ticker ON note_underlyings(underlying_ticker)')
            
        else:
            # SQLite syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS structured_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    custodian_bank TEXT,
                    type_of_structured_product TEXT NOT NULL,
                    notional_amount REAL,
                    isin TEXT,
                    trade_date DATE,
                    issue_date DATE,
                    observation_start_date DATE,
                    final_valuation_date DATE,
                    coupon_payment_dates TEXT,
                    coupon_per_annum REAL,
                    coupon_barrier REAL,
                    ko_type TEXT,
                    ko_observation_frequency TEXT,
                    ki_type TEXT,
                    current_status TEXT DEFAULT 'Not Observed Yet',
                    ko_event_occurred INTEGER DEFAULT 0,
                    ko_event_date DATE,
                    ki_event_occurred INTEGER DEFAULT 0,
                    ki_event_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_underlyings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER NOT NULL,
                    underlying_sequence INTEGER NOT NULL,
                    underlying_name TEXT,
                    underlying_ticker TEXT,
                    spot_price REAL,
                    strike_price REAL,
                    ko_price REAL,
                    ki_price REAL,
                    last_close_price REAL,
                    last_price_update TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES structured_notes(id) ON DELETE CASCADE,
                    UNIQUE(note_id, underlying_sequence)
                )
            ''')
            
            # Create indexes for SQLite
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_name ON structured_notes(customer_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_type ON structured_notes(type_of_structured_product)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_note_underlyings_note_id ON note_underlyings(note_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_underlying_ticker ON note_underlyings(underlying_ticker)')
        
        self.conn.commit()
        print(f"✅ Database tables created successfully ({self.db_type})")
    
    def insert_structured_note(self, note_data: Dict, underlyings: List[Dict]) -> int:
        """
        Insert a new structured note with its underlyings
        
        Args:
            note_data: Dictionary with main note fields
            underlyings: List of dictionaries, each containing underlying data
        
        Returns:
            note_id: ID of the inserted note
        """
        # Ensure connection is alive
        self.ensure_connection()
        
        cursor = self.conn.cursor()
        
        # Prepare values
        values = (
            note_data['customer_name'],
            note_data.get('custodian_bank'),
            note_data['type_of_structured_product'],
            note_data.get('notional_amount'),
            note_data.get('isin'),
            note_data.get('trade_date'),
            note_data.get('issue_date'),
            note_data.get('observation_start_date'),
            note_data.get('final_valuation_date'),
            note_data.get('coupon_payment_dates'),
            note_data.get('coupon_per_annum'),
            note_data.get('coupon_barrier'),
            note_data.get('ko_type'),
            note_data.get('ko_observation_frequency'),
            note_data.get('ki_type'),
            'Not Observed Yet',  # Initial status
            0,   # ko_event_occurred
            None,  # ko_event_date
            0,   # ki_event_occurred
            None   # ki_event_date
        )
        
        # Insert main note (different syntax for PostgreSQL vs SQLite)
        if self.db_type == 'postgresql':
            cursor.execute('''
                INSERT INTO structured_notes 
                (customer_name, custodian_bank, type_of_structured_product, notional_amount,
                 isin, trade_date, issue_date, observation_start_date, final_valuation_date,
                 coupon_payment_dates, coupon_per_annum, coupon_barrier, 
                 ko_type, ko_observation_frequency, ki_type,
                 current_status, ko_event_occurred, ko_event_date, ki_event_occurred, ki_event_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', values)
            note_id = cursor.fetchone()['id']
        else:
            cursor.execute('''
                INSERT INTO structured_notes 
                (customer_name, custodian_bank, type_of_structured_product, notional_amount,
                 isin, trade_date, issue_date, observation_start_date, final_valuation_date,
                 coupon_payment_dates, coupon_per_annum, coupon_barrier, 
                 ko_type, ko_observation_frequency, ki_type,
                 current_status, ko_event_occurred, ko_event_date, ki_event_occurred, ki_event_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            note_id = cursor.lastrowid
        
        # Insert underlyings
        for underlying in underlyings:
            underlying_values = (
                note_id,
                underlying['sequence'],
                underlying.get('underlying_name'),
                underlying.get('underlying_ticker'),
                underlying.get('spot_price'),
                underlying.get('strike_price'),
                underlying.get('ko_price'),
                underlying.get('ki_price'),
                underlying.get('last_close_price')
            )
            
            if self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO note_underlyings
                    (note_id, underlying_sequence, underlying_name, underlying_ticker,
                     spot_price, strike_price, ko_price, ki_price, last_close_price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', underlying_values)
            else:
                cursor.execute('''
                    INSERT INTO note_underlyings
                    (note_id, underlying_sequence, underlying_name, underlying_ticker,
                     spot_price, strike_price, ko_price, ki_price, last_close_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', underlying_values)
        
        self.conn.commit()
        return note_id
    
    def get_all_notes(self, customer_name: Optional[str] = None) -> List[Dict]:
        """Get all structured notes, optionally filtered by customer"""
        cursor = self.conn.cursor()
        
        placeholder = '%s' if self.db_type == 'postgresql' else '?'
        
        if customer_name:
            cursor.execute(f'SELECT * FROM structured_notes WHERE customer_name = {placeholder} ORDER BY trade_date DESC', (customer_name,))
        else:
            cursor.execute('SELECT * FROM structured_notes ORDER BY trade_date DESC')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_note_with_underlyings(self, note_id: int) -> Dict:
        """Get a note with all its underlyings"""
        cursor = self.conn.cursor()
        
        placeholder = '%s' if self.db_type == 'postgresql' else '?'
        
        # Get main note
        cursor.execute(f'SELECT * FROM structured_notes WHERE id = {placeholder}', (note_id,))
        note = dict(cursor.fetchone())
        
        # Get underlyings
        cursor.execute(f'SELECT * FROM note_underlyings WHERE note_id = {placeholder} ORDER BY underlying_sequence', (note_id,))
        note['underlyings'] = [dict(row) for row in cursor.fetchall()]
        
        return note
    
    def update_structured_note(self, note_id: int, note_data: Dict, underlyings: List[Dict]) -> bool:
        """
        Update an existing structured note and its underlyings
        
        Args:
            note_id: ID of the note to update
            note_data: Dictionary with updated note fields
            underlyings: List of dictionaries with updated underlying data
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Prepare values
            update_values = (
                note_data['customer_name'],
                note_data.get('custodian_bank'),
                note_data['type_of_structured_product'],
                note_data.get('notional_amount'),
                note_data.get('isin'),
                note_data.get('trade_date'),
                note_data.get('issue_date'),
                note_data.get('observation_start_date'),
                note_data.get('final_valuation_date'),
                note_data.get('coupon_payment_dates'),
                note_data.get('coupon_per_annum'),
                note_data.get('coupon_barrier'),
                note_data.get('ko_type'),
                note_data.get('ko_observation_frequency'),
                note_data.get('ki_type'),
                note_id
            )
            
            # Update main note
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            query = f'''
                UPDATE structured_notes
                SET customer_name = {placeholder}, custodian_bank = {placeholder}, type_of_structured_product = {placeholder},
                    notional_amount = {placeholder}, isin = {placeholder}, trade_date = {placeholder}, issue_date = {placeholder},
                    observation_start_date = {placeholder}, final_valuation_date = {placeholder},
                    coupon_payment_dates = {placeholder}, coupon_per_annum = {placeholder}, coupon_barrier = {placeholder},
                    ko_type = {placeholder}, ko_observation_frequency = {placeholder}, ki_type = {placeholder},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            '''
            cursor.execute(query, update_values)
            
            # Delete existing underlyings
            cursor.execute(f'DELETE FROM note_underlyings WHERE note_id = {placeholder}', (note_id,))
            
            # Insert updated underlyings
            for underlying in underlyings:
                underlying_values = (
                    note_id,
                    underlying['sequence'],
                    underlying.get('underlying_name'),
                    underlying.get('underlying_ticker'),
                    underlying.get('spot_price'),
                    underlying.get('strike_price'),
                    underlying.get('ko_price'),
                    underlying.get('ki_price'),
                    underlying.get('last_close_price')
                )
                
                if self.db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO note_underlyings
                        (note_id, underlying_sequence, underlying_name, underlying_ticker,
                         spot_price, strike_price, ko_price, ki_price, last_close_price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', underlying_values)
                else:
                    cursor.execute('''
                        INSERT INTO note_underlyings
                        (note_id, underlying_sequence, underlying_name, underlying_ticker,
                         spot_price, strike_price, ko_price, ki_price, last_close_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', underlying_values)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating note {note_id}: {e}")
            return False
    
    def delete_note(self, note_id: int) -> bool:
        """
        Delete a structured note and all its underlyings
        
        Args:
            note_id: ID of the note to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            
            # Delete underlyings and main note
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cursor.execute(f'DELETE FROM note_underlyings WHERE note_id = {placeholder}', (note_id,))
            cursor.execute(f'DELETE FROM structured_notes WHERE id = {placeholder}', (note_id,))
            
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting note {note_id}: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # Initialize database
    db = StructuredNotesDB()
    db.connect()
    db.create_tables()
    print("✅ Database initialized successfully")
    db.close()

