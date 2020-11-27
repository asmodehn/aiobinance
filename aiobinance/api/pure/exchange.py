from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic.dataclasses import dataclass

from aiobinance.api.pure.filters import Filter
from aiobinance.api.pure.puremarket import PureMarket


@dataclass
class RateLimit:
    rate_limit_type: str
    interval: str
    interval_num: int
    limit: int


# Leveraging pydantic to validate based on type hints
@dataclass
class Exchange:

    servertime: datetime  # with timezone !

    rate_limits: List[RateLimit]

    exchange_filters: List[Filter]

    symbols: List[PureMarket]