from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType as PolymarketOrderType, PostOrdersArgs, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY, SELL
from typing import List, Dict, Any, Optional, NamedTuple
import logging
from src.config import config
from src.models import Order, OrderSide, OrderType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderExecutionResult(NamedTuple):
    """Result of an order execution attempt."""
    order: Order  # Original order object
    success: bool  # Whether the order was successfully placed
    order_id: Optional[str]  # Polymarket order ID if successful
    status: Optional[str]  # Order status (matched, live, delayed, unmatched)
    error_msg: Optional[str]  # Error message if failed
    polymarket_response: Dict[str, Any]  # Full response from Polymarket


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

    def place_single_order(self, order: Order, neg_risk: bool = True) -> Optional[Dict[str, Any]]:
        """
        Place a single order on Polymarket.

        Args:
            order: Internal Order object (must have order_type attribute)
            neg_risk: Whether this is a negative risk market (binary yes/no)

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

            # Convert our OrderType to Polymarket's OrderType
            order_type_map = {
                OrderType.GTC: PolymarketOrderType.GTC,
                OrderType.FOK: PolymarketOrderType.FOK,
                OrderType.FAK: PolymarketOrderType.FAK,
                OrderType.GTD: PolymarketOrderType.GTD
            }
            polymarket_order_type = order_type_map.get(order.order_type, PolymarketOrderType.FOK)

            # Submit the order
            result = self.client.post_order(signed_order, polymarket_order_type)

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

    def place_multiple_orders(self, orders: List[Order], neg_risk: bool = True) -> List[Dict[str, Any]]:
        """
        Place multiple orders in batches on Polymarket.

        Args:
            orders: List of internal Order objects (each must have order_type attribute)
            neg_risk: Whether this is a negative risk market (binary yes/no)

        Returns:
            List of results for each batch (max 5 orders per batch)

        Note:
            Automatically splits orders into batches of 5
        """
        if not orders:
            return []

        results = []

        # Split orders into batches of 5
        for i in range(0, len(orders), 5):
            batch = orders[i:i+5]
            batch_result = self._place_order_batch(batch, neg_risk)
            results.append(batch_result)

        return results

    def _place_order_batch(self, orders: List[Order], neg_risk: bool) -> Dict[str, Any]:
        """
        Place a single batch of orders (max 5).

        Args:
            orders: List of Order objects (max 5, each with order_type)
            neg_risk: Whether this is a negative risk market

        Returns:
            Batch execution result
        """
        try:
            if len(orders) > 5:
                error_msg = "Maximum of 5 orders per batch request"
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
                # Convert our OrderType to Polymarket's OrderType
                order_type_map = {
                    OrderType.GTC: PolymarketOrderType.GTC,
                    OrderType.FOK: PolymarketOrderType.FOK,
                    OrderType.FAK: PolymarketOrderType.FAK,
                    OrderType.GTD: PolymarketOrderType.GTD
                }
                polymarket_order_type = order_type_map.get(order.order_type, PolymarketOrderType.FOK)

                post_orders_args.append(PostOrdersArgs(
                    order=signed_order,
                    orderType=polymarket_order_type
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

    def execute_orders_from_list(self, orders: List[Order], neg_risk: bool = True) -> List[OrderExecutionResult]:
        """
        Execute a list of Order objects, handling batching automatically.

        Args:
            orders: List of Order objects to execute (each with order_type)
            neg_risk: Whether this is a negative risk market (binary yes/no)

        Returns:
            List of OrderExecutionResult tuples, one for each order
        """
        if not orders:
            return []

        logger.info(f"Executing {len(orders)} orders in batches of 5")

        execution_results = []

        # Split orders into batches of 5
        for i in range(0, len(orders), 5):
            batch = orders[i:i+5]

            try:
                # Convert orders to PostOrdersArgs
                post_orders_args = []
                for order in batch:
                    order_args = self._convert_order_to_polymarket(order)
                    signed_order = self.client.create_order(
                        order_args,
                        PartialCreateOrderOptions(neg_risk=neg_risk)
                    )

                    # Convert our OrderType to Polymarket's OrderType
                    # TODO: Revisit, this seems silly but maybe its necessary
                    order_type_map = {
                        OrderType.GTC: PolymarketOrderType.GTC,
                        OrderType.FOK: PolymarketOrderType.FOK,
                        OrderType.FAK: PolymarketOrderType.FAK,
                        OrderType.GTD: PolymarketOrderType.GTD
                    }
                    polymarket_order_type = order_type_map.get(order.order_type, PolymarketOrderType.FOK)

                    post_orders_args.append(PostOrdersArgs(
                        order=signed_order,
                        orderType=polymarket_order_type
                    ))

                # Submit batch and get results
                batch_results = self.client.post_orders(post_orders_args)

                # Process results - batch_results should be a list of individual order results
                if isinstance(batch_results, list):
                    for j, (order, result) in enumerate(zip(batch, batch_results)):
                        execution_results.append(OrderExecutionResult(
                            order=order,
                            success=result.get('success', False),
                            order_id=result.get('orderId'),
                            status=result.get('status'),
                            error_msg=result.get('errorMsg'),
                            polymarket_response=result
                        ))
                else:
                    # If batch failed as a whole, create failure results for all orders
                    error_msg = batch_results.get('errorMsg', 'Unknown batch error')
                    for order in batch:
                        execution_results.append(OrderExecutionResult(
                            order=order,
                            success=False,
                            order_id=None,
                            status=None,
                            error_msg=error_msg,
                            polymarket_response=batch_results
                        ))

            except Exception as e:
                # If exception occurs, create failure results for all orders in batch
                logger.error(f"Error placing batch: {e}")
                for order in batch:
                    execution_results.append(OrderExecutionResult(
                        order=order,
                        success=False,
                        order_id=None,
                        status=None,
                        error_msg=str(e),
                        polymarket_response={'error': str(e)}
                    ))

        # Log summary
        successful_orders = sum(1 for r in execution_results if r.success)
        logger.info(f"Executed {len(orders)} orders: {successful_orders} successful, {len(orders) - successful_orders} failed")

        return execution_results
