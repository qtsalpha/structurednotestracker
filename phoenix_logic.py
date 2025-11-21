"""
Phoenix Note Specific Logic
Handles memory coupons, step-down KO barriers, and coupon barrier checking
"""

from datetime import date, datetime
from typing import Dict, List, Tuple, Optional


def parse_step_down_ko_barriers(ko_barriers_str: str) -> List[Dict]:
    """
    Parse step-down KO barriers from string format
    
    Format: "Month1:Price1, Month2:Price2, ..."
    Example: "1:608.84, 2:596.66, 3:584.48, 4:572.31, 5:560.13, 6:547.95"
    
    Returns:
        List of dicts with {'month': int, 'barrier': float}
    """
    if not ko_barriers_str:
        return []
    
    barriers = []
    for item in ko_barriers_str.split(','):
        item = item.strip()
        if ':' in item:
            try:
                month, price = item.split(':')
                barriers.append({
                    'month': int(month.strip()),
                    'barrier': float(price.strip())
                })
            except:
                continue
    
    return sorted(barriers, key=lambda x: x['month'])


def get_current_ko_barrier(ko_barriers: List[Dict], payment_period: int) -> Optional[float]:
    """
    Get KO barrier for current payment period
    
    Args:
        ko_barriers: List of step-down barriers
        payment_period: Current payment period (1-6 for Phoenix)
    
    Returns:
        KO barrier price for this period
    """
    for barrier in ko_barriers:
        if barrier['month'] == payment_period:
            return barrier['barrier']
    return None


def calculate_memory_coupon(
    notional: float,
    coupon_rates: List[float],  # Cumulative rates: [1.67%, 3.33%, 5%, ...]
    coupon_barrier: float,
    underlyings: List[Dict],
    payment_period: int
) -> Tuple[float, bool, str]:
    """
    Calculate memory coupon for Phoenix note
    
    Phoenix Memory Coupon Logic:
    - Check if WPS >= Coupon Barrier
    - If yes: Pay accumulated unpaid coupons
    - If no: Coupon accumulates for next period
    
    Args:
        notional: Notional amount
        coupon_rates: List of cumulative coupon rates (as decimals)
        coupon_barrier: Coupon barrier price
        underlyings: List of underlying data with current prices
        payment_period: Current payment period (1-based)
    
    Returns:
        Tuple of (coupon_amount, coupon_paid, message)
    """
    # Find Worst Performing Share
    underlyings_with_prices = [u for u in underlyings 
                               if u.get('last_close_price') and u.get('spot_price')]
    
    if not underlyings_with_prices:
        return 0.0, False, "No price data available"
    
    # Calculate WPS (worst performance)
    worst_performance = float('inf')
    worst_underlying = None
    
    for u in underlyings_with_prices:
        performance = u['last_close_price'] / u['spot_price']
        if performance < worst_performance:
            worst_performance = performance
            worst_underlying = u
    
    if not worst_underlying:
        return 0.0, False, "Could not determine WPS"
    
    # Check if WPS >= Coupon Barrier
    if worst_underlying['last_close_price'] >= coupon_barrier:
        # Pay accumulated coupon
        if payment_period > 0 and payment_period <= len(coupon_rates):
            coupon_rate = coupon_rates[payment_period - 1]
            coupon_amount = notional * coupon_rate
            return coupon_amount, True, f"Coupon paid: WPS {worst_underlying['underlying_ticker']} at ${worst_underlying['last_close_price']:.2f} >= Barrier ${coupon_barrier:.2f}"
        else:
            return 0.0, False, "Invalid payment period"
    else:
        # Coupon not paid - accumulates
        return 0.0, False, f"Coupon not paid: WPS {worst_underlying['underlying_ticker']} at ${worst_underlying['last_close_price']:.2f} < Barrier ${coupon_barrier:.2f}"


def check_phoenix_autocall(
    note: Dict,
    underlyings: List[Dict],
    ko_barriers: List[Dict],
    current_period: int
) -> Tuple[bool, str]:
    """
    Check if Phoenix note should autocall
    
    Args:
        note: Note data
        underlyings: List of underlyings with current prices
        ko_barriers: List of step-down KO barriers
        current_period: Current observation period (1-6)
    
    Returns:
        Tuple of (should_autocall, message)
    """
    # Get KO barrier for current period
    ko_barrier = get_current_ko_barrier(ko_barriers, current_period)
    
    if not ko_barrier:
        return False, "No KO barrier for this period"
    
    # Find WPS
    underlyings_with_prices = [u for u in underlyings 
                               if u.get('last_close_price') and u.get('spot_price')]
    
    if not underlyings_with_prices:
        return False, "No price data"
    
    worst_performance = float('inf')
    worst_underlying = None
    
    for u in underlyings_with_prices:
        performance = u['last_close_price'] / u['spot_price']
        if performance < worst_performance:
            worst_performance = performance
            worst_underlying = u
    
    if not worst_underlying:
        return False, "Could not determine WPS"
    
    # Check autocall condition
    if worst_underlying['last_close_price'] >= ko_barrier:
        return True, f"Autocall triggered! WPS {worst_underlying['underlying_ticker']} at ${worst_underlying['last_close_price']:.2f} >= KO Barrier ${ko_barrier:.2f} (Period {current_period})"
    else:
        return False, f"No autocall: WPS at ${worst_underlying['last_close_price']:.2f} < KO ${ko_barrier:.2f}"

