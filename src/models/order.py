from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any

class OrderType(Enum):
    LIMIT_BUY = "LIMIT_BUY"
    LIMIT_SELL = "LIMIT_SELL"

@dataclass
class Order:
    asset_id: int
    #market: str
    market_slug: str
    order_type: OrderType
    price: float
    size: float
    timestamp: int

    def asdict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert OrderType enum to its string value
        data['order_type'] = self.order_type.value
        return data


