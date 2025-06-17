import pytest
from calculators.decimal_odds import (
    remove_vig_decimal, 
    calculate_fair_odds,
    FairOddsResult,
    calculate_vig_decimal, 
    fair_prob_to_decimal,
    decimal_to_american,
    american_to_decimal
)
from models.odds_event import OddsType


class TestDecimalOdds:
    
    def test_remove_vig_even_odds(self):
        """Test vig removal for even odds (2.0/2.0)."""
        odds = [2.0, 2.0]
        fair_probs = remove_vig_decimal(odds)
        
        assert len(fair_probs) == 2
        assert abs(fair_probs[0] - 0.5) < 0.0001
        assert abs(fair_probs[1] - 0.5) < 0.0001
        assert abs(sum(fair_probs) - 1.0) < 0.0001
    
    def test_remove_vig_pinnacle_example(self):
        """Test vig removal for Pinnacle odds example."""
        odds = [2.050, 1.884]
        fair_probs = remove_vig_decimal(odds)
        
        assert len(fair_probs) == 2
        assert fair_probs[1] > fair_probs[0]  # Lower decimal odds = favorite
        assert abs(sum(fair_probs) - 1.0) < 0.0001
        
        # Check approximate values
        assert abs(fair_probs[0] - 0.4789) < 0.001
        assert abs(fair_probs[1] - 0.5211) < 0.001
    
    def test_remove_vig_heavy_favorite(self):
        """Test vig removal for heavy favorite."""
        odds = [1.25, 4.0]
        fair_probs = remove_vig_decimal(odds)
        
        assert fair_probs[0] > 0.7  # Heavy favorite (low decimal odds)
        assert fair_probs[1] < 0.3  # Heavy underdog (high decimal odds)
        assert abs(sum(fair_probs) - 1.0) < 0.0001
    
    def test_calculate_vig_no_vig(self):
        """Test vig calculation for no-vig scenario."""
        odds = [2.0, 2.0]
        vig = calculate_vig_decimal(odds)
        
        assert abs(vig) < 0.0001  # Should be 0%
    
    def test_calculate_vig_standard(self):
        """Test vig calculation for standard vigged odds."""
        odds = [1.91, 1.91]  # Approximately -110/-110 in American
        vig = calculate_vig_decimal(odds)
        
        assert abs(vig - 4.71) < 0.1
    
    def test_calculate_vig_pinnacle(self):
        """Test vig calculation for Pinnacle example."""
        odds = [2.050, 1.884]
        vig = calculate_vig_decimal(odds)
        
        assert abs(vig - 1.86) < 0.01
    
    def test_fair_prob_to_decimal_even(self):
        """Test conversion of 50% probability to decimal odds."""
        prob = 0.5
        decimal = fair_prob_to_decimal(prob)
        
        assert decimal == 2.0
    
    def test_fair_prob_to_decimal_favorite(self):
        """Test conversion of favorite probability to decimal odds."""
        prob = 0.6
        decimal = fair_prob_to_decimal(prob)
        
        assert abs(decimal - 1.667) < 0.001
    
    def test_fair_prob_to_decimal_underdog(self):
        """Test conversion of underdog probability to decimal odds."""
        prob = 0.25
        decimal = fair_prob_to_decimal(prob)
        
        assert decimal == 4.0
    
    def test_decimal_to_american_even(self):
        """Test conversion of even decimal odds to American."""
        american = decimal_to_american(2.0)
        assert american == 100
    
    def test_decimal_to_american_favorite(self):
        """Test conversion of favorite decimal odds to American."""
        american = decimal_to_american(1.5)
        assert american == -199  # int() truncates, so -199.999... becomes -199
    
    def test_decimal_to_american_underdog(self):
        """Test conversion of underdog decimal odds to American."""
        american = decimal_to_american(2.5)
        assert american == 149  # int() truncates, so 149.999... becomes 149
    
    def test_american_to_decimal_positive(self):
        """Test conversion of positive American odds to decimal."""
        decimal = american_to_decimal(150)
        assert decimal == 2.5
    
    def test_american_to_decimal_negative(self):
        """Test conversion of negative American odds to decimal."""
        decimal = american_to_decimal(-200)
        assert decimal == 1.5
    
    def test_american_to_decimal_even(self):
        """Test conversion of even American odds to decimal."""
        decimal = american_to_decimal(100)
        assert decimal == 2.0
    
    def test_roundtrip_conversion(self):
        """Test that converting odds to probabilities and back maintains consistency."""
        original_odds = [1.83, 2.2]
        fair_probs = remove_vig_decimal(original_odds)
        
        # Convert back to decimal odds
        converted_odds = [fair_prob_to_decimal(p) for p in fair_probs]
        
        # Convert those back to probabilities
        re_converted_probs = remove_vig_decimal(converted_odds)
        
        # Should be very close to original fair probabilities
        for i in range(len(fair_probs)):
            assert abs(fair_probs[i] - re_converted_probs[i]) < 0.001
    
    def test_invalid_odds_too_low(self):
        """Test that decimal odds <= 1.0 raise an error."""
        with pytest.raises(ValueError, match="Decimal odds must be greater than 1.0"):
            remove_vig_decimal([1.0, 2.0])
        
        with pytest.raises(ValueError, match="Decimal odds must be greater than 1.0"):
            remove_vig_decimal([0.5, 2.0])
    
    def test_invalid_odds_empty_list(self):
        """Test that empty odds list raises an error."""
        with pytest.raises(ValueError, match="Odds list cannot be empty"):
            remove_vig_decimal([])
    
    def test_invalid_probability_out_of_range(self):
        """Test that invalid probabilities raise errors."""
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_decimal(0.0)
        
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_decimal(1.0)
        
        with pytest.raises(ValueError, match="Probability must be between 0 and 1"):
            fair_prob_to_decimal(1.5)
    
    def test_invalid_american_odds_zero(self):
        """Test that American odds of 0 raise an error."""
        with pytest.raises(ValueError, match="American odds cannot be 0"):
            american_to_decimal(0)
    
    def test_three_way_market(self):
        """Test vig removal for three-way market (e.g., soccer with draw)."""
        odds = [2.5, 3.4, 3.8]
        fair_probs = remove_vig_decimal(odds)
        
        assert len(fair_probs) == 3
        assert abs(sum(fair_probs) - 1.0) < 0.0001
        assert all(p > 0 for p in fair_probs)
        assert all(p < 1 for p in fair_probs)


