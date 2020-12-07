from dataclasses import asdict, fields
from datetime import datetime
from decimal import Decimal
from pprint import pprint
from typing import Iterable, List, Optional

import hypothesis.strategies as st
import numpy as np
from hypothesis import infer
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass


@dataclass
class AssetAmount:
    asset: str  # should only allow known assets
    free: Decimal
    locked: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            AssetAmount,
            free=st.decimals(allow_nan=False, allow_infinity=False),
            locked=st.decimals(allow_nan=False, allow_infinity=False),
        )

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]

    def __str__(self):
        return f"{self.free + self.locked} {self.asset} (free: {self.free}, locked: {self.locked})"


# Leveraging pydantic to validate based on type hints
@dataclass
class AccountInfo:
    # REMINDER : as 'precise' and 'pythonic' semantic as possible
    makerCommission: int
    takerCommission: int
    buyerCommission: int
    sellerCommission: int
    canTrade: bool
    canWithdraw: bool
    canDeposit: bool
    updateTime: datetime
    accountType: str  # should be "SPOT"
    balances: List[
        AssetAmount
    ]  # TODO : validate to not have balance of (0, 0) for an asset...
    permissions: List[str]

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            AccountInfo, balances=st.lists(elements=AssetAmount.strategy())
        )

    def __dir__(self) -> Iterable[str]:
        # hiding private methods and data validators
        return [f.name for f in fields(self)]

    def __str__(self):
        accstr = f"""
accountType: {self.accountType}
canTrade: {self.canTrade}
canWithdraw: {self.canWithdraw}
canDeposit: {self.canDeposit}
"""

        accstr += """balances:
""" + "\n".join(
            [" - " + str(a) for a in self.balances if not (a.free + a.locked).is_zero()]
        )

        accstr += f"""
updateTime: {self.updateTime}
permissions: {self.permissions}
makerCommission: {self.makerCommission}
takerCommission: {self.takerCommission}
"""
        if self.buyerCommission > 0:
            accstr += f"""
buyerCommission: {self.buyerCommission}
"""
        if self.sellerCommission > 0:
            accstr += f"""
sellerCommission: {self.sellerCommission}
"""
        return accstr
