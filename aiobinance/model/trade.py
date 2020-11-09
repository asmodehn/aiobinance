from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import numpy as np
import pandas as pd
from pydantic import validator
from pydantic.dataclasses import dataclass

# Leveraging pydantic to validate based on type hints
from tabulate import tabulate


@dataclass
class Trade:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    time: datetime
    symbol: str  # TODO : improve
    id: int
    price: Decimal
    qty: Decimal
    quote_qty: Decimal
    commission: Decimal
    commission_asset: str  # TODO : improve
    is_buyer: bool
    is_maker: bool

    order_id: Optional[
        int
    ] = None  # some source (hummingbot) might not have the accurate int... # TODO : investigate...
    order_list_id: Optional[
        int
    ] = None  # None replaces the cryptic '-1' of binance data when not part of a list TODO!!
    is_best_match: Optional[
        bool
    ] = None  # outside of binance, we might not have this information

    @validator("time", pre=True)
    def convert_pandas_timestamp(cls, v):
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()
        return v


class TradeFrame:
    _df: pd.DataFrame

    def __init__(self, *trades: Trade):
        # Here we follow binance format and enforce proper python types

        df = pd.DataFrame.from_records([asdict(dc) for dc in trades])

        self._df = df

    def __getitem__(self, item: int):  # TODO : slice
        if item < len(self._df):
            return Trade(**self._df.iloc[item])
        elif item in self._df.id:
            return Trade(**self._df[self._df.id == item])
        else:
            raise KeyError(f"No Trade with index {item} or id {item}")

    # NO SETTING ON TRADES :they are immutable events.

    def __iter__(self):
        return (Trade(**t._asdict()) for t in self._df.itertuples(index=False))

    def __len__(self):
        return len(self._df)

    def __str__(self):
        return tabulate(self._df, headers="keys", tablefmt="psql")
