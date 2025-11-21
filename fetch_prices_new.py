"""
Fetch current prices from Yahoo Finance for structured note underlyings
Compatible with yfinance 0.2.66 (latest version)
"""

import yfinance as yf
import sqlite3
from typing import Dict, Optional, Tuple
import time
from datetime import datetime


def clean_ticker_for_yahoo(ticker: str) -> Optional[str]:
    """
    Convert underlying ticker to Yahoo Finance format
    
    Examples:
        'TSLA' -> 'TSLA'
        'AMZN UQ' -> 'AMZN'
        'MSFT UW' -> 'MSFT'
    """
    if not ticker:
        return None
    
    # Clean up ticker
    ticker = ticker.strip().upper()
    
    # Remove common suffixes
    suffixes = ['UQ', 'UW', 'UN', 'UP', 'EQUITY']
    for suffix in suffixes:
        if ticker.endswith(f' {suffix}'):
            ticker = ticker.replace(f' {suffix}', '')
        elif ticker.endswith(suffix):
            ticker = ticker[:-len(suffix)]
    
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


def update_all_prices(conn: sqlite3.Connection, delay: float = 0.2) -> Tuple[int, int]:
    """
    Update all underlying prices from Yahoo Finance
    
    Args:
        conn: Database connection
        delay: Delay between API calls (seconds) to avoid rate limiting
    
    Returns:
        Tuple of (updated_count, error_count)
    """
    cursor = conn.cursor()
    
    # Get all unique tickers
    cursor.execute('''
        SELECT DISTINCT underlying_ticker
        FROM note_underlyings
        WHERE underlying_ticker IS NOT NULL AND underlying_ticker != ''
    ''')
    
    tickers = [row[0] for row in cursor.fetchall()]
    
    print(f"🔄 Updating prices for {len(tickers)} unique tickers...")
    
    price_cache = {}
    updated_count = 0
    error_count = 0
    
    for ticker in tickers:
        # Clean ticker for Yahoo Finance
        yahoo_ticker = clean_ticker_for_yahoo(ticker)
        
        if not yahoo_ticker:
            print(f"  ⚠️ Skipping {ticker}: Could not parse ticker")
            error_count += 1
            continue
        
        # Check cache first
        if yahoo_ticker in price_cache:
            price = price_cache[yahoo_ticker]
        else:
            print(f"  Fetching {yahoo_ticker}...", end=" ")
            price = fetch_price_from_yahoo(yahoo_ticker)
            
            if price:
                price_cache[yahoo_ticker] = price
                print(f"✅ ${price:.2f}")
            else:
                print(f"❌ Failed")
                error_count += 1
            
            time.sleep(delay)  # Rate limiting
        
        if price:
            # Update all rows with this ticker
            cursor.execute('''
                UPDATE note_underlyings
                SET last_close_price = ?, last_price_update = CURRENT_TIMESTAMP
                WHERE underlying_ticker = ?
            ''', (price, ticker))
            
            updated_count += cursor.rowcount
    
    conn.commit()
    
    print(f"\n✅ Price update complete:")
    print(f"   Updated: {updated_count} positions")
    print(f"   Errors: {error_count} tickers")
    
    return updated_count, error_count


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

