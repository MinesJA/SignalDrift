#!/usr/bin/env python3
"""
Example demonstrating the updated PolymarketOrderService that returns OrderExecutionResult tuples.
"""

from src.models import Order, OrderSide, OrderType
from src.services.polymarket_order_service import PolymarketOrderService, OrderExecutionResult
import csv
from datetime import datetime
from typing import List


def save_execution_results_to_csv(results: List[OrderExecutionResult], filename: str):
    """Save execution results to CSV for tracking."""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'timestamp', 'market_slug', 'market_id', 'asset_id', 'outcome_name',
            'side', 'order_type', 'price', 'size', 'success', 'order_id', 
            'status', 'error_msg'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'market_slug': result.order.market_slug,
                'market_id': result.order.market_id,
                'asset_id': result.order.asset_id,
                'outcome_name': result.order.outcome_name,
                'side': result.order.side.value,
                'order_type': result.order.order_type.value,
                'price': result.order.price,
                'size': result.order.size,
                'success': result.success,
                'order_id': result.order_id,
                'status': result.status,
                'error_msg': result.error_msg
            })


def main():
    # Example orders with different order types
    orders = [
        Order(
            market_slug="will-bitcoin-reach-100k-by-2025",
            market_id=123456,
            asset_id="16678291189211314327",
            outcome_name="YES",
            side=OrderSide.BUY,
            order_type=OrderType.GTC,  # Good-Til-Cancelled
            price=0.45,
            size=10.0,
            timestamp=1234567890
        ),
        Order(
            market_slug="will-bitcoin-reach-100k-by-2025",
            market_id=123456,
            asset_id="16678291189211314327",
            outcome_name="YES",
            side=OrderSide.SELL,
            order_type=OrderType.FOK,  # Fill-Or-Kill
            price=0.55,
            size=5.0,
            timestamp=1234567891
        ),
        Order(
            market_slug="will-eth-reach-5k-by-2025",
            market_id=789012,
            asset_id="26778391289311414428",
            outcome_name="NO",
            side=OrderSide.BUY,
            order_type=OrderType.FAK,  # Fill-And-Kill
            price=0.30,
            size=20.0,
            timestamp=1234567892
        )
    ]
    
    try:
        # Initialize the service (will fail without proper environment variables)
        service = PolymarketOrderService()
        
        # Execute orders and get results
        results = service.execute_orders_from_list(orders, neg_risk=True)
        
        # Print summary
        print(f"Executed {len(results)} orders:")
        for i, result in enumerate(results):
            print(f"\nOrder {i+1}:")
            print(f"  Market: {result.order.market_slug}")
            print(f"  Side: {result.order.side.value} {result.order.outcome_name}")
            print(f"  Type: {result.order.order_type.value}")
            print(f"  Price: {result.order.price}, Size: {result.order.size}")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  Order ID: {result.order_id}")
                print(f"  Status: {result.status}")
            else:
                print(f"  Error: {result.error_msg}")
        
        # Save to CSV
        save_execution_results_to_csv(results, "order_execution_results.csv")
        print("\nResults saved to order_execution_results.csv")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set POLYMARKET_PRIVATE_KEY and POLYMARKET_PROXY_ADDRESS environment variables")


if __name__ == "__main__":
    main()