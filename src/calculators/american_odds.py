from typing import List, Tuple


def remove_vig_american(odds_list: List[int]) -> List[float]:
    """
    Remove vig from American odds and return fair odds probabilities.
    
    Args:
        odds_list: List of American odds (e.g., [-110, +110] or [-150, +130])
    
    Returns:
        List of fair probabilities (as decimals, e.g., 0.5 for 50%) with vig removed
    
    Example:
        >>> remove_vig_american([-110, -110])
        [0.5, 0.5]
        
        >>> remove_vig_american([-150, +130])
        [0.5833, 0.4167]  # Approximately
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    # Convert American odds to implied probabilities
    implied_probs = []
    
    for odds in odds_list:
        if odds == 0:
            raise ValueError("American odds cannot be 0")
        
        if odds > 0:
            # Positive odds (underdog): +150 = 100/(150+100) = 40%
            implied_prob = 100 / (odds + 100)
        else:
            # Negative odds (favorite): -150 = 150/(150+100) = 60%
            implied_prob = abs(odds) / (abs(odds) + 100)
        
        implied_probs.append(implied_prob)
    
    # Calculate total implied probability (will be > 1.0 due to vig)
    total_prob = sum(implied_probs)
    
    if total_prob <= 0:
        raise ValueError("Total probability must be positive")
    
    # Remove vig by normalizing probabilities
    fair_probs = [prob / total_prob for prob in implied_probs]
    
    return fair_probs


def calculate_vig_american(odds_list: List[int]) -> float:
    """
    Calculate the vig percentage from American odds.
    
    Args:
        odds_list: List of American odds
    
    Returns:
        Vig as a percentage
    
    Example:
        >>> calculate_vig_american([-110, -110])
        4.76  # Approximately
    """
    implied_probs = []
    
    for odds in odds_list:
        if odds == 0:
            raise ValueError("American odds cannot be 0")
        
        if odds > 0:
            implied_prob = 100 / (odds + 100)
        else:
            implied_prob = abs(odds) / (abs(odds) + 100)
        
        implied_probs.append(implied_prob)
    
    total_prob = sum(implied_probs)
    return (total_prob - 1.0) * 100


def american_to_probability(american_odds: int) -> float:
    """
    Convert American odds to probability.
    
    Args:
        american_odds: American odds (e.g., -110, +150)
    
    Returns:
        Probability as a decimal (e.g., 0.6 for 60%)
    
    Example:
        >>> american_to_probability(-150)
        0.6
        >>> american_to_probability(+150)
        0.4
    """
    if american_odds == 0:
        raise ValueError("American odds cannot be 0")
    
    if american_odds > 0:
        # Positive odds (underdog): +150 = 100/(150+100) = 40%
        return 100 / (american_odds + 100)
    else:
        # Negative odds (favorite): -150 = 150/(150+100) = 60%
        return abs(american_odds) / (abs(american_odds) + 100)


def probability_to_american(probability: float) -> int:
    """
    Convert probability to American odds.
    
    Args:
        probability: Probability as a decimal (e.g., 0.6 for 60%)
    
    Returns:
        American odds as an integer
    
    Example:
        >>> probability_to_american(0.6)
        -150
        >>> probability_to_american(0.4)
        150
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    if probability > 0.5:
        # Favorite (negative odds)
        return int(-(probability / (1 - probability)) * 100)
    else:
        # Underdog (positive odds)
        return int(((1 - probability) / probability) * 100)


def fair_prob_to_american(probability: float) -> int:
    """
    Convert a fair probability back to American odds format.
    
    Args:
        probability: Probability as a decimal (e.g., 0.5 for 50%)
    
    Returns:
        American odds as an integer
    
    Example:
        >>> fair_prob_to_american(0.5)
        100
        >>> fair_prob_to_american(0.6)
        -150
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    if probability > 0.5:
        # Favorite (negative odds)
        return int(-(probability / (1 - probability)) * 100)
    else:
        # Underdog (positive odds) - includes exactly 50%
        return int(((1 - probability) / probability) * 100)