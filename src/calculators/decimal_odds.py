from dataclasses import dataclass
from typing import Any

from models.odds_event import OddsType


@dataclass
class FairOddsResult:
    """Result of fair odds calculation"""
    question: str
    og_odds: float
    fair_odds: float
    impl_prob: float
    odds_type: OddsType

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'question': self.question,
            'og_odds': self.og_odds,
            'fair_odds': self.fair_odds,
            'impl_prob': self.impl_prob,
            'odds_type': self.odds_type.value
        }


def calculate_fair_odds(odds_data: list[dict[str, Any]]) -> list[FairOddsResult]:
    """
    Calculate fair odds by removing vig from decimal odds.

    Args:
        odds_data: List of dictionaries with keys 'question' and 'odds'
                   Example: [{'question': 'Team A wins', 'odds': 2.0},
                            {'question': 'Team B wins', 'odds': 2.0}]

    Returns:
        List of FairOddsResult dataclass instances containing:
        - question: The betting question
        - og_odds: Original odds
        - fair_odds: Fair odds after vig removal
        - impl_prob: Implied probability after vig removal
        - odds_type: OddsType.DECIMAL

    Example:
        >>> results = calculate_fair_odds([
        ...     {'question': 'Team A wins', 'odds': 1.83},
        ...     {'question': 'Team B wins', 'odds': 2.2}
        ... ])
        >>> results[0].fair_odds
        1.829
        >>> results[0].impl_prob
        0.5468
    """
    if not odds_data:
        raise ValueError("Odds data cannot be empty")

    # Convert decimal odds to implied probabilities
    implied_probs = []

    for item in odds_data:
        odds = item.get('odds')
        if odds is None:
            raise ValueError("Each item must have 'odds' key")
        if odds <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0")

        # Decimal odds: probability = 1 / decimal_odds
        implied_prob = 1 / odds
        implied_probs.append(implied_prob)

    # Calculate total implied probability (will be > 1.0 due to vig)
    total_prob = sum(implied_probs)

    if total_prob <= 0:
        raise ValueError("Total probability must be positive")

    # Remove vig by normalizing probabilities and convert back to decimal odds
    result = []
    for i, item in enumerate(odds_data):
        fair_prob = implied_probs[i] / total_prob
        fair_decimal_odds = 1 / fair_prob

        result.append(FairOddsResult(
            question=item.get('question'),
            og_odds=item.get('odds'),
            fair_odds=fair_decimal_odds,
            impl_prob=fair_prob,
            odds_type=OddsType.DECIMAL
        ))

    return result


def remove_vig_decimal(odds_list: list[float]) -> list[float]:
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


def calculate_vig_decimal(odds_list: list[float]) -> float:
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
