https://gist.github.com/MinesJA/7e1115724652049342ab29a05afa2881
Given the sell side of each order book for markets a and b:
```
"market_a_sells" = [
  { "price": ".47", "size": "25" },
  { "price": ".53", "size": "60" },
  { "price": ".54", "size": "10" }
]


"market_b_sells" = [
  { "price": ".48", "size": "10" },
  { "price": ".49", "size": "60" },
  { "price": ".54", "size": "10" }
]
```

For the cheapest sell price for each side we take the smaller size and create an order for both sides from that if their sum is less than $1. In this case:
```
b for 10 @ 0.48
a for 10 @ 0.47
```

We then remove those from our copy of the order books and recursively check the remainder:

```
"market_a_sells" = [
  { "price": ".47", "size": "15" }, # Original 25 - 10 that we ordered leaves 15 Remaining
  { "price": ".53", "size": "60" },
  { "price": ".54", "size": "10" }
]

"market_b_sells" = [
  { "price": ".49", "size": "60" }, # Original 0.48 @ 10 is removed because we bought it all
  { "price": ".54", "size": "10" }
]
```

Here we match up:
```
a for 15 @ 0.47
b for 15 @ 0.49
```

When there are no more possible under $1 matches, we stop and batch create orders:

```
resulting_orders = [
[   {'market': 'b', 'price': 0.48, 'size': 10, 'type': 'buy'},
    {'market': 'a', 'price': 0.47, 'size': 10, 'type': 'buy'},

    {'market': 'a', 'price': 0.47, 'size': 15, 'type': 'buy'},
    {'market': 'b', 'price': 0.49, 'size': 15, 'type': 'buy'}
]
```

Theoretical profit from this example:
```
a = 1 - (0.48 + 0.47) * 10 = $0.50
b = 1 - (0.49 + 0.47) * 15 = $0.60
a + b = $1.10

invested_a = ($0.48 * 10) + ($0.47 * 10) = $14.40
invested_b = ($0.49 * 15) + ($0.47 * 15) = $9.50

invested_a + invested_b = $23.90

return = $1.10 / $23.90 = 4%
```
c


## Scratch

[
    #{ "price": ".47", "size": "25" },
    { "price": ".47", "size": "15" },
    { "price": ".53", "size": "60" },
    { "price": ".54", "size": "10" }
]

[
   #{ "price": ".48", "size": "10" },
    { "price": ".49", "size": "60" },
    { "price": ".54", "size": "10" }
]

    question_a_data = {
      "event_type": "book",
      "asset_id": "a",
      "market": "ma",
      "buys": [
        { "price": ".48", "size": "30" },
        { "price": ".49", "size": "20" },
        { "price": ".50", "size": "15" }
      ],
      "sells": [
        { "price": ".47", "size": "25" },
        { "price": ".53", "size": "60" },
        { "price": ".54", "size": "10" }
      ],
      "timestamp": "123456789000",
    }

    question_b_data = {
      "event_type": "book",
      "asset_id": "b",
      "market": "mb",
      "buys": [
        { "price": ".46", "size": "10" },
        { "price": ".49", "size": "20" },
        { "price": ".50", "size": "15" }
      ],
      "sells": [
        { "price": ".48", "size": "10" },
        { "price": ".49", "size": "60" },
        { "price": ".54", "size": "10" }
      ],
      "timestamp": "123456789000",
    }
