#!/usr/bin/env python3
"""Test script for Polymarket service."""

import sys
import os
import unittest
from unittest.mock import patch, Mock
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.services.polymarket_service import PolymarketService
from pprint import pprint


class TestPolymarketService(unittest.TestCase):
    """Unit tests for PolymarketService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = PolymarketService()
    
    def test_initialization(self):
        """Test PolymarketService initialization."""
        self.assertIsNotNone(self.service.gamma_api_base)
        self.assertIsNotNone(self.service.clob_api_base)
        self.assertIsInstance(self.service.headers, dict)
        self.assertIsNone(self.service.websocket)
        self.assertFalse(self.service.is_connected)
        self.assertIsInstance(self.service.subscribed_assets, set)
        self.assertIsInstance(self.service.event_handlers, dict)
        
    @patch.object(PolymarketService, 'get_market_by_slug')
    def test_fetch_current_price_success(self, mock_get_market):
        """Test successful price fetching."""
        # Mock successful market data response
        mock_get_market.return_value = {
            "outcomes": '["Team A", "Team B"]',
            "outcomePrices": '["0.52", "0.48"]',
            "updatedAt": "2024-01-01T12:00:00Z"
        }
        
        result = self.service.fetch_current_price("test-slug")
        
        self.assertIsNotNone(result)
        self.assertIn("Team A", result)
        self.assertIn("Team B", result)
        self.assertEqual(result["Team A"], 0.52)
        self.assertEqual(result["Team B"], 0.48)
        self.assertIn("fetched_at", result)
        self.assertIn("updated_at", result)
        
    @patch.object(PolymarketService, 'get_market_by_slug')
    def test_fetch_current_price_failure(self, mock_get_market):
        """Test price fetching with API error."""
        mock_get_market.return_value = None
        
        result = self.service.fetch_current_price("test-slug")
        
        self.assertIsNone(result)
        
    @patch('src.services.polymarket_service.requests.get')
    def test_get_market_by_slug_success(self, mock_get):
        """Test successful market retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "slug": "test-slug",
                "title": "Test Market",
                "active": True
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.get_market_by_slug("test-slug")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["slug"], "test-slug")
        self.assertEqual(result["title"], "Test Market")
        
    @patch('src.services.polymarket_service.requests.get')
    def test_get_market_by_slug_failure(self, mock_get):
        """Test market retrieval with API error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        result = self.service.get_market_by_slug("test-slug")
        
        self.assertIsNone(result)



if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)