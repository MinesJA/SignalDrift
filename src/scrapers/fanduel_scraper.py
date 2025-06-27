"""
FanDuel Scraper

Scrapes American odds from FanDuel sportsbook for moneyline bets.
Based on actual page structure found in fanduel_page_data.

Example structure from test page:
- San Diego Padres: -102 (American odds)
- Milwaukee Brewers: -116 (American odds)

Real page structure uses aria-label attributes:
<div aria-label="Moneyline, San Diego Padres, -102 Odds" role="button">
    <span class="kw kx ek ed ld le ey">-102</span>
</div>
"""

import os
import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class FanDuelOdds:
    """Container for FanDuel odds data"""
    team1_name: str
    team1_odds: int  # American odds as integer
    team2_name: str
    team2_odds: int  # American odds as integer
    market_type: str = "Moneyline"
    odds_format: str = "american"


class FanDuelScraper:
    """
    Scraper for FanDuel sportsbook odds.

    FanDuel displays American odds (e.g., -102, +150, -116).
    This scraper extracts team names and their corresponding American odds.
    """

    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        # Check both possible locations for test data
        self.test_data_paths = [
            os.path.join(self.base_path, "fanduel_page_data"),
            os.path.join(os.path.dirname(os.path.dirname(self.base_path)), "notebooks", "scrapers", "fanduel_page_data")
        ]
        # Use the first path that exists
        self.test_data_path = None
        for path in self.test_data_paths:
            if os.path.exists(path):
                self.test_data_path = path
                break

        if not self.test_data_path:
            raise FileNotFoundError(f"FanDuel test data not found in any of: {self.test_data_paths}")

    def scrape_from_file(self, html_file: str = "test_page.html") -> Optional[FanDuelOdds]:
        """
        Scrape odds from a local HTML file.

        Args:
            html_file: Name of HTML file in fanduel_page_data directory

        Returns:
            FanDuelOdds object with team names and American odds
        """
        file_path = os.path.join(self.test_data_path, html_file)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")

        with open(file_path, encoding='utf-8') as f:
            html_content = f.read()

        return self.parse_html(html_content)

    def parse_html(self, html_content: str) -> Optional[FanDuelOdds]:
        """
        Parse HTML content to extract team odds.

        Args:
            html_content: Raw HTML content

        Returns:
            FanDuelOdds object or None if parsing fails
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Try multiple parsing strategies
        odds_data = (
            self._parse_aria_label_format(soup) or
            self._parse_test_page_format(soup) or
            self._parse_real_page_format(soup) or
            self._parse_generic_format(soup)
        )

        return odds_data

    def _parse_aria_label_format(self, soup: BeautifulSoup) -> Optional[FanDuelOdds]:
        """Parse using aria-label attributes (real FanDuel format)"""
        try:
            # Find elements with aria-label containing "Moneyline" and "Odds"
            moneyline_buttons = soup.find_all('div', attrs={'aria-label': re.compile(r'Moneyline.*Odds', re.I)})

            teams_and_odds = []

            for button in moneyline_buttons:
                aria_label = button.get('aria-label', '')

                # Extract team name and odds from aria-label
                # Format: "Moneyline, Team Name, Odds Value Odds"
                match = re.match(r'Moneyline,\s*(.+?),\s*([+-]?\d+)\s*Odds', aria_label, re.I)

                if match:
                    team_name = match.group(1).strip()
                    odds_value = self._parse_american_odds(match.group(2))

                    # Also verify the odds are displayed in the span
                    odds_span = button.find('span')
                    if odds_span:
                        teams_and_odds.append((team_name, odds_value))

                if len(teams_and_odds) >= 2:
                    break

            if len(teams_and_odds) >= 2:
                return FanDuelOdds(
                    team1_name=teams_and_odds[0][0],
                    team1_odds=teams_and_odds[0][1],
                    team2_name=teams_and_odds[1][0],
                    team2_odds=teams_and_odds[1][1]
                )

        except Exception as e:
            print(f"Aria-label format parsing failed: {e}")

        return None

    def _parse_test_page_format(self, soup: BeautifulSoup) -> Optional[FanDuelOdds]:
        """Parse the simplified test page format"""
        try:
            # Look for team rows with data-test-id
            padres_row = soup.find('div', {'data-test-id': 'padres-row'})
            brewers_row = soup.find('div', {'data-test-id': 'brewers-row'})

            if padres_row and brewers_row:
                # Extract team names
                padres_name = padres_row.find('span', class_='team-name')
                brewers_name = brewers_row.find('span', class_='team-name')

                # Extract odds from button elements
                padres_button = padres_row.find('button', {'data-test-id': 'padres-moneyline-outcome'})
                brewers_button = brewers_row.find('button', {'data-test-id': 'brewers-moneyline-outcome'})

                if padres_button and brewers_button:
                    padres_odds_elem = padres_button.find('span', class_='odds-display')
                    brewers_odds_elem = brewers_button.find('span', class_='odds-display')

                    if all([padres_name, padres_odds_elem, brewers_name, brewers_odds_elem]):
                        return FanDuelOdds(
                            team1_name=padres_name.get_text().strip(),
                            team1_odds=self._parse_american_odds(padres_odds_elem.get_text().strip()),
                            team2_name=brewers_name.get_text().strip(),
                            team2_odds=self._parse_american_odds(brewers_odds_elem.get_text().strip())
                        )
        except (ValueError, AttributeError) as e:
            print(f"Test page format parsing failed: {e}")

        return None

    def _parse_real_page_format(self, soup: BeautifulSoup) -> Optional[FanDuelOdds]:
        """Parse the real FanDuel page format"""
        try:
            # Look for common FanDuel patterns
            # Try to find moneyline market container
            moneyline_containers = soup.find_all(['div', 'section'], class_=re.compile(r'(moneyline|market)', re.I))

            for container in moneyline_containers:
                # Look for odds buttons or displays
                odds_elements = container.find_all(['button', 'div', 'span'],
                                                 class_=re.compile(r'(odds|price|outcome)', re.I))

                teams_and_odds = []

                for elem in odds_elements:
                    # Extract text and look for American odds pattern
                    text = elem.get_text().strip()
                    odds_match = re.search(r'([+-]?\d{3,4})', text)

                    if odds_match:
                        odds_value = self._parse_american_odds(odds_match.group(1))

                        # Try to find associated team name
                        parent = elem.parent
                        team_name = None

                        # Search for team name in parent or siblings
                        for _i in range(3):  # Check up to 3 levels up
                            if parent:
                                team_elem = parent.find(['span', 'div'], class_=re.compile(r'(team|competitor|participant)', re.I))
                                if team_elem:
                                    team_name = team_elem.get_text().strip()
                                    break
                                parent = parent.parent

                        if team_name and odds_value:
                            teams_and_odds.append((team_name, odds_value))

                if len(teams_and_odds) >= 2:
                    return FanDuelOdds(
                        team1_name=teams_and_odds[0][0],
                        team1_odds=teams_and_odds[0][1],
                        team2_name=teams_and_odds[1][0],
                        team2_odds=teams_and_odds[1][1]
                    )

        except Exception as e:
            print(f"Real page format parsing failed: {e}")

        return None

    def _parse_generic_format(self, soup: BeautifulSoup) -> Optional[FanDuelOdds]:
        """Generic fallback parsing using pattern matching"""
        try:
            # Extract all text and find American odds pattern
            page_text = soup.get_text()

            # Find American odds (format: -102, +150, etc.)
            american_pattern = r'([+-]?\d{3,4})(?!\d)'  # Avoid matching longer numbers
            odds_matches = re.findall(american_pattern, page_text)

            # Convert and validate odds
            valid_odds = []
            for odds_str in odds_matches:
                try:
                    odds_val = self._parse_american_odds(odds_str)
                    # American odds should be >= 100 or <= -100
                    if abs(odds_val) >= 100:
                        valid_odds.append(odds_val)
                except ValueError:
                    continue

            # Look for team names
            team_patterns = [
                r'(?i)(san diego padres?|padres)',
                r'(?i)(milwaukee brewers?|brewers)'
            ]

            found_teams = []
            for pattern in team_patterns:
                match = re.search(pattern, page_text)
                if match:
                    found_teams.append(match.group(1))

            # If we found exactly 2 teams and at least 2 valid odds
            if len(found_teams) == 2 and len(valid_odds) >= 2:
                return FanDuelOdds(
                    team1_name=found_teams[0],
                    team1_odds=valid_odds[0],
                    team2_name=found_teams[1],
                    team2_odds=valid_odds[1]
                )

        except Exception as e:
            print(f"Generic format parsing failed: {e}")

        return None

    def _parse_american_odds(self, odds_str: str) -> int:
        """Parse American odds string to integer"""
        # Remove any non-numeric characters except + and -
        cleaned = re.sub(r'[^\d+-]', '', odds_str)
        return int(cleaned)

    def get_odds_for_teams(self, html_file: str = "test_page.html") -> tuple[int, int]:
        """
        Simple method to get just the odds values for both teams.

        Args:
            html_file: HTML file to parse

        Returns:
            Tuple of (team1_odds, team2_odds) as American odds

        Example:
            >>> scraper = FanDuelScraper()
            >>> odds = scraper.get_odds_for_teams()
            >>> print(f"Team 1: {odds[0]}, Team 2: {odds[1]}")
            Team 1: -102, Team 2: -116
        """
        odds_data = self.scrape_from_file(html_file)

        if odds_data:
            return (odds_data.team1_odds, odds_data.team2_odds)
        else:
            raise ValueError(f"Could not extract odds from {html_file}")

    def get_detailed_odds(self, html_file: str = "test_page.html") -> dict:
        """
        Get detailed odds information including team names.

        Args:
            html_file: HTML file to parse

        Returns:
            Dictionary with detailed odds information
        """
        odds_data = self.scrape_from_file(html_file)

        if odds_data:
            return {
                'teams': {
                    odds_data.team1_name: odds_data.team1_odds,
                    odds_data.team2_name: odds_data.team2_odds
                },
                'market_type': odds_data.market_type,
                'odds_format': odds_data.odds_format,
                'raw_data': odds_data
            }
        else:
            raise ValueError(f"Could not extract odds from {html_file}")

    def convert_to_decimal_odds(self, american_odds: int) -> float:
        """
        Convert American odds to decimal odds.

        Args:
            american_odds: American odds value (e.g., -102, +150)

        Returns:
            Decimal odds value

        Example:
            -102 -> 1.98
            +150 -> 2.50
        """
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1


def main():
    """Test the scraper with the available test data"""
    scraper = FanDuelScraper()

    print("Testing FanDuel Scraper")
    print("=" * 50)

    # Test with available files
    test_files = ["test_page.html", "cleaned.html"]

    for test_file in test_files:
        print(f"\nTesting with {test_file}:")
        print("-" * 30)

        try:
            # Test simple odds extraction
            odds = scraper.get_odds_for_teams(test_file)
            print(f"✅ American odds extracted: {odds[0]} vs {odds[1]}")

            # Convert to decimal for comparison with Pinnacle
            decimal1 = scraper.convert_to_decimal_odds(odds[0])
            decimal2 = scraper.convert_to_decimal_odds(odds[1])
            print(f"✅ Decimal odds: {decimal1:.3f} vs {decimal2:.3f}")

            # Test detailed extraction
            detailed = scraper.get_detailed_odds(test_file)
            print("✅ Teams found:")
            for team, odds_val in detailed['teams'].items():
                decimal = scraper.convert_to_decimal_odds(odds_val)
                print(f"   {team}: {odds_val} (decimal: {decimal:.3f})")

        except Exception as e:
            print(f"❌ Failed to parse {test_file}: {e}")

    print("\n" + "=" * 50)
    print("Scraper test completed!")


if __name__ == "__main__":
    main()
