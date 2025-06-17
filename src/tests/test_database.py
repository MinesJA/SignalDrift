"""Tests for database setup and models."""

import pytest
from datetime import datetime
from uuid import uuid4
from src.models.odds_event import OddsEvent, OddsSource, OddsType
from src.models.order_event import OrderEvent, OrderSignal
from src.models.db_models import OddsEventDB, OrderEventDB
from src.utils.database import test_db_manager


class TestDatabaseModels:
    """Test database model conversions."""
    
    def test_odds_event_model_conversion(self):
        """Test OddsEvent to/from database model conversion."""
        # Create domain model
        odds_event = OddsEvent(
            request_id=uuid4(),
            timestamp=datetime.utcnow(),
            og_odds=2.5,
            impl_prob=0.4,
            fair_odds=2.0,
            source=OddsSource.BETFAIR,
            odds_type=OddsType.DECIMAL,
            question="Will Team A win?",
            meta={"market_id": "123", "sport": "football"}
        )
        
        # Convert to database model
        db_model = OddsEventDB.from_domain_model(odds_event)
        
        # Verify conversion
        assert db_model.request_id == odds_event.request_id
        assert db_model.timestamp == odds_event.timestamp
        assert float(db_model.og_odds) == odds_event.og_odds
        assert float(db_model.impl_prob) == odds_event.impl_prob
        assert float(db_model.fair_odds) == odds_event.fair_odds
        assert db_model.source == odds_event.source
        assert db_model.odds_type == odds_event.odds_type
        assert db_model.question == odds_event.question
        assert db_model.meta == odds_event.meta
        
        # Convert back to domain model
        converted_back = db_model.to_domain_model()
        
        # Verify round-trip conversion
        assert converted_back.request_id == odds_event.request_id
        assert converted_back.timestamp == odds_event.timestamp
        assert converted_back.og_odds == odds_event.og_odds
        assert converted_back.impl_prob == odds_event.impl_prob
        assert converted_back.fair_odds == odds_event.fair_odds
        assert converted_back.source == odds_event.source
        assert converted_back.odds_type == odds_event.odds_type
        assert converted_back.question == odds_event.question
        assert converted_back.meta == odds_event.meta
    
    def test_order_event_model_conversion(self):
        """Test OrderEvent to/from database model conversion."""
        # Create domain model
        order_event = OrderEvent(
            timestamp=datetime.utcnow(),
            order_signal=OrderSignal.LIMIT_BUY,
            price=1.5,
            size=100
        )
        
        # Convert to database model
        db_model = OrderEventDB.from_domain_model(order_event)
        
        # Verify conversion
        assert db_model.timestamp == order_event.timestamp
        assert db_model.order_signal == order_event.order_signal
        assert float(db_model.price) == order_event.price
        assert db_model.size == order_event.size
        
        # Convert back to domain model
        converted_back = db_model.to_domain_model()
        
        # Verify round-trip conversion
        assert converted_back.timestamp == order_event.timestamp
        assert converted_back.order_signal == order_event.order_signal
        assert converted_back.price == order_event.price
        assert converted_back.size == order_event.size


class TestDatabaseConnection:
    """Test database connection and basic operations."""
    
    def test_database_manager_creation(self):
        """Test that database manager can be created."""
        assert test_db_manager is not None
        assert test_db_manager.database_url is not None
    
    def test_session_creation(self):
        """Test that database sessions can be created."""
        session = test_db_manager.get_session()
        assert session is not None
        session.close()