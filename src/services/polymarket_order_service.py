from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PostOrdersArgs, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY, SELL
from typing import List, Dict, Any, Optional
import logging
from src.config import config
from src.models import Order, OrderSide

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymarketOrderService:
    """
    Provides ability to submit orders to Polymarket using the official py-clob-client.

    Handles conversion from internal Order objects to Polymarket API calls.
    Supports batch order submission with automatic batching for >5 orders.
    """

    def __init__(self):
        """Initialize the Polymarket order service with configuration from environment variables."""
        self.host = config.POLYMARKET_CLOB_API
        self.chain_id = 137  # Polygon chain ID
        self.private_key = config.POLYMARKET_PRIVATE_KEY
        self.proxy_address = config.POLYMARKET_PROXY_ADDRESS

        if not self.private_key or not self.proxy_address:
            raise ValueError("POLYMARKET_PRIVATE_KEY and POLYMARKET_PROXY_ADDRESS environment variables must be set")

        # Initialize client with browser wallet signature type (2)
        self.client = ClobClient(
            host=self.host,
            key=self.private_key,
            chain_id=self.chain_id,
            signature_type=2,
            funder=self.proxy_address
        )

        # Set up API credentials
        api_creds = self.client.create_or_derive_api_creds()
        self.client.set_api_creds(api_creds)

        logger.info("PolymarketOrderService initialized successfully")



    def _convert_order_to_polymarket(self, order: Order) -> OrderArgs:
        """
        Convert internal Order object to Polymarket OrderArgs.

        Args:
            order: Internal Order object

        Returns:
            OrderArgs object for Polymarket API
        """
        if order.side == OrderSide.BUY:
            side = BUY
        elif order.side == OrderSide.SELL:
            side = SELL
        else:
            raise ValueError(f"Unsupported order side: {order.side}")

        return OrderArgs(
            price=order.price,
            size=order.size,
            side=side,
            token_id=order.asset_id
        )

    def place_single_order(self, order: Order, neg_risk: bool = True, order_type: OrderType = OrderType.FOK) -> Optional[Dict[str, Any]]:
        """
        Place a single order on Polymarket.

        Args:
            order: Internal Order object
            neg_risk: Whether this is a negative risk market (binary yes/no)
            order_type: Polymarket OrderType (GTC, FOK, etc.)

        Returns:
            Dictionary containing order execution result
        """
        try:
            # Convert internal order to Polymarket format
            order_args = self._convert_order_to_polymarket(order)

            # Create and sign the order
            signed_order = self.client.create_order(
                order_args,
                PartialCreateOrderOptions(neg_risk=neg_risk)
            )

            # Submit the order
            result = self.client.post_order(signed_order, order_type)

            logger.info(f"Successfully placed order for {order.market_slug}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error placing single order for {order.market_slug}: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orderId": None,
                "orderHashes": None
            }

    def place_multiple_orders(self, orders: List[Order], neg_risk: bool = True, order_type: OrderType = OrderType.FOK) -> List[Dict[str, Any]]:
        """
        Place multiple orders in batches on Polymarket.

        Args:
            orders: List of internal Order objects
            neg_risk: Whether this is a negative risk market (binary yes/no)
            order_type: Polymarket OrderType (GTC, FOK, etc.)

        Returns:
            List of results for each batch (max 4 orders per batch)

        Note:
            Automatically splits orders into batches of 4
        """
        if not orders:
            return []

        results = []

        # Split orders into batches of 4
        for i in range(0, len(orders), 4):
            batch = orders[i:i+4]
            batch_result = self._place_order_batch(batch, neg_risk, order_type)
            results.append(batch_result)

        return results

    def _place_order_batch(self, orders: List[Order], neg_risk: bool, order_type: OrderType) -> Dict[str, Any]:
        """
        Place a single batch of orders (max 4).

        Args:
            orders: List of Order objects (max 4)
            neg_risk: Whether this is a negative risk market
            order_type: Polymarket OrderType

        Returns:
            Batch execution result
        """
        try:
            if len(orders) > 4:
                error_msg = "Maximum of 4 orders per batch request"
                logger.error(error_msg)
                return {
                    "success": False,
                    "errorMsg": error_msg,
                    "orders_processed": 0,
                    "results": []
                }

            # Convert orders to PostOrdersArgs
            post_orders_args = []
            for order in orders:
                order_args = self._convert_order_to_polymarket(order)
                signed_order = self.client.create_order(
                    order_args,
                    PartialCreateOrderOptions(neg_risk=neg_risk)
                )
                post_orders_args.append(PostOrdersArgs(
                    order=signed_order,
                    orderType=order_type
                ))

            # Submit batch
            result = self.client.post_orders(post_orders_args)

            logger.info(f"Successfully placed batch of {len(orders)} orders: {result}")
            return {
                "success": True,
                "orders_processed": len(orders),
                "results": result,
                "errorMsg": None
            }

        except Exception as e:
            logger.error(f"Error placing order batch: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orders_processed": 0,
                "results": []
            }

    def execute_orders_from_list(self, orders: List[Order], neg_risk: bool = True) -> Dict[str, Any]:
        """
        Execute a list of Order objects, handling batching automatically.

        Args:
            orders: List of Order objects to execute
            neg_risk: Whether this is a negative risk market (binary yes/no)

        Returns:
            Summary of execution results
        """
        if not orders:
            return {
                "success": True,
                "total_orders": 0,
                "batches_processed": 0,
                "results": []
            }

        logger.info(f"Executing {len(orders)} orders in batches of 4")

        results = self.place_multiple_orders(orders, neg_risk=neg_risk)

        # Summarize results
        total_success = sum(1 for r in results if r.get("success", False))
        total_orders = len(orders)

        return {
            "success": total_success == len(results),
            "total_orders": total_orders,
            "batches_processed": len(results),
            "successful_batches": total_success,
            "failed_batches": len(results) - total_success,
            "results": results
        }
