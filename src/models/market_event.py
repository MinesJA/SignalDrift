import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class EventType(Enum):
    BOOK = "book"
    PRICE_CHANGE = "price_change"


class Side(Enum):
    BID = "bid"
    ASK = "ask"


@dataclass
class MarketEvent:
    """
    Represents a market event such as a price_change or book event

    Attributes:
        market_slug: The market identifier slug
        event_type: Type of event - EventType.BOOK or EventType.PRICE_CHANGE
        asset_id: The unique asset identifier
        market: The market address/identifier
        side: Order side - Side.BID or Side.ASK
        price: The price as a string
        size: The size/quantity as a string
        timestamp: Epoch timestamp in milliseconds
        hash: Event hash identifier
    """
    market_slug: Optional[str] = None
    event_type: EventType = EventType.BOOK
    asset_id: str = ""
    market: str = ""
    side: Side = Side.BID
    price: str = ""
    size: str = ""
    timestamp: str = ""
    hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert MarketEvent to dictionary"""
        return {
            'market_slug': self.market_slug,
            'event_type': self.event_type.value,
            'asset_id': self.asset_id,
            'market': self.market,
            'side': self.side.value,
            'price': self.price,
            'size': self.size,
            'timestamp': self.timestamp,
            'hash': self.hash
        }

    def to_json(self) -> str:
        """Convert MarketEvent to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'MarketEvent':
        """Create MarketEvent from dictionary"""
        return cls(
            market_slug=data.get('market_slug'),
            event_type=EventType(data.get('event_type', 'book')),
            asset_id=data.get('asset_id', ''),
            market=data.get('market', ''),
            side=Side(data.get('side', 'bid')),
            price=data.get('price', ''),
            size=data.get('size', ''),
            timestamp=data.get('timestamp', ''),
            hash=data.get('hash', '')
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'MarketEvent':
        """Create MarketEvent from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class BookEvent(MarketEvent):
    """
    Emitted when:
        - First subscribed to a market
        - When there is a trade that affects the book
    """
    event_type: EventType = EventType.BOOK


@dataclass
class PriceChangeEvent(MarketEvent):
    """
    Emitted when:
        - A new order is placed
        - An order is cancelled
    """
    event_type: EventType = EventType.PRICE_CHANGE


