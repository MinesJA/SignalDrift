from config import config
from py_clob_client.client import ClobClient

class ConnectionError(Exception):
    """Error connecting with client"""
    pass


class MissingParam(Exception):
    """Error connecting with client"""
    pass

class PolymarketClobClient:
    def __init__(self, client):
        # TODO: Add validation to host, key, address
        self.client = client

    @classmethod
    def connect(cls):
        host = config.POLYMARKET_CLOB_API
        key = config.POLYMARKET_PRIVATE_KEY
        address = config.POLYMARKET_PROXY_ADDRESS
        chain_id = 137
        signature_type = 2

        if not address or not key or not address:
            # TODO: Rename or look for generic exception?
            raise MissingParam(f"Missing POLYMARKET_CLOB_API or POLYMARKET_PRIVATE_KEY or POLYMARKET_PROXY_ADDRESS")

        client = ClobClient(host, key=key, chain_id=chain_id, signature_type=signature_type, funder=address)

        if not client.get_ok():
            # TODO: Rename or look for generic exception?
            raise ConnectionError("Failed to connect to ClobClient")

        return cls(client)


