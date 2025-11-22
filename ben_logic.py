"""
BEN (Bonus Enhanced Note) Specific Logic
Also known as: Booster Notes, Enhanced Return Notes
"""

from datetime import date
from typing import Dict, List, Tuple, Optional


def calculate_ben_payoff(
    notional: float,
    underlyings: List[Dict],
    participation_rate: float = 1.05,  # 105% typically
    cap: float = 0.1369,  # 13.69% typically
    call_strike: float = 1.0,  # 100%
    strike_pct: float = 0.88,  # 88% typically
    ki_barrier_pct: float = 0.78  # 78% typically
) -> Tuple[str, float, str]:
    """
    Calculate BEN payoff at maturity
    
    BEN Payoff Structure:
    1. If WPS >= Call Strike (100%): Boosted upside (capped)
    2. If WPS between Strike (88%) and Call Strike AND no KI: 100% par
    3. If WPS < Strike BUT no KI: 100% par (capital protected!)
    4. If WPS < Strike AND KI occurred: Physical delivery
    
    Args:
        notional: Notional amount
        underlyings: List of underlyings with prices
        participation_rate: Participation in upside (e.g., 1.05 = 105%)
        cap: Maximum return (e.g., 0.1369 = 13.69%)
        call_strike: Threshold for upside (1.0 = 100%)
        strike_pct: Strike level for conversion (0.88 = 88%)
        ki_barrier_pct: KI barrier level (0.78 = 78%)
    
    Returns:
        Tuple of (settlement_type, amount_or_shares, message)
    """
    # Find Worst Performing Underlying
    underlyings_with_prices = [u for u in underlyings 
                               if u.get('last_close_price') and u.get('spot_price')]
    
    if not underlyings_with_prices:
        return "Unknown", 0, "No price data available"
    
    worst_performance = float('inf')
    worst_underlying = None
    
    for u in underlyings_with_prices:
        performance = u['last_close_price'] / u['spot_price']
        if performance < worst_performance:
            worst_performance = performance
            worst_underlying = u
    
    if not worst_underlying:
        return "Unknown", 0, "Could not determine WPS"
    
    wps_price = worst_underlying['last_close_price']
    wps_initial = worst_underlying['spot_price']
    wps_performance = wps_price / wps_initial
    
    # Calculate strike price (88% of initial)
    strike_price = wps_initial * strike_pct
    
    # Case 1: Upside participation
    if wps_performance >= call_strike:
        # Calculate boosted return
        upside = wps_performance - call_strike
        boosted_upside = min(cap, participation_rate * upside)
        total_return = 1.0 + boosted_upside
        payout = notional * total_return
        
        return "Cash", payout, f"Boosted return: {boosted_upside*100:.2f}% (WPS at {wps_performance*100:.2f}%)"
    
    # Case 2 & 3: Below call strike
    elif wps_price >= strike_price:
        # Between strike and call strike OR above strike with no KI → 100% par
        return "Cash", notional, f"Capital protected: WPS at {wps_performance*100:.2f}% (>= {strike_pct*100}% strike)"
    
    else:
        # WPS < Strike
        # Need to check if KI occurred (this would be in note status)
        # For now, return potential outcomes
        num_shares = notional / strike_price
        return "Physical", num_shares, f"Physical delivery if KI: {num_shares:.2f} shares of {worst_underlying['underlying_ticker']} at ${strike_price:.2f}"


def check_ben_ki_barrier(note: Dict, underlyings: List[Dict], ki_barrier_pct: float = 0.78) -> Tuple[bool, str]:
    """
    Check KI for BEN products
    
    BEN KI Logic:
    - Daily monitoring (from trade date to final date)
    - ANY underlying below its KI barrier (78% of initial)
    - Uses actual KI prices from database (not percentages)
    
    Returns:
        Tuple of (ki_occurred, message)
    """
    # Get underlyings with KI prices
    underlyings_with_prices = [u for u in underlyings 
                               if u.get('last_close_price') and u.get('ki_price')]
    
    if not underlyings_with_prices:
        return False, "No KI price data"
    
    # Check if any underlying below KI barrier
    for u in underlyings_with_prices:
        if u['last_close_price'] < u['ki_price']:
            return True, f"KI triggered: {u['underlying_ticker']} at ${u['last_close_price']:.2f} < KI ${u['ki_price']:.2f}"
    
    return False, "No KI event"

