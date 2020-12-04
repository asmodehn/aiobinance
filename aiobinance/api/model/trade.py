from __future__ import annotations

from dataclasses import asdict, field, fields
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Union

import hypothesis.strategies as st
import numpy as np
import pandas as pd
from hypothesis.strategies import composite
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate


@dataclass(frozen=True)
class Trade:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    time: datetime
    symbol: str  # TODO : improve
    id: int  # TODO : careful there is a sup bound here to allow this as a DAtaFrame Index for easy manipulation...
    # cf: TypeError: cannot do slice indexing on Index with these indexers [18446744073709551615] of type int
    # cf:  E   OverflowError: Python int too large to convert to C long # pandas/_libs/hashtable_class_helper.pxi:1032: OverflowError
    price: Decimal
    qty: Decimal
    quote_qty: Decimal
    commission: Decimal
    commission_asset: str  # TODO : improve
    is_buyer: bool
    is_maker: bool

    order_id: Optional[int] = field(
        init=True, default=None
    )  # some source (hummingbot) might not have the accurate int... # TODO : investigate...
    order_list_id: Optional[int] = field(
        init=True, default=None
    )  # None replaces the cryptic '-1' of binance data when not part of a list TODO!!
    is_best_match: Optional[bool] = field(
        init=True, default=None
    )  # outside of binance, we might not have this information

    @validator("time", pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v

    @classmethod
    def strategy(cls):
        return st.builds(
            cls,
            id=st.integers(
                min_value=1000
            ),  # to avoid overlap of index and ids integers... TODO : validate in real usecase...
            price=st.decimals(allow_nan=False, allow_infinity=False),
            qty=st.decimals(allow_nan=False, allow_infinity=False),
            quote_qty=st.decimals(allow_nan=False, allow_infinity=False),
            commission=st.decimals(allow_nan=False, allow_infinity=False),
        )

    def __str__(self) -> str:
        s = f"""
time: {self.time}
symbol: {self.symbol}
id: {self.id}
price: {self.price}
qty: {self.qty}
quote_qty: {self.quote_qty}
commission: {self.commission} {self.commission_asset}
is_buyer: {self.is_buyer}
is_maker: {self.is_maker}
order_id: {self.order_id}
order_list_id: {self.order_list_id}
is_best_match: {self.is_best_match}
"""
        return s

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]


if __name__ == "__main__":

    print(Trade.strategy().example())
