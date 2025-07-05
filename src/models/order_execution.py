from dataclasses import dataclass, asdict
from src.models import OrderSide, OrderType
from typing import Optional, Dict, Any

@dataclass
class OrderExecution():
    """Result of an order execution attempt."""
    market_slug: str
    market_id: int
    asset_id: str
    outcome_name: str
    side: OrderSide
    order_type: OrderType
    price: float
    size: float
    order_id: str
    status: str
    timestamp: int
    success: bool
    error_msg: Optional[str]
    making_amount: Optional[float]
    taking_amount: Optional[float]

    def asdict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['side'] = self.side.value
        data['order_type'] = self.order_type.value
        return data
