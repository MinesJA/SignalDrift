"""
Test script for order execution functionality.

This script tests the order execution service without actually placing orders.
It validates the configuration and service initialization.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from models.order import Order, OrderType
from services.order_executor import OrderExecutor
import time

def test_service_availability():
    """Test if the order execution services are available."""
    print("Testing order execution service availability...")
    
    executor = OrderExecutor()
    status = executor.get_service_status()
    
    print(f"Service Status: {status}")
    
    if status["polymarket"]:
        print("✅ Polymarket service is available")
    else:
        print("❌ Polymarket service is not available")
        print("   Check environment variables: POLYMARKET_PRIVATE_KEY, POLYMARKET_PROXY_ADDRESS")
    
    return status["polymarket"]

def create_sample_orders():
    """Create sample orders for testing."""
    print("\nCreating sample orders...")
    
    # Create sample orders (these won't be executed)
    current_time = int(time.time())
    
    orders = [
        Order(
            asset_id=123456789,  # Example asset ID
            market_slug="test-market-slug",
            order_type=OrderType.LIMIT_BUY,
            price=0.55,
            size=10.0,
            timestamp=current_time
        ),
        Order(
            asset_id=987654321,  # Example asset ID
            market_slug="test-market-slug-2",
            order_type=OrderType.LIMIT_SELL,
            price=0.45,
            size=5.0,
            timestamp=current_time
        )
    ]
    
    print(f"Created {len(orders)} sample orders:")
    for i, order in enumerate(orders, 1):
        print(f"  {i}. {order.order_type.value} {order.size} @ ${order.price} - {order.market_slug}")
    
    return orders

def test_order_conversion():
    """Test order conversion without executing."""
    print("\nTesting order conversion...")
    
    executor = OrderExecutor()
    
    if not executor.is_polymarket_available():
        print("❌ Cannot test conversion - Polymarket service unavailable")
        return False
    
    orders = create_sample_orders()
    
    try:
        # Test the conversion logic (this might fail without valid asset_ids)
        service = executor.polymarket_service
        
        for order in orders:
            print(f"Converting order: {order.market_slug}")
            order_args = service._convert_order_to_polymarket(order)
            print(f"  ✅ Converted to OrderArgs: price={order_args.price}, size={order_args.size}, side={order_args.side}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order conversion failed: {e}")
        return False

def main():
    """Main test function."""
    print("SignalDrift Order Execution Test")
    print("=" * 40)
    
    # Test service availability
    polymarket_available = test_service_availability()
    
    if polymarket_available:
        # Test order conversion
        conversion_success = test_order_conversion()
        
        if conversion_success:
            print("\n✅ All tests passed!")
            print("\nTo execute actual orders:")
            print("1. Ensure you have valid asset IDs from Polymarket")
            print("2. Use OrderExecutor.execute_polymarket_orders()")
            print("3. Monitor execution results")
        else:
            print("\n⚠️  Service available but conversion failed")
    else:
        print("\n❌ Service not available - check configuration")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()