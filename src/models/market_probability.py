from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json


@dataclass
class MarketProbability:
    """
    Represents a market probability from various betting sources.
    
    Attributes:
        request_id: ID used to connect different fetched results
        fetched_at: DateTime UTC when we fetched the market price
        probability: Fair odds probability (vig removed if applicable)
        source: Name of source (polymarket, betfair, etc.)
        team: Name of team the probability relates to winning
        updated_at: DateTime UTC that the endpoint provides (if available)
        meta: Additional metadata specific to source data
    """
    request_id: int
    fetched_at: datetime
    probability: float
    source: str
    team: str
    updated_at: Optional[datetime] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate probability is between 0 and 1"""
        if not 0 <= self.probability <= 1:
            raise ValueError(f"Probability must be between 0 and 1, got {self.probability}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'request_id': self.request_id,
            'fetched_at': self.fetched_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'probability': self.probability,
            'source': self.source,
            'team': self.team,
            'meta': self.meta
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketProbability':
        """Create instance from dictionary"""
        fetched_at = datetime.fromisoformat(data['fetched_at'])
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            request_id=data['request_id'],
            fetched_at=fetched_at,
            probability=data['probability'],
            source=data['source'],
            team=data['team'],
            updated_at=updated_at,
            meta=data.get('meta', {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MarketProbability':
        """Create instance from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    def __repr__(self) -> str:
        """String representation"""
        return (f"MarketProbability(request_id={self.request_id}, "
                f"source='{self.source}', team='{self.team}', "
                f"probability={self.probability:.4f})")
