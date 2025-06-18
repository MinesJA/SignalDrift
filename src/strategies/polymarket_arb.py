from typing import Dict, Any, List

#def build_orders(market_a_data: Dict[str, Any], market_b_data: Dict[str, Any]):
def build_orders(data_a, data_b):
    s_a = sorted(data_a["orders"], key=lambda item: item["price"])
    s_b = sorted(data_b["orders"], key=lambda item: item["price"])

    return _recurs_build_orders(data_a["asset_id"], s_a, data_b["asset_id"], s_b)


def _recurs_build_orders(a_assetId: str, a_orders: List[Any], b_assetId: str, b_orders: List[Any]) -> List[Any]:
    orders = []

    if a_orders and b_orders:
        a = a_orders[0]
        b = b_orders[0]

        total = a["price"] + b["price"]
        if total < 1:
            if a["size"] < b["size"] and a["size"] >= 1:
                size = a["size"]
                orders.extend(
                    [{"side": "bid", "size": size, "asset_id": a_assetId, "price": a["price"]},
                     {"side": "bid", "size": size, "asset_id": b_assetId, "price": b["price"]}]
                )
                b_orders[0] = {**b, "size": b_orders[0]["size"] - a["size"]}
                orders.extend(_recurs_build_orders(a_assetId, a_orders[1:], b_assetId, b_orders))

            if b["size"] < a["size"] and b["size"] >= 1:
                size = b["size"]
                orders.extend(
                    [{"side": "bid", "size": size, "asset_id": b_assetId, "price": b["price"]},
                     {"side": "bid", "size": size, "asset_id": a_assetId, "price": a["price"]}]
                )
                a_orders[0] = {**a, "size": a_orders[0]["size"] - b["size"]}
                orders.extend(_recurs_build_orders(a_assetId, a_orders, b_assetId, b_orders[1:]))

    return orders














