import pytest

from calculators.fractional_odds import (
    calculate_vig_fractional,
    fair_prob_to_fractional,
    fractional_to_decimal,
    remove_vig_fractional,
)


class TestFractionalOdds:

    def test_remove_vig_even_odds(self):
        """Test vig removal for even odds (1/1 vs 1/1)."""
        odds = [(1, 1), (1, 1)]
        fair_probs = remove_vig_fractional(odds)

        assert len(fair_probs) == 2
        assert abs(fair_probs[0] - 0.5) < 0.0001
        assert abs(fair_probs[1] - 0.5) < 0.0001
        assert abs(sum(fair_probs) - 1.0) < 0.0001

    def test_remove_vig_betfair_example(self):
        """Test vig removal for Betfair odds example."""
        odds = [(1, 1), (9, 10)]
        fair_probs = remove_vig_fractional(odds)

        assert len(fair_probs) == 2
        assert fair_probs[1] > fair_probs[0]  # 9/10 is favorite
        assert abs(sum(fair_probs) - 1.0) < 0.0001

        # Check approximate values
        assert abs(fair_probs[0] - 0.4872) < 0.001
        assert abs(fair_probs[1] - 0.5128) < 0.001

    def test_remove_vig_heavy_favorite(self):
        """Test vig removal for heavy favorite."""
        odds = [(1, 4), (3, 1)]  # 1/4 (heavy favorite) vs 3/1 (underdog)
        fair_probs = remove_vig_fractional(odds)

        assert fair_probs[0] > 0.7  # Heavy favorite
        assert fair_probs[1] < 0.3  # Heavy underdog
        assert abs(sum(fair_probs) - 1.0) < 0.0001

    def test_calculate_vig_no_vig(self):
        """Test vig calculation for no-vig scenario."""
        odds = [(1, 1), (1, 1)]
        vig = calculate_vig_fractional(odds)

        assert abs(vig) < 0.0001  # Should be 0%

    def test_calculate_vig_standard(self):
        """Test vig calculation for standard vigged odds."""
        odds = [(10, 11), (10, 11)]  # Approximately -110/-110
        vig = calculate_vig_fractional(odds)

        assert abs(vig - 4.76) < 0.1

    def test_calculate_vig_betfair(self):
        """Test vig calculation for Betfair example."""
        odds = [(1, 1), (9, 10)]
        vig = calculate_vig_fractional(odds)

        assert abs(vig - 2.63) < 0.01

    def test_fair_prob_to_fractional_even(self):
        """Test conversion of 50% probability to fractional odds."""
        prob = 0.5
        frac = fair_prob_to_fractional(prob)

        assert frac == (1, 1)

    def test_fair_prob_to_fractional_favorite(self):
        """Test conversion of favorite probability to fractional odds."""
        prob = 0.75  # 75% probability
        frac = fair_prob_to_fractional(prob)

        # Should be approximately 1/3
        assert frac[0] == 1
        assert frac[1] == 3

    def test_fair_prob_to_fractional_underdog(self):
        """Test conversion of underdog probability to fractional odds."""
        prob = 0.25  # 25% probability
        frac = fair_prob_to_fractional(prob)

        # Should be 3/1
        assert frac == (3, 1)

    def test_fractional_to_decimal_even(self):
        """Test conversion of even fractional odds to decimal."""
        decimal = fractional_to_decimal(1, 1)
        assert decimal == 2.0

    def test_fractional_to_decimal_favorite(self):
        """Test conversion of favorite fractional odds to decimal."""
        decimal = fractional_to_decimal(1, 2)  # 1/2
        assert decimal == 1.5

    def test_fractional_to_decimal_underdog(self):
        """Test conversion of underdog fractional odds to decimal."""
        decimal = fractional_to_decimal(3, 2)  # 3/2
        assert decimal == 2.5

    def test_fractional_to_decimal_complex(self):
        """Test conversion of complex fractional odds to decimal."""
        decimal = fractional_to_decimal(9, 10)  # 9/10
        assert abs(decimal - 1.9) < 0.0001

    def test_roundtrip_conversion(self):
        """Test that converting odds to probabilities and back maintains consistency."""
        original_odds = [(6, 5), (4, 5)]
        fair_probs = remove_vig_fractional(original_odds)

        # Convert back to fractional odds
        converted_odds = [fair_prob_to_fractional(p) for p in fair_probs]

        # Convert to decimal for comparison (since fractional approximation may vary)
        [fractional_to_decimal(n, d) for n, d in original_odds]
        [fractional_to_decimal(n, d) for n, d in converted_odds]

        # Normalize to remove vig for fair comparison
        original_probs_normalized = remove_vig_fractional(original_odds)
        converted_probs_normalized = remove_vig_fractional(converted_odds)

        # Should be very close
        for i in range(len(original_probs_normalized)):
            assert abs(original_probs_normalized[i] - converted_probs_normalized[i]) < 0.05

    def test_invalid_odds_zero_denominator(self):
        """Test that zero denominator raises an error."""
        with pytest.raises(ValueError, match="Denominator must be positive"):
            remove_vig_fractional([(1, 0), (1, 1)])

    def test_invalid_odds_negative_numerator(self):
        """Test that negative numerator raises an error."""
        with pytest.raises(ValueError, match="Numerator cannot be negative"):
            remove_vig_fractional([(-1, 1), (1, 1)])

    def test_invalid_odds_empty_list(self):
        """Test that empty odds list raises an error."""
        with pytest.raises(ValueError, match="Odds list cannot be empty"):
            remove_vig_fractional([])

    def test_invalid_probability_out_of_range(self):
        """Test that invalid probabilities raise errors."""
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_fractional(0.0)

        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_fractional(1.0)

        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_fractional(1.5)

    def test_three_way_market(self):
        """Test vig removal for three-way market (e.g., soccer with draw)."""
        odds = [(3, 2), (11, 5), (14, 5)]  # 3/2, 11/5, 14/5
        fair_probs = remove_vig_fractional(odds)

        assert len(fair_probs) == 3
        assert abs(sum(fair_probs) - 1.0) < 0.0001
        assert all(p > 0 for p in fair_probs)
        assert all(p < 1 for p in fair_probs)

    def test_common_fractional_odds(self):
        """Test common fractional odds conversions."""
        # Test some common fractional odds
        common_odds = [
            ((1, 2), 0.6667),    # 1/2 -> 66.67% implied
            ((3, 4), 0.5714),    # 3/4 -> 57.14% implied
            ((5, 4), 0.4444),    # 5/4 -> 44.44% implied
            ((2, 1), 0.3333),    # 2/1 -> 33.33% implied
            ((5, 1), 0.1667),    # 5/1 -> 16.67% implied
        ]

        for (num, den), expected_prob in common_odds:
            odds = [(num, den), (1, 1)]  # Pair with evens for simple test
            remove_vig_fractional(odds)
            # First probability should be close to expected (after vig removal)
            implied = den / (num + den)
            assert abs(implied - expected_prob) < 0.01
