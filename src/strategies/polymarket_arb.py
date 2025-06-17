from typing import Dict, Any, List


#[
#    #{ "price": ".47", "size": "25" },
#    { "price": ".47", "size": "15" },
#    { "price": ".53", "size": "60" },
#    { "price": ".54", "size": "10" }
#]
#
#[
#   #{ "price": ".48", "size": "10" },
#    { "price": ".49", "size": "60" },
#    { "price": ".54", "size": "10" }
#]

#def build_orders(market_a_data: Dict[str, Any], market_b_data: Dict[str, Any]):
def build_orders():
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
    s_a = sorted(question_a_data["sells"], key=lambda item: item["price"])
    s_b = sorted(question_b_data["sells"], key=lambda item: item["price"])

    s_a = [{"price": float(i["price"]), "size": int(i["size"])} for i in s_a]
    s_b = [{"price": float(i["price"]), "size": int(i["size"])} for i in s_b]

    return _recurs_build_orders(s_a, s_b)


def _recurs_build_orders(a_sells: List[Any], b_sells: List[Any]) -> List[Any]:
    orders = []

    if a_sells and b_sells:
        a = a_sells[0]
        b = b_sells[0]

        total = a["price"] + b["price"]
        if total < 1:
            if a["size"] < b["size"]:
                orders.extend(
                    [{"type": "buy", "size": a["size"], "market": "a", "price": a["price"]},
                     {"type": "buy", "size": a["size"], "market": "b", "price": b["price"]}]
                )
                b_sells[0] = {**b, "size": b_sells[0]["size"] - a["size"]}
                orders.extend(_recurs_build_orders(a_sells[1:], b_sells))

            if b["size"] < a["size"]:
                orders.extend(
                    [{"type": "buy", "size": b["size"], "market": "b", "price": b["price"]},
                     {"type": "buy", "size": b["size"], "market": "a", "price": a["price"]}]
                )
                a_sells[0] = {**a, "size": a_sells[0]["size"] - b["size"]}
                orders.extend(_recurs_build_orders(a_sells, b_sells[1:]))

    return orders













