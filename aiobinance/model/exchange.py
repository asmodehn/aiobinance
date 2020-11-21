from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Filter:

    filter_type: str
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    tick_size: Optional[Decimal] = None


@dataclass
class RateLimit:
    rate_limit_type: str
    interval: str
    interval_num: int
    limit: int


@dataclass
class Symbol:

    # TODO   a lot of str can be changed to enum and properly type checked.
    symbol: str
    status: str
    base_asset: str
    base_asset_precision: int
    quote_asset: str
    quote_precision: int
    quote_asset_precision: int

    base_commission_precision: int
    quote_commission_precision: int

    order_types: List[str]

    iceberg_allowed: bool
    oco_allowed: bool
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    quote_order_qty_market_allowed: bool

    filters: List[Filter]

    permissions: List[str]


# Leveraging pydantic to validate based on type hints
@dataclass
class Exchange:

    servertime: datetime  # with timezone !

    rate_limits: List[RateLimit]

    exchange_filters: List[Filter]

    symbols: List[Symbol]
