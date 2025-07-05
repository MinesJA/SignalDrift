#!/usr/bin/env python3
"""Quick test script for Polymarket service."""

from src.services.polymarket_service import fetch_current_price

# Test with different slugs
test_slugs = [
    "mlb-sd-mil-2025-06-08",
    # Add more slugs here as needed
]

for slug in test_slugs:
    print(f"\nTesting slug: {slug}")
    print("-" * 50)
    
    result = fetch_current_price(slug)
    
    if result:
        for key, value in result.items():
            print(f"{key}: {value}")
    else:
        print("Failed to fetch data")