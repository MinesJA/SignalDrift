"""
Tests for FanDuel Scraper
"""

import os

import pytest

from src.scrapers.fanduel_scraper import FanDuelOdds, FanDuelScraper


class TestFanDuelScraper:
    """Test suite for FanDuel scraper"""

    @pytest.fixture
    def scraper(self):
        """Create a FanDuel scraper instance"""
        return FanDuelScraper()

    def test_scraper_initialization(self, scraper):
        """Test that scraper initializes correctly"""
        assert scraper is not None
        assert scraper.test_data_path is not None
        assert os.path.exists(scraper.test_data_path)

    def test_parse_test_page(self, scraper):
        """Test parsing the test page HTML"""
        odds_data = scraper.scrape_from_file("test_page.html")

        assert odds_data is not None
        assert isinstance(odds_data, FanDuelOdds)
        assert odds_data.team1_name == "San Diego Padres"
        assert odds_data.team2_name == "Milwaukee Brewers"
        assert odds_data.team1_odds == -102
        assert odds_data.team2_odds == -116
        assert odds_data.market_type == "Moneyline"
        assert odds_data.odds_format == "american"

    def test_get_odds_for_teams(self, scraper):
        """Test simple odds extraction"""
        team1_odds, team2_odds = scraper.get_odds_for_teams("test_page.html")

        assert team1_odds == -102
        assert team2_odds == -116

    def test_get_detailed_odds(self, scraper):
        """Test detailed odds extraction"""
        detailed = scraper.get_detailed_odds("test_page.html")

        assert "teams" in detailed
        assert "San Diego Padres" in detailed["teams"]
        assert "Milwaukee Brewers" in detailed["teams"]
        assert detailed["teams"]["San Diego Padres"] == -102
        assert detailed["teams"]["Milwaukee Brewers"] == -116
        assert detailed["market_type"] == "Moneyline"
        assert detailed["odds_format"] == "american"

    def test_nonexistent_file(self, scraper):
        """Test handling of non-existent file"""
        with pytest.raises(FileNotFoundError):
            scraper.scrape_from_file("nonexistent.html")

    def test_american_to_decimal_conversion(self, scraper):
        """Test conversion from American to decimal odds"""
        # Test negative American odds
        assert scraper.convert_to_decimal_odds(-102) == pytest.approx(1.98, rel=0.01)
        assert scraper.convert_to_decimal_odds(-116) == pytest.approx(1.862, rel=0.01)
        assert scraper.convert_to_decimal_odds(-200) == 1.5

        # Test positive American odds
        assert scraper.convert_to_decimal_odds(150) == 2.5
        assert scraper.convert_to_decimal_odds(200) == 3.0
        assert scraper.convert_to_decimal_odds(548) == 6.48

    def test_parse_american_odds(self, scraper):
        """Test parsing American odds strings"""
        assert scraper._parse_american_odds("-102") == -102
        assert scraper._parse_american_odds("+150") == 150
        assert scraper._parse_american_odds("200") == 200
        assert scraper._parse_american_odds("-116") == -116

    def test_american_odds_validation(self, scraper):
        """Test that American odds are valid"""
        odds_data = scraper.scrape_from_file("test_page.html")

        # American odds should be >= 100 or <= -100
        assert abs(odds_data.team1_odds) >= 100
        assert abs(odds_data.team2_odds) >= 100

    def test_parse_html_with_invalid_content(self, scraper):
        """Test parsing HTML with no valid odds data"""
        invalid_html = "<html><body>No odds here</body></html>"
        result = scraper.parse_html(invalid_html)

        assert result is None

    def test_parse_aria_label_format(self, scraper):
        """Test parsing aria-label format (real FanDuel structure)"""
        from bs4 import BeautifulSoup

        html = '''
        <div aria-label="Moneyline, San Diego Padres, -102 Odds" role="button">
            <span>-102</span>
        </div>
        <div aria-label="Moneyline, Milwaukee Brewers, -116 Odds" role="button">
            <span>-116</span>
        </div>
        '''

        soup = BeautifulSoup(html, 'html.parser')
        result = scraper._parse_aria_label_format(soup)

        assert result is not None
        assert result.team1_name == "San Diego Padres"
        assert result.team1_odds == -102
        assert result.team2_name == "Milwaukee Brewers"
        assert result.team2_odds == -116

    def test_parse_cleaned_html(self, scraper):
        """Test parsing the cleaned.html file if it exists"""
        cleaned_path = os.path.join(scraper.test_data_path, "cleaned.html")
        if os.path.exists(cleaned_path):
            odds_data = scraper.scrape_from_file("cleaned.html")

            # Should parse successfully
            assert odds_data is not None
            assert isinstance(odds_data, FanDuelOdds)
            assert abs(odds_data.team1_odds) >= 100
            assert abs(odds_data.team2_odds) >= 100

    def test_edge_cases(self, scraper):
        """Test edge cases for American odds"""
        # Test even money (-100/+100)
        assert scraper.convert_to_decimal_odds(-100) == 2.0
        assert scraper.convert_to_decimal_odds(100) == 2.0

        # Test heavy favorites
        assert scraper.convert_to_decimal_odds(-1000) == pytest.approx(1.1, rel=0.01)

        # Test heavy underdogs
        assert scraper.convert_to_decimal_odds(1000) == 11.0
