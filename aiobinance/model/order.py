from dataclasses import asdict, fields
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints

""" This module defined order datastructure, as returned by binance.
NOT the information we need to send to the exchange...
"""


@dataclass
class OrderFill:
    price: Decimal
    qty: Decimal
    commission: Decimal
    commissionAsset: str  # TODO : improve...
    tradeId: int


@dataclass
class Order:  # TODO : probably better to split in various python types...
    symbol: str
    side: str
    type: str

    order_id: int
    order_list_id: int
    clientOrderId: str
    transactTime: int

    origQty: Decimal
    executedQty: Decimal
    cummulativeQuoteQty: Decimal
    status: str

    fills: List[OrderFill]


@dataclass
class MarketOrder(Order):
    # TODO : enforce that one or the other must be set

    quoteOrderQty: Optional[Decimal] = None


@dataclass
class LimitOrder(Order):
    timeInForce: str

    price: Decimal
    icebergQty: Optional[Decimal] = None


@dataclass
class StopLossOrder(Order):

    stopPrice: Decimal


@dataclass
class StopLossLimitOrder(
    Order
):  # Child of LimitOrder, or StopLossOrder ? none , both ?

    timeInForce: str

    price: Decimal
    stopPrice: Decimal
    icebergQty: Optional[Decimal] = None


@dataclass
class TakeProfitOrder(Order):

    stopPrice: Decimal


@dataclass
class TakeProfitLimitOrder(
    Order
):  # Child of LimitOrder, or TakeProfitOrder ? none , both ?

    timeInForce: str

    price: Decimal
    stopPrice: Decimal
    icebergQty: Optional[Decimal] = None
