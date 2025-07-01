from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any

class OrderType(Enum):
    FOK = "FOK"
    """Fill-Or-Kill: Must fill all shares at price or cancel the order."""
    FAK = "FAK"
    """Fill-And-Kill: Must fill all that can be filled and cancel the rest."""
    GTC = "GTC"
    """Good-Til-Cancelled: Limit order that remains active until cancelled."""
    GTD = "GTD"
    """Good-Til-Date: Limit order that remains active until specific date."""

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Order:
    """
    Represents an Order that we have or intend to place

    Attributes:
    """
    market_slug: str
    market_id: int
    asset_id: str
    outcome_name: str
    side: OrderSide
    order_type: OrderType
    price: float
    size: float
    timestamp: int

    def asdict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['side'] = self.side.value
        data['order_type'] = self.order_type.value
        return data


