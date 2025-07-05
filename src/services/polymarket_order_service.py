from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType as PolymarketOrderType, PostOrdersArgs, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY, SELL
from typing import List, Dict, Any, Optional, NamedTuple
import logging
from src.config import config
from src.models import Order, OrderSide, OrderType, OrderExecution
from src.utils.datetime_utils import datetime_to_epoch
from datetime import datetime

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
            self.host,
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

    def _build_polymarket_order(self, order: Order, neg_risk: bool) -> PostOrdersArgs:

        """
         TODO: Revisit this
         Will probably need some more logic in the Order models
         because a FOK and FAK will only specify a total amount in $
         to purchase (because they are essentially market orders)
         I don't think we can specify a price and size for FOK/FAK.
         Maybe do a polymorphic/inheritance model to capture different
         argument requirements.

         The other option (tho not mutually exclusive with polymorphic models)
         is to go back to using traditional finance terms that then get
         translated to Polymarket terms. I'm worried we're tying our logic too
         much to polymarket. Should be more agnostic

         Bid/Ask
         Limit Buy Order, Limit Sell Order, Market Order
        """
        order_side_map = {
            OrderSide.BUY: BUY,
            OrderSide.SELL: SELL
        }
        order_type_map = {
            OrderType.GTC: PolymarketOrderType.GTC,
            OrderType.FOK: PolymarketOrderType.FOK,
            OrderType.FAK: PolymarketOrderType.FAK,
            OrderType.GTD: PolymarketOrderType.GTD
        }

        poly_ordertype = order_type_map.get(order.order_type)
        poly_orderside = order_side_map.get(order.side)

        #TODO: Need to import ArgumentError
        #if poly_ordertype is None:
        #    raise ArgumentError(f"Must provide valid order_type. {order.order_type} not valid")

        #TODO: Need to import ArgumentError
        #if poly_orderside is None:
        #    raise ArgumentError(f"Must provide valid order_side. {order.side} not valid")

        signed_order = self.client.create_order(
            OrderArgs(
                price=order.price,
                size=order.size,
                side=poly_orderside,
                token_id=order.asset_id
            ),
            PartialCreateOrderOptions(neg_risk=neg_risk)
        )

        return PostOrdersArgs(
            order=signed_order,
            orderType=poly_ordertype
        )

    def post_order(self, order: Order, neg_risk: bool = True) -> Optional[Dict[str, Any]]:
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
                PartialCreateOrderOptions(neg_risk=False)
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


    def _execute_batch(self, orders: List[Order], neg_risk: bool = False) -> List[Order]:
        posted_at_timestamp = datetime_to_epoch(datetime.now())
        try:
            post_orders_args = [self._build_polymarket_order(order, neg_risk) for order in orders]
            order_results = self.client.post_orders(post_orders_args)

            if not isinstance(order_results, list):
                error_msg = order_results.get('errorMsg', 'Unknown batch error')
                return [order.with_post_failure(error_msg, None, posted_at_timestamp) for order in orders]

            order_results = []
            for _, (order, result) in enumerate(zip(orders, order_results)):
                success = result.get("success", False)
                error_msg = result.get("errorMsg")
                status = result.get("status", "")

                if success and error_msg is None:
                    order_results.append(order.with_post_success(
                        order_id=result.get("orderID"),
                        status=status,
                        making_amount=result.get("makingAmount"),
                        taking_amount=result.get("takingAmount"),
                        posted_at_timestamp=posted_at_timestamp
                    ))
                else:
                    order_results.append(order.with_post_failure(
                        error_msg=error_msg,
                        status=status,
                        posted_at_timestamp=posted_at_timestamp
                    ))

            return order_results
        except Exception as e:
            # If exception occurs, create failure results for all orders in batch
            logger.error(f"Error placing batch: {e}")
            return [ order.with_post_failure(
                    error_msg="Error placing batch",
                    status=None, # Could add our own status like "internal_failure"
                    posted_at_timestamp=posted_at_timestamp
                ) for order in orders]

    def post_orders(self, orders: List[Order], neg_risk: bool = False) -> List[Order]:
        """
        Execute a list of Order objects, handling batching automatically.

        Args:
            orders: List of Order objects to execute (each with order_type)
            neg_risk: Whether this is a negative risk market (binary yes/no)

        Returns:
            List of Orders, updated with execution results
        """
        if not orders:
            return []

        logger.info(f"Executing {len(orders)} orders in batches of 4")

        execution_results = []

        # Split orders into batches of 5 -- limit by polymarket
        for i in range(0, len(orders), 4):
            batch = orders[i:i+4]
            execution_results.extend(self._execute_batch(batch, neg_risk))

        # Log summary
        successful_orders = sum(1 for r in execution_results if r.success)
        logger.info(f"Executed {len(orders)} orders: {successful_orders} successful, {len(orders) - successful_orders} failed")

        return execution_results


