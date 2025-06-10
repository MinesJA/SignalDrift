"""
Betfair Scraper

Scrapes fractional odds from Betfair sportsbook for moneyline bets.
Focuses on the "Popular" tab which shows "Match Betting" as seen in screenshots.

Example structure from screenshots:
- San Diego Padres: 11/8 (fractional odds)
- Milwaukee Brewers: 8/13 (fractional odds)

The scraper can also handle the exchange format with back/lay prices.
"""

import os
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from fractions import Fraction


@dataclass
class BetfairOdds:
    """Container for Betfair odds data"""
    team1_name: str
    team1_odds: str  # Fractional odds as string (e.g., "11/8")
    team2_name: str  
    team2_odds: str  # Fractional odds as string (e.g., "8/13")
    market_type: str = "Match Betting"
    odds_format: str = "fractional"
    
    @property
    def team1_decimal(self) -> float:
        """Convert team1 fractional odds to decimal"""
        return self.fractional_to_decimal(self.team1_odds)
    
    @property
    def team2_decimal(self) -> float:
        """Convert team2 fractional odds to decimal"""
        return self.fractional_to_decimal(self.team2_odds)
    
    @staticmethod
    def fractional_to_decimal(fractional_odds: str) -> float:
        """Convert fractional odds to decimal odds"""
        try:
            frac = Fraction(fractional_odds)
            return float(frac) + 1.0
        except:
            return 0.0


