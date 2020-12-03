from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass
from result import Ok, Result
from typing_extensions import Literal

# Ref : https://binance-docs.github.io/apidocs/spot/en/#filters


@dataclass(frozen=True)
class Filter:
    filter_type: str

    @classmethod
    def strategy_symbol(cls) -> SearchStrategy:
        """ only generating possibly valid filter, as per the binance doc"""
        possible_strats = [
            PriceFilter.strategy(),
            PercentPrice.strategy(),
            LotSize.strategy(),
            MinNotional.strategy(),
            IcebergParts.strategy(),
            MarketLotSize.strategy(),
            MaxNumOrders.strategy(),
            MaxNumAlgoOrders.strategy(),
            MaxNumIcebergOrders.strategy(),
            MaxPosition.strategy(),
        ]

        return st.one_of(possible_strats)

    @classmethod
    def strategy_exchange(cls) -> SearchStrategy:
        possible_strats = [
            ExchangeMaxNumOrders.strategy(),
            ExchangeMaxAlgoOrders.strategy(),
        ]

        return st.one_of(possible_strats)

    @staticmethod
    def factory(**kwargs):
        #  a kind of abstract factory...
        if kwargs["filter_type"] == "PRICE_FILTER":
            return PriceFilter(**kwargs)
        elif kwargs["filter_type"] == "PERCENT_PRICE":
            return PercentPrice(**kwargs)
        elif kwargs["filter_type"] == "LOT_SIZE":
            return LotSize(**kwargs)
        elif kwargs["filter_type"] == "MIN_NOTIONAL":
            return MinNotional(**kwargs)
        elif kwargs["filter_type"] == "ICEBERG_PARTS":
            return IcebergParts(**kwargs)
        elif kwargs["filter_type"] == "MARKET_LOT_SIZE":
            return MarketLotSize(**kwargs)
        elif kwargs["filter_type"] == "MAX_NUM_ORDERS":
            return MaxNumOrders(**kwargs)
        elif kwargs["filter_type"] == "MAX_NUM_ALGO_ORDERS":
            return MaxNumAlgoOrders(**kwargs)
        elif kwargs["filter_type"] == "MAX_NUM_ICEBERG_ORDERS":
            return MaxNumIcebergOrders(**kwargs)
        elif kwargs["filter_type"] == "MAX_POSITION":
            return MaxPosition(**kwargs)
        elif kwargs["filter_type"] == "EXCHANGE_MAX_NUM_ORDERS":
            return ExchangeMaxNumOrders(**kwargs)
        elif kwargs["filter_type"] == "EXCHANGE_MAX_ALGO_ORDERS":
            return ExchangeMaxAlgoOrders(**kwargs)
        else:
            raise RuntimeError("Unknown filter type...")


@dataclass(frozen=True)
class PriceFilter(Filter):

    filter_type: Literal["PRICE_FILTER"]
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    tick_size: Optional[Decimal] = None

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            min_price=st.one_of(
                st.none(), st.decimals(allow_nan=False, allow_infinity=False)
            ),
            max_price=st.one_of(
                st.none(), st.decimals(allow_nan=False, allow_infinity=False)
            ),
            tick_size=st.one_of(
                st.none(), st.decimals(allow_nan=False, allow_infinity=False)
            ),
        )


@dataclass(frozen=True)
class PercentPrice(Filter):
    filter_type: Literal["PERCENT_PRICE"]
    multiplier_up: Decimal
    multiplier_down: Decimal
    avg_price_mins: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            multiplier_up=st.decimals(allow_nan=False, allow_infinity=False),
            multiplier_down=st.decimals(allow_nan=False, allow_infinity=False),
            avg_price_mins=st.integers(),
        )


@dataclass(frozen=True)
class LotSize(Filter):
    filter_type: Literal["LOT_SIZE"]
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            min_qty=st.decimals(allow_nan=False, allow_infinity=False),
            max_qty=st.decimals(allow_nan=False, allow_infinity=False),
            step_size=st.decimals(allow_nan=False, allow_infinity=False),
        )


@dataclass(frozen=True)
class MinNotional(Filter):
    filter_type: Literal["MIN_NOTIONAL"]
    min_notional: Decimal
    apply_to_market: bool
    avg_price_mins: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            min_notional=st.decimals(allow_nan=False, allow_infinity=False),
            apply_to_market=st.booleans(),
            avg_price_mins=st.integers(),
        )


@dataclass(frozen=True)
class IcebergParts(Filter):
    filter_type: Literal["ICEBERG_PARTS"]
    limit: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            limit=st.integers(),
        )


@dataclass(frozen=True)
class MarketLotSize(Filter):
    filter_type: Literal["MARKET_LOT_SIZE"]
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            min_qty=st.decimals(allow_nan=False, allow_infinity=False),
            max_qty=st.decimals(allow_nan=False, allow_infinity=False),
            step_size=st.decimals(allow_nan=False, allow_infinity=False),
        )


@dataclass(frozen=True)
class MaxNumOrders(Filter):
    filter_type: Literal["MAX_NUM_ORDERS"]
    max_num_orders: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_num_orders=st.integers(),
        )


@dataclass(frozen=True)
class MaxNumAlgoOrders(Filter):
    filter_type: Literal["MAX_NUM_ALGO_ORDERS"]
    max_num_algo_orders: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_num_algo_orders=st.integers(),
        )


@dataclass(frozen=True)
class MaxNumIcebergOrders(Filter):
    filter_type: Literal["MAX_NUM_ICEBERG_ORDERS"]
    max_num_iceberg_orders: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_num_iceberg_orders=st.integers(),
        )


@dataclass(frozen=True)
class MaxPosition(Filter):
    filter_type: Literal["MAX_POSITION"]
    max_position: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_position=st.decimals(allow_nan=False, allow_infinity=False),
        )


@dataclass(frozen=True)
class ExchangeMaxNumOrders(Filter):
    filter_type: Literal["EXCHANGE_MAX_NUM_ORDERS"]
    max_num_orders: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_num_orders=st.integers(),
        )


@dataclass(frozen=True)
class ExchangeMaxAlgoOrders(Filter):
    filter_type: Literal["EXCHANGE_MAX_ALGO_ORDERS"]
    max_num_algo_orders: int

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            max_num_algo_orders=st.integers(),
        )


if __name__ == "__main__":
    print(Filter.strategy_symbol().example())
    print(Filter.strategy_exchange().example())
