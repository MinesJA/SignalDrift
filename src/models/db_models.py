"""SQLAlchemy models for database tables."""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID
import uuid
from sqlalchemy import (
    Column, BigInteger, String, DateTime, Numeric, Text, Integer,
    Enum as SQLEnum, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID, JSONB
from sqlalchemy.sql import func
from src.utils.database import Base
from src.models.odds_event import OddsSource, OddsType
from src.models.order_event import OrderSignal


class OddsEventDB(Base):
    """SQLAlchemy model for odds_events table."""
    
    __tablename__ = 'odds_events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(PostgreSQLUUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    og_odds = Column(Numeric, nullable=False)
    impl_prob = Column(Numeric, nullable=False)
    fair_odds = Column(Numeric, nullable=False)
    source = Column(SQLEnum(OddsSource), nullable=False)
    odds_type = Column(SQLEnum(OddsType), nullable=False)
    question = Column(Text, nullable=False)
    meta = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Add check constraint for impl_prob range
    __table_args__ = (
        CheckConstraint('impl_prob >= 0 AND impl_prob <= 1', name='check_impl_prob_range'),
        Index('idx_odds_events_request_id', 'request_id'),
        Index('idx_odds_events_source', 'source'),
        Index('idx_odds_events_question', 'question'),
        Index('idx_odds_events_timestamp_source', 'timestamp', 'source'),
        Index('idx_odds_events_meta', 'meta', postgresql_using='gin'),
    )
    
    def to_domain_model(self) -> 'OddsEvent':
        """Convert to domain model."""
        from src.models.odds_event import OddsEvent
        return OddsEvent(
            request_id=self.request_id,
            timestamp=self.timestamp,
            og_odds=float(self.og_odds),
            impl_prob=float(self.impl_prob),
            fair_odds=float(self.fair_odds),
            source=self.source,
            odds_type=self.odds_type,
            question=self.question,
            updated_at=self.updated_at,
            meta=dict(self.meta) if self.meta else {}
        )
    
    @classmethod
    def from_domain_model(cls, odds_event: 'OddsEvent') -> 'OddsEventDB':
        """Create from domain model."""
        return cls(
            request_id=odds_event.request_id,
            timestamp=odds_event.timestamp,
            updated_at=odds_event.updated_at,
            og_odds=odds_event.og_odds,
            impl_prob=odds_event.impl_prob,
            fair_odds=odds_event.fair_odds,
            source=odds_event.source,
            odds_type=odds_event.odds_type,
            question=odds_event.question,
            meta=odds_event.meta
        )


class OrderEventDB(Base):
    """SQLAlchemy model for order_events table."""
    
    __tablename__ = 'order_events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    order_signal = Column(SQLEnum(OrderSignal), nullable=False)
    price = Column(Numeric, nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint('size > 0', name='check_size_positive'),
        Index('idx_order_events_order_signal', 'order_signal'),
        Index('idx_order_events_timestamp_signal', 'timestamp', 'order_signal'),
        Index('idx_order_events_price', 'price'),
    )
    
    def to_domain_model(self) -> 'OrderEvent':
        """Convert to domain model."""
        from src.models.order_event import OrderEvent
        return OrderEvent(
            timestamp=self.timestamp,
            order_signal=self.order_signal,
            price=float(self.price),
            size=self.size
        )
    
    @classmethod
    def from_domain_model(cls, order_event: 'OrderEvent') -> 'OrderEventDB':
        """Create from domain model."""
        return cls(
            timestamp=order_event.timestamp,
            order_signal=order_event.order_signal,
            price=order_event.price,
            size=order_event.size
        )