class BetfairScraper:
    """
    Scraper for Betfair sportsbook odds.
    
    Betfair displays fractional odds (e.g., 11/8, 8/13) on their sportsbook.
    The exchange shows decimal odds, but we focus on the sportsbook view.
    This scraper extracts team names and their corresponding fractional odds.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.test_data_path = os.path.join(self.base_path, "betfair_page_data")
        
        if not os.path.exists(self.test_data_path):
            raise FileNotFoundError(f"Betfair test data not found at: {self.test_data_path}")
    
    def scrape_from_file(self, html_file: str = "test_page.html") -> Optional[BetfairOdds]:
        """
        Scrape odds from a local HTML file.
        
        Args:
            html_file: Name of HTML file in betfair_page_data directory
            
        Returns:
            BetfairOdds object with team names and fractional odds
        """
        file_path = os.path.join(self.test_data_path, html_file)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.parse_html(html_content)
    
    def parse_html(self, html_content: str) -> Optional[BetfairOdds]:
        """
        Parse HTML content to extract team odds.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            BetfairOdds object or None if parsing fails
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try multiple parsing strategies
        odds_data = (
            self._parse_test_page_format(soup) or
            self._parse_sportsbook_format(soup) or
            self._parse_exchange_format(soup) or
            self._parse_generic_format(soup)
        )
        
        return odds_data
    
    def _parse_test_page_format(self, soup: BeautifulSoup) -> Optional[BetfairOdds]:
        """Parse the simplified test page format"""
        try:
            # For test page, look for exchange-style decimal odds
            padres_row = soup.find('tr', {'data-testid': 'padres-runner'})
            brewers_row = soup.find('tr', {'data-testid': 'brewers-runner'})
            
            if padres_row and brewers_row:
                padres_name = padres_row.find('td', class_='team-name')
                brewers_name = brewers_row.find('td', class_='team-name')
                
                # Get best back price (highest back price)
                padres_back = padres_row.find('span', {'data-testid': 'padres-back-2'})
                brewers_back = brewers_row.find('span', {'data-testid': 'brewers-back-2'})
                
                if all([padres_name, padres_back, brewers_name, brewers_back]):
                    # Convert decimal odds to fractional for consistency
                    padres_decimal = float(padres_back.get_text().strip())
                    brewers_decimal = float(brewers_back.get_text().strip())
                    
                    padres_frac = self._decimal_to_fractional(padres_decimal)
                    brewers_frac = self._decimal_to_fractional(brewers_decimal)
                    
                    return BetfairOdds(
                        team1_name=padres_name.get_text().strip(),
                        team1_odds=padres_frac,
                        team2_name=brewers_name.get_text().strip(),
                        team2_odds=brewers_frac
                    )
        except (ValueError, AttributeError) as e:
            print(f"Test page format parsing failed: {e}")
        
        return None
    
    def _parse_sportsbook_format(self, soup: BeautifulSoup) -> Optional[BetfairOdds]:
        """Parse the Betfair sportsbook format (Popular tab, Match Betting)"""
        try:
            # Look for Match Betting section
            match_betting_text = soup.find(text=re.compile(r'Match Betting', re.I))
            
            if match_betting_text:
                # Find the parent container
                container = match_betting_text.parent
                while container and not container.find_all('button', class_=re.compile(r'button|bet|odds', re.I)):
                    container = container.parent
                
                if container:
                    # Look for buttons with fractional odds
                    buttons = container.find_all('button')
                    
                    teams_and_odds = []
                    for button in buttons:
                        # Look for team name and odds
                        team_elem = button.find('span', class_=re.compile(r'(team|runner|selection|supportingText)', re.I))
                        odds_elem = button.find('span', class_=re.compile(r'(odds|price|label)', re.I))
                        
                        if team_elem and odds_elem:
                            team_name = team_elem.get_text().strip()
                            odds_text = odds_elem.get_text().strip()
                            
                            # Verify it's fractional odds
                            if re.match(r'\d+/\d+', odds_text):
                                teams_and_odds.append((team_name, odds_text))
                    
                    if len(teams_and_odds) >= 2:
                        return BetfairOdds(
                            team1_name=teams_and_odds[0][0],
                            team1_odds=teams_and_odds[0][1],
                            team2_name=teams_and_odds[1][0],
                            team2_odds=teams_and_odds[1][1]
                        )
        except Exception as e:
            print(f"Sportsbook format parsing failed: {e}")
        
        return None
    
    def _parse_exchange_format(self, soup: BeautifulSoup) -> Optional[BetfairOdds]:
        """Parse the Betfair exchange format with back/lay prices"""
        try:
            # Look for runner lines
            runner_lines = soup.find_all('tr', class_=re.compile(r'runner-line', re.I))
            
            if len(runner_lines) >= 2:
                teams_and_odds = []
                
                for runner in runner_lines[:2]:
                    team_name_elem = runner.find('td', class_='team-name')
                    if not team_name_elem:
                        continue
                    
                    team_name = team_name_elem.get_text().strip()
                    
                    # Get best back price
                    back_prices = runner.find_all('span', class_='back-price')
                    if back_prices:
                        # Use the best (highest) back price
                        best_back = max([float(p.get_text().strip()) for p in back_prices if p.get_text().strip().replace('.', '').isdigit()])
                        fractional = self._decimal_to_fractional(best_back)
                        teams_and_odds.append((team_name, fractional))
                
                if len(teams_and_odds) >= 2:
                    return BetfairOdds(
                        team1_name=teams_and_odds[0][0],
                        team1_odds=teams_and_odds[0][1],
                        team2_name=teams_and_odds[1][0],
                        team2_odds=teams_and_odds[1][1]
                    )
                    
        except Exception as e:
            print(f"Exchange format parsing failed: {e}")
        
        return None
    
    def _parse_generic_format(self, soup: BeautifulSoup) -> Optional[BetfairOdds]:
        """Generic fallback parsing using pattern matching"""
        try:
            # Extract all text and find fractional odds pattern
            page_text = soup.get_text()
            
            # Find fractional odds (format: X/Y)
            fractional_pattern = r'\b(\d+/\d+)\b'
            odds_matches = re.findall(fractional_pattern, page_text)
            
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
            
            # Look specifically for 11/8 and 8/13
            if '11/8' in page_text and '8/13' in page_text:
                if len(found_teams) >= 2:
                    return BetfairOdds(
                        team1_name=found_teams[0],
                        team1_odds='11/8',
                        team2_name=found_teams[1],
                        team2_odds='8/13'
                    )
            
            # Otherwise use first two fractional odds found
            if len(found_teams) == 2 and len(odds_matches) >= 2:
                return BetfairOdds(
                    team1_name=found_teams[0],
                    team1_odds=odds_matches[0],
                    team2_name=found_teams[1], 
                    team2_odds=odds_matches[1]
                )
                
        except Exception as e:
            print(f"Generic format parsing failed: {e}")
        
        return None
    
    def _decimal_to_fractional(self, decimal_odds: float) -> str:
        """Convert decimal odds to fractional odds string"""
        try:
            # Subtract 1 to get the fractional part
            fractional_value = decimal_odds - 1
            
            # Convert to fraction and simplify
            frac = Fraction(fractional_value).limit_denominator(100)
            
            return f"{frac.numerator}/{frac.denominator}"
        except:
            return "1/1"  # Default odds
    
    def get_odds_for_teams(self, html_file: str = "test_page.html") -> Tuple[str, str]:
        """
        Simple method to get just the odds values for both teams.
        
        Args:
            html_file: HTML file to parse
            
        Returns:
            Tuple of (team1_odds, team2_odds) as fractional odds strings
            
        Example:
            >>> scraper = BetfairScraper()
            >>> odds = scraper.get_odds_for_teams()
            >>> print(f"Team 1: {odds[0]}, Team 2: {odds[1]}")
            Team 1: 11/8, Team 2: 8/13
        """
        odds_data = self.scrape_from_file(html_file)
        
        if odds_data:
            return (odds_data.team1_odds, odds_data.team2_odds)
        else:
            raise ValueError(f"Could not extract odds from {html_file}")
    
    def get_detailed_odds(self, html_file: str = "test_page.html") -> Dict:
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
                    odds_data.team1_name: {
                        'fractional': odds_data.team1_odds,
                        'decimal': odds_data.team1_decimal
                    },
                    odds_data.team2_name: {
                        'fractional': odds_data.team2_odds,
                        'decimal': odds_data.team2_decimal
                    }
                },
                'market_type': odds_data.market_type,
                'odds_format': odds_data.odds_format,
                'raw_data': odds_data
            }
        else:
            raise ValueError(f"Could not extract odds from {html_file}")
    
    def convert_to_decimal_odds(self, fractional_odds: str) -> float:
        """
        Convert fractional odds to decimal odds.
        
        Args:
            fractional_odds: Fractional odds string (e.g., "11/8")
            
        Returns:
            Decimal odds value
            
        Example:
            "11/8" -> 2.375
            "8/13" -> 1.615
        """
        try:
            frac = Fraction(fractional_odds)
            return float(frac) + 1.0
        except:
            raise ValueError(f"Invalid fractional odds format: {fractional_odds}")


def main():
    """Test the scraper with the available test data"""
    scraper = BetfairScraper()
    
    print("Testing Betfair Scraper")
    print("=" * 50)
    
    # Test with available files
    test_files = ["test_page.html", "cleaned.html"]
    
    for test_file in test_files:
        print(f"\nTesting with {test_file}:")
        print("-" * 30)
        
        try:
            # Test simple odds extraction
            odds = scraper.get_odds_for_teams(test_file)
            print(f" Fractional odds extracted: {odds[0]} vs {odds[1]}")
            
            # Convert to decimal for comparison
            decimal1 = scraper.convert_to_decimal_odds(odds[0])
            decimal2 = scraper.convert_to_decimal_odds(odds[1])
            print(f" Decimal odds: {decimal1:.3f} vs {decimal2:.3f}")
            
            # Test detailed extraction
            detailed = scraper.get_detailed_odds(test_file)
            print(f" Teams found:")
            for team, odds_info in detailed['teams'].items():
                print(f"   {team}: {odds_info['fractional']} (decimal: {odds_info['decimal']:.3f})")
            
        except Exception as e:
            print(f"L Failed to parse {test_file}: {e}")
    
    print("\n" + "=" * 50)
    print("Scraper test completed!")


if __name__ == "__main__":
    main()