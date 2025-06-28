from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY
from config import config

host: str = config.POLYMARKET_CLOB_API
chain_id: int = 137  # Polygon chain ID

# THIS WAS SO CONFUSING BUT...
# The address is the address that has the money (you can find it in the top right profile)
# NOT THE ADDRESS YOU FUND TO VIA THE DEPOSIT BUTTON
# I think thats just to do the swap, but that address has no money in it
# It's also not your wallet address. Thats why they call it a proxy. Its a proxy to your wallet
# if you're using a browser wallet like coinbase
# The key is from your browser wallet though

# All sensitive values now come from environment variables
POLYMARKET_PROXY_ADDRESS: str = config.POLYMARKET_PROXY_ADDRESS
private_key: str = config.POLYMARKET_PRIVATE_KEY

if not POLYMARKET_PROXY_ADDRESS or not private_key:
    raise ValueError("POLYMARKET_PROXY_ADDRESS and POLYMARKET_PRIVATE_KEY environment variables must be set")

client = ClobClient(host, key=private_key, chain_id=chain_id, signature_type=2, funder=POLYMARKET_PROXY_ADDRESS)

## Create and sign a limit order buying 5 tokens for 0.010c each
x = client.create_or_derive_api_creds()
client.set_api_creds(x)

order_args = OrderArgs(
    price=0.01,
    size=5.0,
    side=BUY,
    token_id="1203912039"  # asset_id (CLOB Token Id) you want to purchase goes here.
)
signed_order = client.create_order(order_args, PartialCreateOrderOptions(
    # True if its a market that has a binary option like yes/no
    # I think its false for thins like baseball games where its one team or the other but its two separate markets
    neg_risk=True
))

## GTC(Good-Till-Cancelled) Order
resp = client.post_order(signed_order, OrderType.GTC)
print(resp)
