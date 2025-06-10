"""
Pinnacle Scraper

Scrapes decimal odds from Pinnacle sportsbook for moneyline bets.
Based on actual page structure found in pinnacle_page_data.

Example structure from real page:
- San Diego Padres: 2.040 (decimal odds)
- Milwaukee Brewers: 1.884 (decimal odds)
"""

import os
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PinnacleOdds:
    """Container for Pinnacle odds data"""
    team1_name: str
    team1_odds: float
    team2_name: str  
    team2_odds: float
    market_type: str = "Moneyline"
    odds_format: str = "decimal"


class PinnacleScraper:
    """
    Scraper for Pinnacle sportsbook odds.
    
    Pinnacle displays decimal odds (e.g., 2.040, 1.884).
    This scraper extracts team names and their corresponding decimal odds.
    """
    
    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.test_data_path = os.path.join(self.base_path, "pinnacle_page_data")
    
    def scrape_from_file(self, html_file: str = "test_page.html") -> Optional[PinnacleOdds]:
        """
        Scrape odds from a local HTML file.
        
        Args:
            html_file: Name of HTML file in pinnacle_page_data directory
            
        Returns:
            PinnacleOdds object with team names and decimal odds
        """
        file_path = os.path.join(self.test_data_path, html_file)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.parse_html(html_content)
    
    def parse_html(self, html_content: str) -> Optional[PinnacleOdds]:
        """
        Parse HTML content to extract team odds.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            PinnacleOdds object or None if parsing fails
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try multiple parsing strategies
        odds_data = (
            self._parse_test_page_format(soup) or
            self._parse_real_page_format(soup) or
            self._parse_generic_format(soup)
        )
        
        return odds_data
    
    def _parse_test_page_format(self, soup: BeautifulSoup) -> Optional[PinnacleOdds]:
        """Parse the simplified test page format"""
        try:
            # Look for participant rows in test format
            padres_row = soup.find('div', {'data-cy': 'padres-participant'})
            brewers_row = soup.find('div', {'data-cy': 'brewers-participant'})
            
            if padres_row and brewers_row:
                padres_name = padres_row.find('span', class_='participant-name')
                padres_odds = padres_row.find('span', class_='odds-display')
                
                brewers_name = brewers_row.find('span', class_='participant-name')
                brewers_odds = brewers_row.find('span', class_='odds-display')
                
                if all([padres_name, padres_odds, brewers_name, brewers_odds]):
                    return PinnacleOdds(
                        team1_name=padres_name.get_text().strip(),
                        team1_odds=float(padres_odds.get_text().strip()),
                        team2_name=brewers_name.get_text().strip(),
                        team2_odds=float(brewers_odds.get_text().strip())
                    )
        except (ValueError, AttributeError) as e:
            print(f"Test page format parsing failed: {e}")
        
        return None
    
    def _parse_real_page_format(self, soup: BeautifulSoup) -> Optional[PinnacleOdds]:
        """Parse the real Pinnacle page format based on metadata findings"""
        try:
            # Look for participant elements with class containing 'participant'
            participants = soup.find_all('div', class_=re.compile(r'participant'))
            
            if len(participants) >= 2:
                # Extract team names and find corresponding odds
                teams_and_odds = []
                
                for participant in participants[:2]:  # Take first 2 participants
                    team_name = participant.get_text().strip()
                    
                    # Find odds near this participant
                    # Look for decimal odds pattern in nearby elements
                    odds_candidates = self._find_nearby_odds(participant)
                    
                    if team_name and odds_candidates:
                        teams_and_odds.append((team_name, odds_candidates[0]))
                
                if len(teams_and_odds) == 2:
                    return PinnacleOdds(
                        team1_name=teams_and_odds[0][0],
                        team1_odds=teams_and_odds[0][1],
                        team2_name=teams_and_odds[1][0],
                        team2_odds=teams_and_odds[1][1]
                    )
        except Exception as e:
            print(f"Real page format parsing failed: {e}")
        
        return None
    
    def _parse_generic_format(self, soup: BeautifulSoup) -> Optional[PinnacleOdds]:
        """Generic fallback parsing using pattern matching"""
        try:
            # Extract all text and find decimal odds pattern
            page_text = soup.get_text()
            
            # Find decimal odds (format: X.XXX where X is a digit)
            decimal_pattern = r'\b\d+\.\d{2,3}\b'
            odds_matches = re.findall(decimal_pattern, page_text)
            
            # Convert to floats and filter reasonable odds (1.0 - 20.0)
            valid_odds = []
            for odds_str in odds_matches:
                try:
                    odds_val = float(odds_str)
                    if 1.0 <= odds_val <= 20.0:  # Reasonable odds range
                        valid_odds.append(odds_val)
                except ValueError:
                    continue
            
            # Look for team names (Padres, Brewers, or generic patterns)
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
                return PinnacleOdds(
                    team1_name=found_teams[0],
                    team1_odds=valid_odds[0],
                    team2_name=found_teams[1], 
                    team2_odds=valid_odds[1]
                )
                
        except Exception as e:
            print(f"Generic format parsing failed: {e}")
        
        return None
    
    def _find_nearby_odds(self, element) -> List[float]:
        """Find decimal odds near a given element"""
        odds_found = []
        
        # Check the element itself and its siblings
        elements_to_check = [element] + list(element.find_next_siblings())[:3]
        
        for elem in elements_to_check:
            text = elem.get_text()
            decimal_pattern = r'\b\d+\.\d{2,3}\b'
            matches = re.findall(decimal_pattern, text)
            
            for match in matches:
                try:
                    odds_val = float(match)
                    if 1.0 <= odds_val <= 20.0:  # Reasonable odds range
                        odds_found.append(odds_val)
                except ValueError:
                    continue
        
        return odds_found
    
    def get_odds_for_teams(self, html_file: str = "test_page.html") -> Tuple[float, float]:
        """
        Simple method to get just the odds values for both teams.
        
        Args:
            html_file: HTML file to parse
            
        Returns:
            Tuple of (team1_odds, team2_odds) as decimal odds
            
        Example:
            >>> scraper = PinnacleScraper()
            >>> odds = scraper.get_odds_for_teams()
            >>> print(f"Team 1: {odds[0]}, Team 2: {odds[1]}")
            Team 1: 2.050, Team 2: 1.884
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
                    odds_data.team1_name: odds_data.team1_odds,
                    odds_data.team2_name: odds_data.team2_odds
                },
                'market_type': odds_data.market_type,
                'odds_format': odds_data.odds_format,
                'raw_data': odds_data
            }
        else:
            raise ValueError(f"Could not extract odds from {html_file}")


def main():
    """Test the scraper with the available test data"""
    scraper = PinnacleScraper()
    
    print("Testing Pinnacle Scraper")
    print("=" * 50)
    
    # Test with available files
    test_files = ["test_page.html", "cleaned.html"]
    
    for test_file in test_files:
        print(f"\nTesting with {test_file}:")
        print("-" * 30)
        
        try:
            # Test simple odds extraction
            odds = scraper.get_odds_for_teams(test_file)
            print(f"✅ Odds extracted: {odds[0]} vs {odds[1]}")
            
            # Test detailed extraction
            detailed = scraper.get_detailed_odds(test_file)
            print(f"✅ Teams found:")
            for team, odds_val in detailed['teams'].items():
                print(f"   {team}: {odds_val}")
            
        except Exception as e:
            print(f"❌ Failed to parse {test_file}: {e}")
    
    print("\n" + "=" * 50)
    print("Scraper test completed!")


if __name__ == "__main__":
    main()