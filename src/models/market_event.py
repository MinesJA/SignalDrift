from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Self
from src.models import OrderSide, SyntheticOrder
import json

from abc import ABC, abstractmethod


class EventType(Enum):
    """Types of market events emitted by Polymarket websocket."""
    
    BOOK = "book"
    """Full order book snapshot - sent on initial subscription and after trades"""
    
    PRICE_CHANGE = "price_change"
    """Incremental order book update - sent when orders are placed, cancelled, or modified"""

@dataclass
class MarketEvent(ABC):
    """
    Represents a market event such as a price_change or book event

    Attributes:
        market_slug: The market identifier slug
        asset_id: The unique asset identifier
        market_id: The market address/identifier
        timestamp: Epoch timestamp in milliseconds
        hash: Event hash identifier
    """
    event_type: EventType
    market_slug: str
    market_id: int
    market: str
    asset_id: str
    outcome_name: str
    timestamp: int
    hash: str

    @classmethod
    def validate_event_type(cls, event_type: Optional[Any]) -> EventType:
        """Validate and convert event type to EventType enum."""
        if not event_type:
            raise ValueError("event_type cannot not be None")

        return EventType(event_type)

    @classmethod
    def validate_market_slug(cls, market_slug: Optional[Any]) -> str:
        """Validate market slug is not None."""
        if not market_slug:
            raise ValueError("market_slug cannot not be None")

        return market_slug

    @classmethod
    def validate_market_id(cls, market_id: Optional[Any]) -> int:
        """Validate market_id is not None and convert to int."""
        if not market_id:
            raise ValueError("market_id cannot not be None")

        return int(market_id)

    @classmethod
    def validate_market(cls, market: Optional[Any]) -> str:
        """Validate market is not None."""
        if not market:
            raise ValueError("market cannot not be None")

        return market

    @classmethod
    def validate_asset_id(cls, asset_id: Optional[Any]) -> str:
        """Validate asset_id is not None."""
        if not asset_id:
            raise ValueError("asset_id cannot not be None")

        return str(asset_id)

    @classmethod
    def validate_outcome_name(cls, outcome_name: Optional[Any]) -> str:
        """Validate outcome_name is not None."""
        if not outcome_name:
            raise ValueError("outcome_name cannot not be None")

        return outcome_name

    @classmethod
    def validate_timestamp(cls, timestamp: Optional[Any]) -> int:
        """Validate timestamp is not None and convert to int."""
        if not timestamp:
            raise ValueError("timestamp cannot not be None")

        return int(timestamp)

    @classmethod
    def validate_hash(cls, hash: Optional[Any]) -> str:
        """Validate hash is not None."""
        if not hash:
            raise ValueError("hash cannot not be None")

        return hash

    @abstractmethod
    def asdict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        pass

    @abstractmethod
    def asdict_rows(self) -> List[Dict[str, Any]]:
        """
        Convert event to list of flat dictionary rows for CSV export.
        
        Abstract method to be implemented by subclasses to flatten
        hierarchical event data into rows suitable for CSV/tabular export.
        
        Returns:
            List of dictionaries where each represents a row
        """
        pass

    def to_json(self) -> str:
        """Convert MarketEvent to JSON string"""
        return json.dumps(self.asdict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketEvent':
        """
        Create MarketEvent from dictionary

        TODO: Is there generics for typing in python?
        """

        event_type = cls.validate_event_type(data.get('event_type'))
        if event_type == EventType.BOOK:
            return BookEvent.from_dict(data)
        elif event_type == EventType.PRICE_CHANGE:
            return PriceChangeEvent.from_dict(data)
        else:
            raise ValueError(f"event_type of {event_type} must be of type 'PRICE_CHANGE' or 'BOOK'")

    @classmethod
    def from_json(cls, json_str: str) -> 'MarketEvent':
        """Create MarketEvent from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class BookEvent(MarketEvent):
    """
    Book event emitted when:
        - First subscribed to a market
        - When there is a trade that affects the book
    """
    bids: List[SyntheticOrder] = field(default_factory=list)
    asks: List[SyntheticOrder] = field(default_factory=list)


    @classmethod
    def validate_bids(cls, bids: Optional[Any]) -> List[SyntheticOrder]:
        if bids is None:
            raise ValueError("bids cannot be None")
        if not bids:  # Empty list is ok
            return []

        return [
            SyntheticOrder(
                side=OrderSide.BUY,
                price=float(bid["price"]),
                size=float(bid["size"]),
            )
            for bid in bids
        ]

    @classmethod
    def validate_asks(cls, asks: Optional[Any]) -> List[SyntheticOrder]:
        if asks is None:
            raise ValueError("asks cannot be None")
        if not asks:  # Empty list is ok
            return []

        return [
            SyntheticOrder(
                side=OrderSide.SELL,
                price=float(ask["price"]),
                size=float(ask["size"]),
            )
            for ask in asks
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            event_type = EventType.BOOK,
            market_slug = cls.validate_market_slug(data.get('market_slug')),
            market_id = cls.validate_market_id(data.get('market_id')),
            market = cls.validate_market(data.get('market')),
            asset_id = cls.validate_asset_id(data.get('asset_id')),
            outcome_name = cls.validate_outcome_name(data.get('outcome_name')),
            timestamp = cls.validate_timestamp(data.get('timestamp')),
            hash = cls.validate_hash(data.get('hash')),
            bids = cls.validate_bids(data.get('bids')),
            asks = cls.validate_asks(data.get('asks'))
        )


    def asdict(self) -> Dict[str, Any]:
        """
        TODO: Should refactor this. There's ways to do this that are cleaner
        for dataclasses and don't require as much repetition between child
        classes
        """
        return {
            'market_slug': self.market_slug,
            'event_type': self.event_type.value,
            'asset_id': self.asset_id,
            'market': self.market,
            'timestamp': self.timestamp,
            'hash': self.hash,
            'bids': [bid.asdict() for bid in self.bids],
            'asks': [ask.asdict() for ask in self.asks]
        }

    def asdict_rows(self) -> List[Dict[str, Any]]:
        """
        Convert BookEvent to list of flat dictionary rows for CSV export.
        
        Creates one row per order (bid or ask), with market event metadata
        duplicated in each row.
        
        Returns:
            List of dictionaries where each dict represents one order with:
            - All market event metadata fields
            - Individual order fields (side, price, size)
        """
        event_dict = self.asdict()
        ask_dicts = event_dict.pop("asks")
        bid_dicts = event_dict.pop("bids")
        asks = [{**event_dict, **ask} for ask in ask_dicts]
        bids = [{**event_dict, **bid} for bid in bid_dicts]

        return asks + bids


@dataclass
class PriceChangeEvent(MarketEvent):
    """
    Represents a market event such as a price_change or book event
        PriceChange event emitted when:
            - An order is cancelled
            - A new order is placed

    Attributes:
    """
    changes: List[SyntheticOrder] = field(default_factory=list)


    @classmethod
    def validate_changes(cls, changes: Optional[Any]) -> List[SyntheticOrder]:
        if not changes:
            raise ValueError("bids cannot be None")

        return [
            SyntheticOrder(
                side=OrderSide(change["side"]),
                price=float(change["price"]),
                size=float(change["size"]),
            )
            for change in changes
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        return cls(
            event_type = EventType.PRICE_CHANGE,
            market_slug = cls.validate_market_slug(data.get('market_slug')),
            market_id = cls.validate_market_id(data.get('market_id')),
            market = cls.validate_market(data.get('market')),
            asset_id = cls.validate_asset_id(data.get('asset_id')),
            outcome_name = cls.validate_outcome_name(data.get('outcome_name')),
            timestamp = cls.validate_timestamp(data.get('timestamp')),
            hash = cls.validate_hash(data.get('hash')),
            changes = cls.validate_changes(data.get('changes'))
        )

    def asdict(self) -> Dict[str, Any]:
        return {
            'market_slug': self.market_slug,
            'event_type': self.event_type.value,
            'asset_id': self.asset_id,
            'market': self.market,
            'timestamp': self.timestamp,
            'hash': self.hash,
            'changes': [change.asdict() for change in self.changes]
        }

    def asdict_rows(self) -> List[Dict[str, Any]]:
        """
        Convert PriceChangeEvent to list of flat dictionary rows for CSV export.
        
        Creates one row per order change, with market event metadata
        duplicated in each row.
        
        Returns:
            List of dictionaries where each dict represents one change with:
            - All market event metadata fields  
            - Individual change fields (side, price, size)
        """
        event_dict = self.asdict()
        changes = event_dict.pop("changes")
        return [{**event_dict, **change} for change in changes]


