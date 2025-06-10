from typing import List, Tuple


def remove_vig_fractional(odds_list: List[Tuple[int, int]]) -> List[float]:
    """
    Remove vig from fractional odds and return fair odds probabilities.
    
    Args:
        odds_list: List of fractional odds as tuples (numerator, denominator)
                   e.g., [(1, 1), (9, 10)] for "1/1" and "9/10"
    
    Returns:
        List of fair probabilities (as decimals, e.g., 0.5 for 50%) with vig removed
    
    Example:
        >>> remove_vig_fractional([(1, 1), (1, 1)])
        [0.5, 0.5]
        
        >>> remove_vig_fractional([(1, 1), (9, 10)])
        [0.4762, 0.5238]  # Approximately
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    # Convert fractional odds to implied probabilities
    implied_probs = []
    
    for numerator, denominator in odds_list:
        if denominator <= 0:
            raise ValueError("Denominator must be positive")
        if numerator < 0:
            raise ValueError("Numerator cannot be negative")
        
        # Fractional odds: n/d means you win n for every d wagered
        # Implied probability = d / (n + d)
        implied_prob = denominator / (numerator + denominator)
        implied_probs.append(implied_prob)
    
    # Calculate total implied probability (will be > 1.0 due to vig)
    total_prob = sum(implied_probs)
    
    if total_prob <= 0:
        raise ValueError("Total probability must be positive")
    
    # Remove vig by normalizing probabilities
    fair_probs = [prob / total_prob for prob in implied_probs]
    
    return fair_probs


def calculate_vig_fractional(odds_list: List[Tuple[int, int]]) -> float:
    """
    Calculate the vig percentage from fractional odds.
    
    Args:
        odds_list: List of fractional odds as tuples (numerator, denominator)
    
    Returns:
        Vig as a percentage
    
    Example:
        >>> calculate_vig_fractional([(10, 11), (10, 11)])
        4.76  # Approximately
    """
    implied_probs = []
    
    for numerator, denominator in odds_list:
        if denominator <= 0:
            raise ValueError("Denominator must be positive")
        if numerator < 0:
            raise ValueError("Numerator cannot be negative")
        
        implied_prob = denominator / (numerator + denominator)
        implied_probs.append(implied_prob)
    
    total_prob = sum(implied_probs)
    return (total_prob - 1.0) * 100


def fair_prob_to_fractional(probability: float) -> Tuple[int, int]:
    """
    Convert a fair probability to fractional odds format.
    
    This returns simplified fractional odds as integers.
    For exact decimal representations, use decimal odds instead.
    
    Args:
        probability: Probability as a decimal (e.g., 0.5 for 50%)
    
    Returns:
        Tuple of (numerator, denominator) for fractional odds
    
    Example:
        >>> fair_prob_to_fractional(0.5)
        (1, 1)
        >>> fair_prob_to_fractional(0.4)
        (3, 2)
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    # Calculate decimal odds first
    decimal_odds = 1 / probability
    
    # Convert to fractional (decimal_odds - 1)
    fractional_value = decimal_odds - 1
    
    # Find a reasonable approximation as a fraction
    # For simplicity, we'll use common denominators
    if abs(fractional_value - 1.0) < 0.01:
        return (1, 1)
    elif fractional_value < 1:
        # Favorite - find closest simple fraction
        for denom in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20]:
            num = round(fractional_value * denom)
            if abs(num / denom - fractional_value) < 0.05:
                return (num, denom)
    else:
        # Underdog - find closest simple fraction
        for num in range(1, 21):
            denom = round(num / fractional_value)
            if denom > 0 and abs(num / denom - fractional_value) < 0.05:
                return (num, denom)
    
    # If no good approximation found, use 100 as denominator
    return (int(fractional_value * 100), 100)


def fractional_to_decimal(numerator: int, denominator: int) -> float:
    """
    Convert fractional odds to decimal odds.
    
    Args:
        numerator: Numerator of fractional odds
        denominator: Denominator of fractional odds
    
    Returns:
        Decimal odds
    
    Example:
        >>> fractional_to_decimal(1, 1)
        2.0
        >>> fractional_to_decimal(3, 2)
        2.5
    """
    if denominator <= 0:
        raise ValueError("Denominator must be positive")
    
    return (numerator / denominator) + 1