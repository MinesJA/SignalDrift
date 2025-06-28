import logging
from typing import Any, Dict, List, Optional

import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PostOrdersArgs
from py_clob_client.order_builder.constants import BUY

logger = logging.getLogger(__name__)


class PolymarketOrderService:
    """
    Provides ability to submit orders to Polymarket

    Attributes:
        request_id: ID used to connect different fetched results
    """

    def __init__(self):
        self.client = None  # TODO: Initialize client properly



    def place_single_order(self, order_data: Dict[str, Any], order_type: str = "GTC") -> Optional[Dict[str, Any]]:
        """
        Place a single order on Polymarket.

        Args:
            order_data: Dictionary containing order details:
                - order: Signed order object with all required fields
                - owner: API key of order owner
            order_type: Order type ("FOK", "GTC", "GTD", "FAK")

        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - orderId: Unique order identifier
            - orderHashes: Settlement transaction hashes
            - errorMsg: Error message if applicable
        """
        try:
            url = f"{self.clob_api_base}/order"

            payload = {
                "order": order_data["order"],
                "owner": order_data["owner"],
                "orderType": order_type
            }

            headers = {**self.headers, "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info(f"Successfully placed order: {result.get('orderId')}")
            else:
                logger.error(f"Order placement failed: {result.get('errorMsg')}")

            return result

        except Exception as e:
            logger.error(f"Error placing single order: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orderId": None,
                "orderHashes": None
            }

    def place_multiple_orders(self, orders_data: List[Dict[str, Any]], order_type: str = "KOF") -> Optional[Dict[str, Any]]:
        """
        Place multiple orders in a batch on Polymarket.

        Args:
            orders_data: List of order dictionaries, each containing:
                - order: Signed order object with all required fields
                - owner: API key of order owner
            order_type: Order type for all orders ("FOK", "GTC", "GTD", "FAK")

        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - orderId: ID of the batch order
            - orderHashes: Settlement transaction hashes
            - errorMsg: Error message if applicable

        Note:
            Maximum of 5 orders per batch request
        """
        try:
            if len(orders_data) > 5:
                error_msg = "Maximum of 5 orders per batch request"
                logger.error(error_msg)
                return {
                    "success": False,
                    "errorMsg": error_msg,
                    "orderId": None,
                    "orderHashes": None
                }

            url = f"{self.clob_api_base}/orders"

            # Format orders for batch request
            formatted_orders = []
            for order_data in orders_data:
                formatted_orders.append({
                    "order": order_data["order"],
                    "owner": order_data["owner"],
                    "orderType": order_type
                })

            headers = {**self.headers, "Content-Type": "application/json"}

            response = requests.post(url, json=formatted_orders, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info(f"Successfully placed batch order: {result.get('orderId')}")
            else:
                logger.error(f"Batch order placement failed: {result.get('errorMsg')}")

            return result

        except Exception as e:
            logger.error(f"Error placing multiple orders: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orderId": None,
                "orderHashes": None
            }


host: str = "https://clob.polymarket.com"
key: str = "" ##This is your Private Key. Export from https://reveal.magic.link/polymarket or from your Web3 Application
chain_id: int = 137 #No need to adjust this
POLYMARKET_PROXY_ADDRESS: str = '' #This is the address you deposit/send USDC to to FUND your Polymarket account.

#Select from the following 3 initialization options to matches your login method, and remove any unused lines so only one client is initialized.


### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account. If you login with your email use this example.
client = ClobClient(host, key=key, chain_id=chain_id, signature_type=1, funder=POLYMARKET_PROXY_ADDRESS)

### Initialization of a client using a Polymarket Proxy associated with a Browser Wallet(Metamask, Coinbase Wallet, etc)
client = ClobClient(host, key=key, chain_id=chain_id, signature_type=2, funder=POLYMARKET_PROXY_ADDRESS)

### Initialization of a client that trades directly from an EOA.
client = ClobClient(host, key=key, chain_id=chain_id)

## Create and sign a limit order buying 100 YES tokens for 0.50c each
#Refer to the Markets API documentation to locate a tokenID: https://docs.polymarket.com/developers/gamma-markets-api/get-markets

client.set_api_creds(client.create_or_derive_api_creds())

resp = client.post_orders([
    PostOrdersArgs(
        # Create and sign a limit order buying 100 YES tokens for 0.50 each
        order=client.create_order(OrderArgs(
            price=0.01,
            size=5,
            side=BUY,
            token_id="88613172803544318200496156596909968959424174365708473463931555296257475886634",
        )),
        orderType=OrderType.GTC,  # Good 'Til Cancelled
    ),
    PostOrdersArgs(
        # Create and sign a limit order selling 200 NO tokens for 0.25 each
        order=client.create_order(OrderArgs(
            price=0.01,
            size=5,
            side=BUY,
            token_id="93025177978745967226369398316375153283719303181694312089956059680730874301533",
        )),
        orderType=OrderType.GTC,  # Good 'Til Cancelled
    )
])
print(resp)
