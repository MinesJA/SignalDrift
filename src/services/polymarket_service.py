import requests
import json
from datetime import datetime
from typing import Dict, Optional, Any, List
import logging
from src.config import config
from src.models import OrderType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymarketService:
    def __init__(self):
        self.gamma_api_base = config.POLYMARKET_GAMMA_API
        self.clob_api_base = config.POLYMARKET_CLOB_API if hasattr(config, 'POLYMARKET_CLOB_API') else "https://clob.polymarket.com"
        self.headers = {}

        # WebSocket connection state
        self.websocket = None
        self.is_connected = False
        self.subscribed_assets = set()
        self.event_handlers = {
            "book": [],
            "price_change": [],
            "order_update": []
        }

        # Add authentication headers if tokens are configured
        if config.POLYMARKET_PRIVY_TOKEN:
            self.headers['privy-token'] = config.POLYMARKET_PRIVY_TOKEN
        if config.POLYMARKET_PRIVY_ID_TOKEN:
            self.headers['privy-id-token'] = config.POLYMARKET_PRIVY_ID_TOKEN

    def fetch_current_price(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current market price for two teams given a slug.

        Args:
            slug: Market slug, e.g., 'mlb-sd-mil-2025-06-08'

        Returns:
            Dictionary containing:
            - team_name_a: float (price)
            - team_name_b: float (price)
            - fetched_at: datetime (time request was made)
            - updated_at: datetime (from request)
        """
        fetched_at = datetime.now()

        try:
            # Get market information using Gamma API
            market = self.get_market_by_slug(slug)
            if not market:
                logger.error(f"No market found for slug: {slug}")
                return None

            # Extract market data
            outcomes = json.loads(market.get('outcomes', '[]'))
            outcome_prices = json.loads(market.get('outcomePrices', '[]'))

            if len(outcomes) != 2 or len(outcome_prices) != 2:
                logger.error(f"Invalid market data: expected 2 outcomes, got {len(outcomes)}")
                return None

            # Get current prices from market data
            team_a, team_b = outcomes[0], outcomes[1]
            price_a, price_b = float(outcome_prices[0]), float(outcome_prices[1])

            # Get updated_at time from market data
            updated_at_str = market.get('updatedAt', '')
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))

            result = {
                team_a: price_a,
                team_b: price_b,
                'fetched_at': fetched_at,
                'updated_at': updated_at
            }

            logger.info(f"Successfully fetched prices for {slug}: {team_a}={price_a}, {team_b}={price_b}")
            return result

        except Exception as e:
            logger.error(f"Error fetching prices for {slug}: {e}")
            return None

    def get_market_by_slug(self, market_slug: str) -> Optional[Dict[str, Any]]:
        """Get market information using the Gamma API."""
        try:
            url = f"{self.gamma_api_base}/markets"
            params = {
                'slug': market_slug,
                'active': True,
                'closed': False
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            markets = response.json()

            if not markets:
                return None

            return markets[0]  # Return the first matching market

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching market data: {e}")
            return None

