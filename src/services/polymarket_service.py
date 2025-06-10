import requests
import json
from datetime import datetime
from typing import Dict, Optional, Any, Literal
import logging
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from ..config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymarketService:
    def __init__(self, private_key: Optional[str] = None):
        self.gamma_api_base = config.POLYMARKET_GAMMA_API
        self.clob_api_base = config.POLYMARKET_CLOB_API
        self.headers = {}
        
        # Add authentication headers if tokens are configured
        if config.POLYMARKET_PRIVY_TOKEN:
            self.headers['privy-token'] = config.POLYMARKET_PRIVY_TOKEN
        if config.POLYMARKET_PRIVY_ID_TOKEN:
            self.headers['privy-id-token'] = config.POLYMARKET_PRIVY_ID_TOKEN
            
        # Initialize CLOB client for trading operations
        self.clob_client = None
        if private_key:
            try:
                self.clob_client = ClobClient(
                    host=self.clob_api_base,
                    key=private_key,
                    chain_id=POLYGON
                )
            except Exception as e:
                logger.error(f"Failed to initialize CLOB client: {e}")
                self.clob_client = None
        
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
            market = self._get_market_by_slug(slug)
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
    
    def _get_market_by_slug(self, market_slug: str) -> Optional[Dict[str, Any]]:
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
    
    def place_order(
        self,
        token_id: str,
        side: Literal["BUY", "SELL"],
        size: float,
        price: float,
        price_type: Literal["price", "tick"] = "price"
    ) -> Optional[Dict[str, Any]]:
        """
        Place a single trade order on Polymarket.
        
        Args:
            token_id: The token ID for the market outcome to trade
            side: Whether to BUY or SELL the outcome
            size: The size/amount to trade (in USDC for BUY, in shares for SELL)
            price: The limit price (0.0 to 1.0) or tick value
            price_type: Whether price is a decimal price or tick value
            
        Returns:
            Dictionary containing order response or None if failed
        """
        if not self.clob_client:
            logger.error("CLOB client not initialized. Private key required for trading.")
            return None
            
        try:
            # Validate inputs
            if side not in ["BUY", "SELL"]:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
                
            if price_type == "price" and not (0.0 <= price <= 1.0):
                raise ValueError(f"Price must be between 0.0 and 1.0, got {price}")
                
            if size <= 0:
                raise ValueError(f"Size must be positive, got {size}")
            
            # Create the order using the CLOB client
            order_args = {
                "token_id": token_id,
                "side": side,
                "size": str(size),
            }
            
            # Add price argument based on price_type
            if price_type == "price":
                order_args["price"] = str(price)
            else:  # tick
                order_args["tick_size"] = str(price)
            
            logger.info(f"Placing {side} order: {size} @ {price} for token {token_id}")
            
            # Place the order
            order_response = self.clob_client.create_order(**order_args)
            
            if order_response and hasattr(order_response, 'order_id'):
                logger.info(f"Order placed successfully. Order ID: {order_response.order_id}")
                return {
                    "order_id": order_response.order_id,
                    "token_id": token_id,
                    "side": side,
                    "size": size,
                    "price": price,
                    "price_type": price_type,
                    "status": "placed",
                    "timestamp": datetime.now()
                }
            else:
                logger.error(f"Order placement failed: {order_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None


# Create a module-level instance for convenience
_service = PolymarketService()
fetch_current_price = _service.fetch_current_price
