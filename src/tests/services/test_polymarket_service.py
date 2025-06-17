#!/usr/bin/env python3
"""Test script for Polymarket service."""

import sys
import os
import unittest
from unittest.mock import patch, Mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.services.polymarket_service import PolymarketService, fetch_current_price, place_single_order, place_multiple_orders
from pprint import pprint


class TestPolymarketService(unittest.TestCase):
    """Unit tests for PolymarketService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = PolymarketService()
        
        # Sample order data for testing
        self.sample_order_data = {
            "order": {
                "salt": 12345,
                "maker": "0x123abc...",
                "signer": "0x456def...",
                "taker": "0x789ghi...",
                "tokenId": "token123",
                "makerAmount": "1000000",
                "takerAmount": "500000",
                "expiration": 1703980800,
                "nonce": 1,
                "feeRateBps": 100,
                "side": "BUY",
                "signatureType": 0,
                "signature": "0xabcd1234..."
            },
            "owner": "test-api-key"
        }
        
        self.sample_success_response = {
            "success": True,
            "orderId": "order-123",
            "orderHashes": ["0xhash1", "0xhash2"],
            "errorMsg": None
        }
        
        self.sample_error_response = {
            "success": False,
            "orderId": None,
            "orderHashes": None,
            "errorMsg": "Insufficient balance"
        }

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_success(self, mock_post):
        """Test successful single order placement."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_success_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.service.place_single_order(self.sample_order_data, "GTC")
        
        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertEqual(result["orderId"], "order-123")
        
        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("order", call_args.kwargs["json"])
        self.assertIn("owner", call_args.kwargs["json"])
        self.assertIn("orderType", call_args.kwargs["json"])
        self.assertEqual(call_args.kwargs["json"]["orderType"], "GTC")

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_failure(self, mock_post):
        """Test single order placement with API error."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_error_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.service.place_single_order(self.sample_order_data, "FOK")
        
        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertEqual(result["errorMsg"], "Insufficient balance")
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_network_error(self, mock_post):
        """Test single order placement with network error."""
        mock_post.side_effect = Exception("Network error")
        
        result = self.service.place_single_order(self.sample_order_data, "GTC")
        
        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Network error", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_multiple_orders_success(self, mock_post):
        """Test successful multiple orders placement."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_success_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        orders_data = [self.sample_order_data, self.sample_order_data]
        result = self.service.place_multiple_orders(orders_data, "GTC")
        
        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertEqual(result["orderId"], "order-123")
        
        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIsInstance(call_args.kwargs["json"], list)
        self.assertEqual(len(call_args.kwargs["json"]), 2)

    def test_place_multiple_orders_too_many(self):
        """Test multiple orders placement with too many orders."""
        orders_data = [self.sample_order_data] * 6  # 6 orders, max is 5
        
        result = self.service.place_multiple_orders(orders_data, "GTC")
        
        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Maximum of 5 orders", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_multiple_orders_network_error(self, mock_post):
        """Test multiple orders placement with network error."""
        mock_post.side_effect = Exception("Network error")
        
        orders_data = [self.sample_order_data, self.sample_order_data]
        result = self.service.place_multiple_orders(orders_data, "FAK")
        
        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Network error", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    def test_order_types_validation(self):
        """Test that different order types are handled correctly."""
        order_types = ["GTC", "FOK", "FAK", "GTD"]
        
        with patch('src.services.polymarket_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_success_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            for order_type in order_types:
                result = self.service.place_single_order(self.sample_order_data, order_type)
                self.assertTrue(result["success"])
                
                # Check that the correct order type was sent
                call_args = mock_post.call_args
                self.assertEqual(call_args.kwargs["json"]["orderType"], order_type)


def run_integration_test():
    """Run integration test with actual API call (commented out for safety)."""
    print("\n" + "="*60)
    print("INTEGRATION TESTS (Manual)")
    print("="*60)
    print("The following integration test is commented out to prevent")
    print("accidental real API calls during automated testing.")
    print("Uncomment and configure with real credentials to test:")
    print()
    print("# Test with a sample slug")
    print('slug = "mlb-sd-mil-2025-06-08"')
    print('print(f"Testing fetch_current_price with slug: {slug}")')
    print('print("-" * 50)')
    print()
    print('result = fetch_current_price(slug)')
    print()
    print('if result:')
    print('    print("Success! Fetched data:")')
    print('    pprint(result)')
    print('else:')
    print('    print("Failed to fetch data.")')


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration test info
    run_integration_test()