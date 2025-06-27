"""
Tests for Pinnacle Scraper
"""

import os

import pytest

from src.scrapers.pinnacle_scraper import PinnacleOdds, PinnacleScraper


class TestPinnacleScraper:
    """Test suite for Pinnacle scraper"""

    @pytest.fixture
    def scraper(self):
        """Create a Pinnacle scraper instance"""
        return PinnacleScraper()

    def test_scraper_initialization(self, scraper):
        """Test that scraper initializes correctly"""
        assert scraper is not None
        assert os.path.exists(scraper.test_data_path)

    def test_parse_test_page(self, scraper):
        """Test parsing the test page HTML"""
        odds_data = scraper.scrape_from_file("test_page.html")

        assert odds_data is not None
        assert isinstance(odds_data, PinnacleOdds)
        assert odds_data.team1_name == "San Diego Padres"
        assert odds_data.team2_name == "Milwaukee Brewers"
        assert odds_data.team1_odds == 2.050
        assert odds_data.team2_odds == 1.884
        assert odds_data.market_type == "Moneyline"
        assert odds_data.odds_format == "decimal"

    def test_get_odds_for_teams(self, scraper):
        """Test simple odds extraction"""
        team1_odds, team2_odds = scraper.get_odds_for_teams("test_page.html")

        assert team1_odds == 2.050
        assert team2_odds == 1.884

    def test_get_detailed_odds(self, scraper):
        """Test detailed odds extraction"""
        detailed = scraper.get_detailed_odds("test_page.html")

        assert "teams" in detailed
        assert "San Diego Padres" in detailed["teams"]
        assert "Milwaukee Brewers" in detailed["teams"]
        assert detailed["teams"]["San Diego Padres"] == 2.050
        assert detailed["teams"]["Milwaukee Brewers"] == 1.884
        assert detailed["market_type"] == "Moneyline"
        assert detailed["odds_format"] == "decimal"

    def test_nonexistent_file(self, scraper):
        """Test handling of non-existent file"""
        with pytest.raises(FileNotFoundError):
            scraper.scrape_from_file("nonexistent.html")

    def test_parse_cleaned_html(self, scraper):
        """Test parsing the cleaned.html file if it exists"""
        cleaned_path = os.path.join(scraper.test_data_path, "cleaned.html")
        if os.path.exists(cleaned_path):
            odds_data = scraper.scrape_from_file("cleaned.html")

            # Should parse successfully even if different teams
            assert odds_data is not None
            assert isinstance(odds_data, PinnacleOdds)
            assert odds_data.team1_odds > 1.0
            assert odds_data.team2_odds > 1.0

    def test_decimal_odds_validation(self, scraper):
        """Test that decimal odds are in valid range"""
        odds_data = scraper.scrape_from_file("test_page.html")

        # Decimal odds should be >= 1.0
        assert odds_data.team1_odds >= 1.0
        assert odds_data.team2_odds >= 1.0

        # Reasonable upper bound for testing
        assert odds_data.team1_odds <= 20.0
        assert odds_data.team2_odds <= 20.0

    def test_parse_html_with_invalid_content(self, scraper):
        """Test parsing HTML with no valid odds data"""
        invalid_html = "<html><body>No odds here</body></html>"
        result = scraper.parse_html(invalid_html)

        assert result is None

    def test_find_nearby_odds(self, scraper):
        """Test the _find_nearby_odds helper method"""
        from bs4 import BeautifulSoup

        html = '<div><span>Team Name</span><span>2.050</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('span')

        odds = scraper._find_nearby_odds(element)
        assert 2.050 in odds
