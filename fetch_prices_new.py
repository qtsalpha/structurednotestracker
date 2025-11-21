"""
Fetch current prices from Yahoo Finance for structured note underlyings
Compatible with yfinance 0.2.66 (latest version)
"""

import yfinance as yf
import sqlite3
from typing import Dict, Optional, Tuple
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def clean_ticker_for_yahoo(ticker: str) -> Optional[str]:
    """
    Convert underlying ticker to Yahoo Finance format
    
    Examples:
        'TSLA' -> 'TSLA'
        'APPLE INC. (XNAS:AAPL)' -> 'AAPL'
        'NVIDIA CORPORATION (XNAS:NVDA)' -> 'NVDA'
        'ALIBABA GROUP HOLDING LIMITED (XHKG:9988)' -> '9988.HK'
        '8316 JT' -> '8316.T'
        'SOFTBANK GROUP CORP 9984 JT' -> '9984.T'
    """
    if not ticker:
        return None
    
    ticker = ticker.strip()
    
    # Extract ticker from parentheses format: "COMPANY NAME (EXCHANGE:TICKER)"
    if '(' in ticker and ')' in ticker:
        # Extract content in parentheses
        start = ticker.find('(')
        end = ticker.find(')')
        exchange_ticker = ticker[start+1:end]
        
        # Split by colon to get ticker
        if ':' in exchange_ticker:
            exchange, symbol = exchange_ticker.split(':', 1)
            
            # Handle different exchanges
            if exchange == 'XHKG':  # Hong Kong
                return f"{symbol}.HK"
            elif exchange == 'NEOE':  # Toronto
                return f"{symbol}.TO"
            else:  # US exchanges (XNAS, XNYS, ARCX, etc.)
                return symbol
        else:
            return exchange_ticker
    
    # Handle Japanese stocks: "8316 JT" or "SOFTBANK GROUP CORP 9984 JT"
    if ' JT' in ticker.upper():
        # Extract the number before JT
        parts = ticker.upper().replace('JT', '').split()
        for part in reversed(parts):
            if part.isdigit():
                return f"{part}.T"  # Tokyo Stock Exchange
    
    # Handle simple tickers with spaces (already clean)
    ticker = ticker.upper()
    
    # Remove common suffixes
    suffixes = ['UQ', 'UW', 'UN', 'UP', 'EQUITY', 'US', 'EQUITY']
    for suffix in suffixes:
        if ticker.endswith(f' {suffix}'):
            ticker = ticker.replace(f' {suffix}', '')
    
    # Remove any remaining spaces
    ticker = ticker.strip()
    
    return ticker if ticker else None


