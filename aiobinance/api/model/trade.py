from __future__ import annotations

from dataclasses import asdict, field, fields
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from typing import Iterable, List, Optional, Tuple, Union

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
    # TODO : directly use numpy dtypes here in hints instead of specific as_dtype() method ?
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    time_utc: datetime  # Making it obvious that time here is meant to be utc, even if datetime is naive like with numpy
    symbol: str  # TODO : improve
    id: int
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

    @validator("time_utc", pre=True)
    def convert_pandas_timestamp(
        cls, v: Union[float, int, datetime, np.datetime64, pd.Timestamp]
    ) -> datetime:  # TODO : rename

        if isinstance(v, int):  # timestamp [ns]
            v = datetime.fromtimestamp(
                v * 0.001, tz=timezone.utc
            )  # assume original timestamp is in [ns] on UTC
            # TODO : probably storing raw data in dataframe before conversion would be a good idea...
            #  Pb : how to check validity...
        if isinstance(v, float):  # timestamp [us] (from python)
            v = datetime.fromtimestamp(v, tz=timezone.utc)

        # making datetime tz-offset aware on UTC if needed
        if isinstance(v, datetime):
            if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
                # naive => assume already UTC (no conversion)
                v = v.replace(tzinfo=timezone.utc)
            elif v.tzinfo != timezone.utc:  # aware and need conversion
                # force conversion to utc (before stripping it in numpy)
                v = v.astimezone(tz=timezone.utc)

        # something else ? => rely on pandas for conversion until a better solution appears...
        if isinstance(v, np.datetime64):
            # because numpy doesnt have a proper datetime conversion story
            # but pandas does...
            v = pd.Timestamp(v, tz=timezone.utc)

        if isinstance(v, pd.Timestamp):  # TODO  :timezone ?
            v = v.to_pydatetime()

        if not isinstance(v, datetime):
            raise TypeError(f"{v} is not a datetime")
        lowbound = pd.Timestamp.min.replace(tzinfo=timezone.utc).to_pydatetime()
        highbound = pd.Timestamp.max.replace(tzinfo=timezone.utc).to_pydatetime()
        if v < lowbound or v > highbound:
            raise ValueError(
                f"{v} is not in pandas.Timestamp bounds [{pd.Timestamp.min.to_pydatetime()}..{pd.Timestamp.max.to_pydatetime()}]"
            )
        return v

    @validator("id", pre=True)
    def check_id(cls, v: Union[int, np.uint64]) -> int:
        if isinstance(v, np.uint64):
            v = int(v)
        if not isinstance(v, int):
            raise TypeError(f"{v} is not an int")
        if v < np.iinfo(np.dtype("uint64")).min or v > np.iinfo(np.dtype("uint64")).max:
            raise ValueError(
                f"{v} is not in numpy.uint64 bounds [{np.iinfo(np.dtype('uint64')).min}..{np.iinfo(np.dtype('uint64')).max}]"
            )
        return v

    @classmethod  # actually property of the class itself -> metaclass (see datacrytals...)
    def as_dtype(cls) -> List[Tuple[str, np.dtype]]:
        """ Interpretation of this dataclass as dtype for optimizations with numpy """
        # Ref : https://numpy.org/devdocs/reference/arrays.dtypes.html#arrays-dtypes-constructing
        specified = {
            "time_utc": np.dtype(
                "datetime64[ns]"
            ),  # CAREFUL : timezone naive since numpy 1.11.0
            # Note: datetime64[ms] is usual server timestamp, but not enough precise for python [us]
            # Note: datetime64[ns] is the enforced format for pandas datetime/timestamp, but more precise than python [us]
            "id": np.dtype("uint64"),
        }
        # TODO : min/max properties on the type itself...
        # TODO : more strict column dtypes !

        # CAREFUL order needs to match fields order here...
        return [
            (f.name, specified[f.name])
            if f.name in specified
            else (f.name, np.dtype("O"))
            for f in fields(cls)
        ]

    @classmethod
    def strategy(cls):
        return st.builds(
            cls,
            time_utc=st.datetimes(
                min_value=pd.Timestamp.min.to_pydatetime(),
                max_value=pd.Timestamp.max.to_pydatetime(),
            ),
            id=st.integers(
                # for proper dataframe storage, we should stay in numpy representables int...
                min_value=np.iinfo(np.dtype("uint64")).min,
                max_value=np.iinfo(np.dtype("uint64")).max,
            ),  # to avoid overlap of index and ids integers... TODO : validate in real usecase...
            price=st.decimals(allow_nan=False, allow_infinity=False),
            qty=st.decimals(allow_nan=False, allow_infinity=False),
            quote_qty=st.decimals(allow_nan=False, allow_infinity=False),
            commission=st.decimals(allow_nan=False, allow_infinity=False),
        )

    def __str__(self) -> str:
        s = f"""
time_utc: {self.time_utc}
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
