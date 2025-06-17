from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class OrderSignal(Enum):
    LIMIT_BUY = "LIMIT_BUY"
    LIMIT_SELL = "LIMIT_SELL"

@dataclass
class OrderEvent:
    timestamp: datetime
    order_signal: OrderSignal
    price: float
    size: int