def fetch_price_from_yahoo(ticker: str) -> Optional[float]:
    """
    Fetch current price from Yahoo Finance using yfinance 0.2.66
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Current price or None if not found
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Method 1: Try fast_info (new in recent versions)
        try:
            price = stock.fast_info.get('last_price')
            if price:
                return float(price)
        except:
            pass
        
        # Method 2: Try info dictionary
        try:
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            if price:
                return float(price)
        except:
            pass
        
        # Method 3: Fallback to history
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        
        return None
        
    except Exception as e:
        print(f"  ⚠️ Error fetching {ticker}: {str(e)[:50]}")
        return None


def fetch_single_ticker_price(ticker: str) -> Tuple[str, Optional[float], Optional[str]]:
    """
    Fetch price for a single ticker (for parallel processing)
    
    Returns:
        Tuple of (ticker, price, error_message)
    """
    yahoo_ticker = clean_ticker_for_yahoo(ticker)
    
    if not yahoo_ticker:
        return (ticker, None, "Could not parse ticker")
    
    price = fetch_price_from_yahoo(yahoo_ticker)
    
    if price:
        return (ticker, price, None)
    else:
        return (ticker, None, "Failed to fetch from Yahoo Finance")


def update_all_prices(conn, delay: float = 0.2, progress_callback=None) -> Tuple[int, int, list]:
    """
    Update all underlying prices from Yahoo Finance with parallel fetching
    
    Args:
        conn: Database connection
        delay: Delay between API calls (seconds) to avoid rate limiting (not used in parallel mode)
        progress_callback: Optional callback function(current, total, ticker, status) for progress updates
    
    Returns:
        Tuple of (updated_count, error_count, failed_tickers_with_isins)
    """
    cursor = conn.cursor()
    
    # Get all unique tickers
    cursor.execute('''
        SELECT DISTINCT underlying_ticker
        FROM note_underlyings
        WHERE underlying_ticker IS NOT NULL AND underlying_ticker != ''
    ''')
    
    # Handle both PostgreSQL (dict) and SQLite (tuple) rows
    rows = cursor.fetchall()
    tickers = []
    for row in rows:
        if isinstance(row, dict):
            tickers.append(row['underlying_ticker'])
        else:
            tickers.append(row[0])
    
    total_tickers = len(tickers)
    print(f"🔄 Updating prices for {total_tickers} unique tickers...")
    
    updated_count = 0
    error_count = 0
    completed = 0
    failed_tickers = []
    
    # Use parallel fetching for speed (max 5 concurrent requests)
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all fetch tasks
        future_to_ticker = {executor.submit(fetch_single_ticker_price, ticker): ticker for ticker in tickers}
        
        # Process results as they complete
        for future in as_completed(future_to_ticker):
            ticker, price, error = future.result()
            completed += 1
            
            if progress_callback:
                status = f"✅ ${price:.2f}" if price else f"❌ {error}"
                progress_callback(completed, total_tickers, ticker, status)
            
            if price:
                print(f"  ✅ {ticker}: ${price:.2f}")
                
                # Update database
                try:
                    # Detect database type
                    if hasattr(conn, 'get_backend_pid'):
                        # PostgreSQL
                        cursor.execute('''
                            UPDATE note_underlyings
                            SET last_close_price = %s, last_price_update = CURRENT_TIMESTAMP
                            WHERE underlying_ticker = %s
                        ''', (price, ticker))
                    else:
                        # SQLite
                        cursor.execute('''
                            UPDATE note_underlyings
                            SET last_close_price = ?, last_price_update = CURRENT_TIMESTAMP
                            WHERE underlying_ticker = ?
                        ''', (price, ticker))
                    
                    updated_count += cursor.rowcount
                    conn.commit()  # Commit after each update
                except Exception as e:
                    print(f"  ⚠️ Database update failed for {ticker}: {e}")
                    error_count += 1
            else:
                print(f"  ❌ {ticker}: {error}")
                error_count += 1
                
                # Get ISINs for this failed ticker
                try:
                    if hasattr(conn, 'get_backend_pid'):
                        cursor.execute('''
                            SELECT DISTINCT sn.isin 
                            FROM note_underlyings nu
                            JOIN structured_notes sn ON nu.note_id = sn.id
                            WHERE nu.underlying_ticker = %s
                        ''', (ticker,))
                    else:
                        cursor.execute('''
                            SELECT DISTINCT sn.isin 
                            FROM note_underlyings nu
                            JOIN structured_notes sn ON nu.note_id = sn.id
                            WHERE nu.underlying_ticker = ?
                        ''', (ticker,))
                    
                    isins = [row[0] if not isinstance(row, dict) else row['isin'] for row in cursor.fetchall()]
                    isins_str = ', '.join([isin if isin else 'No ISIN' for isin in isins])
                    failed_tickers.append(f"{ticker} (ISINs: {isins_str})")
                except:
                    failed_tickers.append(f"{ticker}")
    
    print(f"\n✅ Price update complete:")
    print(f"   Updated: {updated_count} positions")
    print(f"   Errors: {error_count} tickers")
    
    return updated_count, error_count, failed_tickers


if __name__ == "__main__":
    # Test price fetching
    print(f"yfinance version: {yf.__version__}")
    print("\nTesting Yahoo Finance price fetching...")
    print("="*60)
    
    test_tickers = ['TSLA', 'AAPL', 'MSFT', 'NVDA', 'META']
    
    for ticker in test_tickers:
        price = fetch_price_from_yahoo(ticker)
        if price:
            print(f"✅ {ticker}: ${price:.2f}")
        else:
            print(f"❌ {ticker}: Failed")

