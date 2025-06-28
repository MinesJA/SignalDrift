import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class OddsSource(Enum):
    """Supported betting sources"""
    BETFAIR = "BETFAIR"
    FANDUEL = "FANDUEL"
    PINNACLE = "PINNACLE"
    POLYMARKET = "POLYMARKET"


class OddsType(Enum):
    """Types of odds formats"""
    DECIMAL = "DECIMAL"
    AMERICAN = "AMERICAN"
    FRACTIONAL = "FRACTIONAL"
    EXCHANGE = "EXCHANGE"


@dataclass
class OddsEvent:
    """
    Represents an odds event from various betting sources.

    Attributes:
        request_id: ID used to connect different fetched results
        timestamp: DateTime UTC when we fetched the market price
        impl_prob: Implied probability (vig removed if applicable)
        fair_odds: Fair odds value
        source: Name of source (polymarket, betfair, etc.)
        odds_type: Type of odds (decimal, american, fractional, exchange)
        question: The betting question/event
        updated_at: DateTime UTC that the endpoint provides (if available)
        meta: Additional metadata specific to source data
    """
    request_id: UUID
    timestamp: datetime
    og_odds: float
    impl_prob: float
    fair_odds: float
    source: OddsSource
    odds_type: OddsType
    question: str
    updated_at: Optional[datetime] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate impl_prob is between 0 and 1"""
        if not 0 <= self.impl_prob <= 1:
            raise ValueError(f"Implied probability must be between 0 and 1, got {self.impl_prob}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'request_id': str(self.request_id),
            'timestamp': self.timestamp.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'og_odds': self.og_odds,
            'impl_prob': self.impl_prob,
            'fair_odds': self.fair_odds,
            'source': self.source.value,
            'odds_type': self.odds_type.value,
            'question': self.question,
            'meta': self.meta
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'OddsEvent':
        """Create instance from dictionary"""
        timestamp = datetime.fromisoformat(data['timestamp'])
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])

        # Handle UUID conversion - accept both UUID and string
        request_id = data['request_id']
        if isinstance(request_id, str):
            request_id = UUID(request_id)

        return cls(
            request_id=request_id,
            timestamp=timestamp,
            og_odds=data['og_odds'],
            impl_prob=data['impl_prob'],
            fair_odds=data['fair_odds'],
            source=OddsSource(data['source']),
            odds_type=OddsType(data['odds_type']),
            question=data['question'],
            updated_at=updated_at,
            meta=data.get('meta', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'OddsEvent':
        """Create instance from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        """String representation"""
        return (f"OddsEvent(request_id={str(self.request_id)[:8]}..., "
                f"source={self.source.value}, question='{self.question}', "
                f"impl_prob={self.impl_prob:.4f}, fair_odds={self.fair_odds:.4f})")
