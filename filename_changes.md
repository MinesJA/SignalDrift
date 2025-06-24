# Filename Changes

## Files Renamed

| Original Name | New Name |
|---------------|----------|
| `order_book_mlb-cle-sf-2025-06-17.csv` | `20250617-mlb-cle-sf-2025-06-17-order_book.csv` |
| `order_book_mlb-mil-chc-2025-06-17.csv` | `20250617-mlb-mil-chc-2025-06-17-order_book.csv` |
| `order_book_mlb-sd-lad-2025-06-17.csv` | `20250617-mlb-sd-lad-2025-06-17-order_book.csv` |
| `poly_market_price_change_event_mlb-cle-sf-2025-06-17.csv` | `20250617-mlb-cle-sf-2025-06-17-polymarket_market_events.csv` |
| `poly_market_price_change_event_mlb-mil-chc-2025-06-17.csv` | `20250617-mlb-mil-chc-2025-06-17-polymarket_market_events.csv` |
| `poly_market_price_change_event_mlb-sd-lad-2025-06-17.csv` | `20250617-mlb-sd-lad-2025-06-17-polymarket_market_events.csv` |
| `polymarket_trades_mlb-cle-sf-2025-06-17.csv` | `20250617-mlb-cle-sf-2025-06-17-orders.csv` |
| `polymarket_trades_mlb-mil-chc-2025-06-17.csv` | `20250617-mlb-mil-chc-2025-06-17-orders.csv` |
| `polymarket_trades_mlb-sd-lad-2025-06-17.csv` | `20250617-mlb-sd-lad-2025-06-17-orders.csv` |
| `20250619-mlb-ari-tor-2025-06-19-synthetic_orders.csv` | `20250619-mlb-ari-tor-2025-06-19-order_book.csv` |
| `20250619-mlb-cle-sf-2025-06-19-synthetic_orders.csv` | `20250619-mlb-cle-sf-2025-06-19-order_book.csv` |
| `20250619-mlb-col-wsh-2025-06-19-synthetic_orders.csv` | `20250619-mlb-col-wsh-2025-06-19-order_book.csv` |
| `20250619-mlb-kc-tex-2025-06-19-synthetic_orders.csv` | `20250619-mlb-kc-tex-2025-06-19-order_book.csv` |
| `20250619-mlb-laa-nyy-2025-06-19-synthetic_orders.csv` | `20250619-mlb-laa-nyy-2025-06-19-order_book.csv` |
| `20250619-mlb-mil-chc-2025-06-19-synthetic_orders.csv` | `20250619-mlb-mil-chc-2025-06-19-order_book.csv` |
| `20250619-mlb-min-cin-2025-06-19-synthetic_orders.csv` | `20250619-mlb-min-cin-2025-06-19-order_book.csv` |
| `20250619-mlb-pit-det-2025-06-19-synthetic_orders.csv` | `20250619-mlb-pit-det-2025-06-19-order_book.csv` |
| `20250619-mlb-stl-cws-2025-06-19-synthetic_orders.csv` | `20250619-mlb-stl-cws-2025-06-19-order_book.csv` |

## Files Ignored (as requested)

- `order_book.csv`
- `polymarket_trades.csv`
- `poly_market_price_change_event.csv`

## Naming Convention Applied

Format: `{YYYYMMDD}-{market_slug}-{file-type}`

### File Type Mappings
- `poly_market_price_change_event` → `polymarket_market_events`
- `polymarket_trades` → `orders`
- `synthetic_orders` → `order_book`
- `order_book` → `order_book`