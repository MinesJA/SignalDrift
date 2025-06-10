#!/usr/bin/env python3
"""Test script for Polymarket service."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.services.polymarket_service import fetch_current_price
from pprint import pprint

# Test with a sample slug
slug = "mlb-sd-mil-2025-06-08"
print(f"Testing fetch_current_price with slug: {slug}")
print("-" * 50)

result = fetch_current_price(slug)

if result:
    print("Success! Fetched data:")
    pprint(result)
else:
    print("Failed to fetch data.")