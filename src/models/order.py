from dataclasses import dataclass, asdict, fields, replace
from enum import Enum
from typing import Dict, Any, Optional, List, Self

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

    TODO: Revisit data structure

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
    timestamp: int # Created at timestamp
    order_id: Optional[str] = None
    status: Optional[str] = None
    success: Optional[bool] = None
    error_msg: Optional[str] = None
    making_amount: Optional[float] = None
    taking_amount: Optional[float] = None
    posted_at_timestamp: Optional[int] = None
    # calculated_at: datetime TODO: Add

    # TODO: Is there a way to make this a constant thats only calculated once
    # at runtime?
    @classmethod
    def field_names(cls) -> List[str]:
        return [field.name for field in fields(cls)]

    def asdict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['side'] = self.side.value
        data['order_type'] = self.order_type.value
        return data

    """
        TODO: I don't love this pattern. Would probably be better to just
        seperate the tables into an Order and an OrderExecution rather than
        combine and have one process produce an incomplete order and another process
        update the order to make it complete

        On the flip side, it'll be easier to query because we can see exactly what
        did and didn't result in an actualy posted order
    """
    def with_post_success(self,
        order_id: str,
        status: str,
        making_amount: float,
        taking_amount: float,
        posted_at_timestamp: int) -> Self:

        return replace(self,
            success=True,
            order_id=order_id,
            status=status,
            making_amount=making_amount,
            taking_amount=taking_amount,
            posted_at_timestamp=posted_at_timestamp
        )


    def with_post_failure(self,
        error_msg: str,
        status: Optional[str],
        posted_at_timestamp: int) -> Self:

        return replace(self,
            success=False,
            error_msg=error_msg,
            status=status,
            posted_at_timestamp=posted_at_timestamp
        )