class TestCalculateFairOdds:
    
    def test_calculate_fair_odds_even(self):
        """Test fair odds calculation for even odds."""
        odds_data = [
            {'question': 'Team A wins', 'odds': 2.0},
            {'question': 'Team B wins', 'odds': 2.0}
        ]
        result = calculate_fair_odds(odds_data)
        
        assert len(result) == 2
        assert all(isinstance(item, FairOddsResult) for item in result)
        
        # Check all attributes exist
        assert result[0].question == 'Team A wins'
        assert result[0].og_odds == 2.0
        assert result[0].odds_type == OddsType.DECIMAL
        
        # Fair odds should still be 2.0 for even odds with no vig
        assert abs(result[0].fair_odds - 2.0) < 0.0001
        assert abs(result[1].fair_odds - 2.0) < 0.0001
        
        # Implied probabilities should be 0.5 each
        assert abs(result[0].impl_prob - 0.5) < 0.0001
        assert abs(result[1].impl_prob - 0.5) < 0.0001
    
    def test_calculate_fair_odds_with_vig(self):
        """Test fair odds calculation with vig."""
        odds_data = [
            {'question': 'Team A wins', 'odds': 1.83},
            {'question': 'Team B wins', 'odds': 2.2}
        ]
        result = calculate_fair_odds(odds_data)
        
        assert len(result) == 2
        
        # Check structure
        assert result[0].question == 'Team A wins'
        assert result[0].og_odds == 1.83
        assert result[1].question == 'Team B wins'
        assert result[1].og_odds == 2.2
        
        # Fair odds should be higher than original odds (vig removed)
        assert result[0].fair_odds > result[0].og_odds
        assert result[1].fair_odds > result[1].og_odds
        
        # Check approximate fair odds values
        assert abs(result[0].fair_odds - 1.829) < 0.01
        assert abs(result[1].fair_odds - 2.206) < 0.01
        
        # Check implied probabilities
        assert abs(result[0].impl_prob - 0.5468) < 0.001
        assert abs(result[1].impl_prob - 0.4532) < 0.001
    
    def test_calculate_fair_odds_three_way(self):
        """Test fair odds calculation for three-way market."""
        # Using more realistic odds with vig
        odds_data = [
            {'question': 'Home wins', 'odds': 2.3},
            {'question': 'Draw', 'odds': 3.2},
            {'question': 'Away wins', 'odds': 3.5}
        ]
        result = calculate_fair_odds(odds_data)
        
        assert len(result) == 3
        
        # Check that all results are FairOddsResult instances
        for item in result:
            assert isinstance(item, FairOddsResult)
            assert item.odds_type == OddsType.DECIMAL
        
        # Verify probabilities sum to 1
        total_prob = sum(item.impl_prob for item in result)
        assert abs(total_prob - 1.0) < 0.0001
        
        # Check that the structure is preserved
        assert result[0].question == 'Home wins'
        assert result[1].question == 'Draw'
        assert result[2].question == 'Away wins'
        
        # Check original odds are preserved
        assert result[0].og_odds == 2.3
        assert result[1].og_odds == 3.2
        assert result[2].og_odds == 3.5
    
    def test_calculate_fair_odds_empty_list(self):
        """Test that empty odds data raises an error."""
        with pytest.raises(ValueError, match="Odds data cannot be empty"):
            calculate_fair_odds([])
    
    def test_calculate_fair_odds_missing_odds_key(self):
        """Test that missing odds key raises an error."""
        odds_data = [
            {'question': 'Team A wins'},  # Missing 'odds' key
            {'question': 'Team B wins', 'odds': 2.0}
        ]
        with pytest.raises(ValueError, match="Each item must have 'odds' key"):
            calculate_fair_odds(odds_data)
    
    def test_calculate_fair_odds_invalid_odds(self):
        """Test that invalid odds raise an error."""
        odds_data = [
            {'question': 'Team A wins', 'odds': 0.5},  # Invalid odds <= 1.0
            {'question': 'Team B wins', 'odds': 2.0}
        ]
        with pytest.raises(ValueError, match="Decimal odds must be greater than 1.0"):
            calculate_fair_odds(odds_data)