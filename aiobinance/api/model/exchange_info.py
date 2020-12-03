# TODO : store exchange information (including FIXED current time)
#  a pure ExchangeBase will have testable, deterministic, side-effect-free, computation
#  a Exchange child class will implement effectful (dynamic time adjustment, etc.) behavior.
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass

from aiobinance.api.model.filters import Filter
from aiobinance.api.model.market_info import MarketInfo


@dataclass(frozen=True)
class RateLimit:
    rate_limit_type: str
    interval: str
    interval_num: int
    limit: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            rate_limit_type=st.sampled_from(
                ["REQUEST_WEIGHT", "ORDERS", "RAW_REQUESTS"]
            ),
            interval=st.sampled_from(["SECOND", "MINUTE", "HOUR", "DAY"]),
            interval_num=st.integers(min_value=0),
            limit=st.integers(min_value=0),
        )


# Leveraging pydantic to validate based on type hints
@dataclass(frozen=True)
class ExchangeInfo:
    servertime: datetime  # with timezone !

    rate_limits: List[RateLimit]

    exchange_filters: List[Filter]

    symbols: List[MarketInfo]

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            servertime=st.datetimes(
                timezones=st.just(timezone.utc)
            ),  # only utc servertime
            rate_limits=st.lists(
                elements=RateLimit.strategy(),
                max_size=3,
                unique_by=lambda i: i.rate_limit_type,
            ),
            exchange_filters=st.lists(
                elements=Filter.strategy_exchange(),
                max_size=2,
                unique_by=lambda i: i.filter_type,
            ),
            symbols=st.lists(
                elements=MarketInfo.strategy(), max_size=5, unique_by=lambda i: i.symbol
            ),
        )


if __name__ == "__main__":

    ei = ExchangeInfo.strategy().example()
    print(ei)
