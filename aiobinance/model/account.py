# {
#   "makerCommission": 15,
#   "takerCommission": 15,
#   "buyerCommission": 0,
#   "sellerCommission": 0,
#   "canTrade": true,
#   "canWithdraw": true,
#   "canDeposit": true,
#   "updateTime": 123456789,
#   "accountType": "SPOT",
#   "balances": [
#     {
#       "asset": "BTC",
#       "free": "4723846.89208129",
#       "locked": "0.00000000"
#     },
#     {
#       "asset": "LTC",
#       "free": "4763368.68006011",
#       "locked": "0.00000000"
#     }
#   ],
#   "permissions": [
#     "SPOT"
#   ]
# }

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pprint import pprint
from typing import List, Optional

import numpy as np
from pydantic.dataclasses import dataclass


@dataclass
class AssetAmount:
    asset: str  # should only allow known assets
    free: Decimal
    locked: Decimal

    def __str__(self):
        return f"{self.free + self.locked} {self.asset} (free: {self.free}, locked: {self.locked})"


# Leveraging pydantic to validate based on type hints
@dataclass
class Account:
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
    balances: List[AssetAmount]
    permissions: List[str]

    # TODO : validate to not have balance of (0, 0) for an asset...

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
            accstr += """
buyerCommission: {self.buyerCommission}
"""
        if self.sellerCommission > 0:
            accstr += """
sellerCommission: {self.sellerCommission}
"""
        return accstr
