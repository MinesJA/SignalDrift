from dataclasses import dataclass

@dataclass
class MarketEvent:
    """
    Represents a market event such as a price_change or book event

    Attributes:
        market_slug:
        event_type: "book" | "price_change"
        asset_id:
        market:
        side: bid | ask
        price:
        size:
        timestamp: Epoch timestamp
        hash:
    """


class BookEvent(MarketEvent):
    """
    Emitted when:
        - First subscribed to a market/
        - When there is a trade that affects the book
    """

    #{
    #  "event_type": "book",
    #  "asset_id": "65818619657568813474341868652308942079804919287380422192892211131408793125422",
    #  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
    #  "buys": [
    #    { "price": ".48", "size": "30" },
    #    { "price": ".49", "size": "20" },
    #    { "price": ".50", "size": "15" }
    #  ],
    #  "sells": [
    #    { "price": ".52", "size": "25" },
    #    { "price": ".53", "size": "60" },
    #    { "price": ".54", "size": "10" }
    #  ],
    #  "timestamp": "123456789000",
    #  "hash": "0x0...."
    #}

    #{
    #    "event_type": "book"
    #    "asset_id"
    #    "market"
    #    "side": bid | ask
    #    "price"
    #    "size"
    #    "timestamp"
    #    "hash"
    #}


"""
Emitted when:
    - A new order is placed
    - An order is cancelled
"""
class PriceChangeEvent(MarketEvent):

    #{
    #  "asset_id": "71321045679252212594626385532706912750332728571942532289631379312455583992563",
    #  "changes": [
    #    {
    #      "price": "0.4",
    #      "side": "SELL",
    #      "size": "3300"
    #    },
    #    {
    #      "price": "0.5",
    #      "side": "SELL",
    #      "size": "3400"
    #    },
    #    {
    #      "price": "0.3",
    #      "side": "SELL",
    #      "size": "3400"
    #    }
    #  ],
    #  "event_type": "price_change",
    #  "market": "0x5f65177b394277fd294cd75650044e32ba009a95022d88a0c1d565897d72f8f1",
    #  "timestamp": "1729084877448",
    #  "hash": "3cd4d61e042c81560c9037ece0c61f3b1a8fbbdd"
    #}

    #{
    #    "event_type": "price_change"
    #    "asset_id"
    #    "market"
    #    "side": bid | ask
    #    "price"
    #    "size"
    #    "timestamp"
    #    "hash"
    #}


