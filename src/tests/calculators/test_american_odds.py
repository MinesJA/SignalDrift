import pytest

from calculators.american_odds import (
    calculate_vig_american,
    fair_prob_to_american,
    remove_vig_american,
)


class TestAmericanOdds:

    def test_remove_vig_even_odds(self):
        """Test vig removal for even odds (-110/-110)."""
        odds = [-110, -110]
        fair_probs = remove_vig_american(odds)

        assert len(fair_probs) == 2
        assert abs(fair_probs[0] - 0.5) < 0.0001
        assert abs(fair_probs[1] - 0.5) < 0.0001
        assert abs(sum(fair_probs) - 1.0) < 0.0001

    def test_remove_vig_favorite_underdog(self):
        """Test vig removal for favorite/underdog scenario."""
        odds = [-150, +130]
        fair_probs = remove_vig_american(odds)

        assert len(fair_probs) == 2
        assert fair_probs[0] > fair_probs[1]  # Favorite should have higher probability
        assert abs(sum(fair_probs) - 1.0) < 0.0001

        # Check approximate values
        assert abs(fair_probs[0] - 0.5798) < 0.001
        assert abs(fair_probs[1] - 0.4202) < 0.001

    def test_remove_vig_heavy_favorite(self):
        """Test vig removal for heavy favorite."""
        odds = [-300, +250]
        fair_probs = remove_vig_american(odds)

        assert fair_probs[0] > 0.7  # Heavy favorite
        assert fair_probs[1] < 0.3  # Heavy underdog
        assert abs(sum(fair_probs) - 1.0) < 0.0001

    def test_calculate_vig_standard(self):
        """Test vig calculation for standard -110/-110 odds."""
        odds = [-110, -110]
        vig = calculate_vig_american(odds)

        assert abs(vig - 4.76) < 0.01

    def test_calculate_vig_low(self):
        """Test vig calculation for low vig scenario."""
        odds = [-102, -102]
        vig = calculate_vig_american(odds)

        assert vig < 2.0
        assert vig > 0.0

    def test_fair_prob_to_american_even(self):
        """Test conversion of 50% probability to American odds."""
        prob = 0.5
        american = fair_prob_to_american(prob)

        assert american == 100

    def test_fair_prob_to_american_favorite(self):
        """Test conversion of favorite probability to American odds."""
        prob = 0.6
        american = fair_prob_to_american(prob)

        assert american == -149  # int() truncates, so -149.999... becomes -149

    def test_fair_prob_to_american_underdog(self):
        """Test conversion of underdog probability to American odds."""
        prob = 0.4
        american = fair_prob_to_american(prob)

        assert american == 149  # int() truncates, so 149.999... becomes 149

    def test_roundtrip_conversion(self):
        """Test that converting odds to probabilities and back maintains consistency."""
        original_odds = [-120, +110]
        fair_probs = remove_vig_american(original_odds)

        # Convert back to American odds
        converted_odds = [fair_prob_to_american(p) for p in fair_probs]

        # Convert those back to probabilities
        re_converted_probs = remove_vig_american(converted_odds)

        # Should be very close to original fair probabilities
        for i in range(len(fair_probs)):
            assert abs(fair_probs[i] - re_converted_probs[i]) < 0.002  # Allow slightly more tolerance for rounding

    def test_invalid_odds_zero(self):
        """Test that zero odds raise an error."""
        with pytest.raises(ValueError, match="American odds cannot be 0"):
            remove_vig_american([0, -110])

    def test_invalid_odds_empty_list(self):
        """Test that empty odds list raises an error."""
        with pytest.raises(ValueError, match="Odds list cannot be empty"):
            remove_vig_american([])

    def test_invalid_probability_out_of_range(self):
        """Test that invalid probabilities raise errors."""
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_american(0.0)

        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_american(1.0)

        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_american(1.5)

        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_american(-0.5)

    def test_three_way_market(self):
        """Test vig removal for three-way market (e.g., soccer with draw)."""
        odds = [+150, +220, +280]
        fair_probs = remove_vig_american(odds)

        assert len(fair_probs) == 3
        assert abs(sum(fair_probs) - 1.0) < 0.0001
        assert all(p > 0 for p in fair_probs)
        assert all(p < 1 for p in fair_probs)
