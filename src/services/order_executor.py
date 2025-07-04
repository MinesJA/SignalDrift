"""
Order execution service for SignalDrift.

This module provides a high-level interface for executing trading orders
across different platforms, starting with Polymarket.
"""

from typing import List, Dict, Any, Optional
import logging
from src.models import Order
from services.polymarket_batch_order import PolymarketOrderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    High-level order execution service.
    
    Handles execution of Order objects across different trading platforms.
    Currently supports Polymarket with plans to expand to other platforms.
    """
    
    def __init__(self):
        """Initialize the order executor with available services."""
        self.polymarket_service = None
        
        # Try to initialize Polymarket service
        try:
            self.polymarket_service = PolymarketOrderService()
            logger.info("Polymarket order service initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Polymarket service: {e}")
    
    def execute_polymarket_orders(self, orders: List[Order], neg_risk: bool = True) -> Dict[str, Any]:
        """
        Execute orders on Polymarket.
        
        Args:
            orders: List of Order objects to execute
            neg_risk: Whether this is a negative risk market (binary yes/no)
            
        Returns:
            Execution results summary
            
        Raises:
            RuntimeError: If Polymarket service is not available
        """
        if not self.polymarket_service:
            raise RuntimeError("Polymarket service is not available. Check environment variables.")
        
        logger.info(f"Executing {len(orders)} orders on Polymarket")
        return self.polymarket_service.execute_orders_from_list(orders, neg_risk=neg_risk)
    
    def is_polymarket_available(self) -> bool:
        """Check if Polymarket service is available."""
        return self.polymarket_service is not None
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all available services."""
        return {
            "polymarket": self.is_polymarket_available()
        }
