from typing import List


def remove_vig_decimal(odds_list: List[float]) -> List[float]:
    """
    Remove vig from decimal odds and return fair odds probabilities.
    
    Args:
        odds_list: List of decimal odds (e.g., [2.0, 2.0] or [1.83, 2.2])
    
    Returns:
        List of fair probabilities (as decimals, e.g., 0.5 for 50%) with vig removed
    
    Example:
        >>> remove_vig_decimal([2.0, 2.0])
        [0.5, 0.5]
        
        >>> remove_vig_decimal([1.83, 2.2])
        [0.5468, 0.4532]  # Approximately
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    # Convert decimal odds to implied probabilities
    implied_probs = []
    
    for odds in odds_list:
        if odds <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0")
        
        # Decimal odds: probability = 1 / decimal_odds
        implied_prob = 1 / odds
        implied_probs.append(implied_prob)
    
    # Calculate total implied probability (will be > 1.0 due to vig)
    total_prob = sum(implied_probs)
    
    if total_prob <= 0:
        raise ValueError("Total probability must be positive")
    
    # Remove vig by normalizing probabilities
    fair_probs = [prob / total_prob for prob in implied_probs]
    
    return fair_probs


def calculate_vig_decimal(odds_list: List[float]) -> float:
    """
    Calculate the vig percentage from decimal odds.
    
    Args:
        odds_list: List of decimal odds
    
    Returns:
        Vig as a percentage
    
    Example:
        >>> calculate_vig_decimal([1.91, 1.91])
        4.71  # Approximately
    """
    implied_probs = []
    
    for odds in odds_list:
        if odds <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0")
        
        implied_prob = 1 / odds
        implied_probs.append(implied_prob)
    
    total_prob = sum(implied_probs)
    return (total_prob - 1.0) * 100


def decimal_to_probability(decimal_odds: float) -> float:
    """
    Convert decimal odds to probability.
    
    Args:
        decimal_odds: Decimal odds (e.g., 2.0, 1.5)
    
    Returns:
        Probability as a decimal (e.g., 0.5 for 50%)
    
    Example:
        >>> decimal_to_probability(2.0)
        0.5
        >>> decimal_to_probability(1.5)
        0.6667
    """
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.0")
    
    return 1 / decimal_odds


def probability_to_decimal(probability: float) -> float:
    """
    Convert probability to decimal odds.
    
    Args:
        probability: Probability as a decimal (e.g., 0.5 for 50%)
    
    Returns:
        Decimal odds
    
    Example:
        >>> probability_to_decimal(0.5)
        2.0
        >>> probability_to_decimal(0.6)
        1.6667
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    return 1 / probability


def fair_prob_to_decimal(probability: float) -> float:
    """
    Convert a fair probability to decimal odds format.
    
    Args:
        probability: Probability as a decimal (e.g., 0.5 for 50%)
    
    Returns:
        Decimal odds
    
    Example:
        >>> fair_prob_to_decimal(0.5)
        2.0
        >>> fair_prob_to_decimal(0.6)
        1.667
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    return 1 / probability


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.
    
    Args:
        decimal_odds: Decimal odds
    
    Returns:
        American odds as an integer
    
    Example:
        >>> decimal_to_american(2.0)
        100
        >>> decimal_to_american(1.5)
        -200
    """
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.0")
    
    implied_prob = 1 / decimal_odds
    
    if implied_prob > 0.5:
        # Favorite (negative odds)
        return int(-(implied_prob / (1 - implied_prob)) * 100)
    else:
        # Underdog (positive odds) - includes exactly 50%
        return int(((1 - implied_prob) / implied_prob) * 100)


def american_to_decimal(american_odds: int) -> float:
    """
    Convert American odds to decimal odds.
    
    Args:
        american_odds: American odds
    
    Returns:
        Decimal odds
    
    Example:
        >>> american_to_decimal(100)
        2.0
        >>> american_to_decimal(-200)
        1.5
    """
    if american_odds == 0:
        raise ValueError("American odds cannot be 0")
    
    if american_odds > 0:
        # Positive odds (underdog)
        implied_prob = 100 / (american_odds + 100)
    else:
        # Negative odds (favorite)
        implied_prob = abs(american_odds) / (abs(american_odds) + 100)
    
    return 1 / implied_prob