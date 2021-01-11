# For : https://binance-docs.github.io/apidocs/spot/en/#all-coins-39-information-user_data
from decimal import Decimal
from typing import List, Optional

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInfo:

    addressRegex: str
    coin: str
    depositDesc: Optional[str]
    depositEnable: bool
    isDefault: bool
    memoRegex: str
    minConfirm: int
    name: str
    network: str
    resetAddressStatus: bool
    specialTips: Optional[str]
    unlockConfirm: Optional[int]
    withdrawDesc: Optional[str]
    withdrawEnable: bool
    withdrawIntegerMultiple: Decimal
    withdrawFee: Decimal
    withdrawMin: Decimal
    withdrawMax: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(NetworkInfo)


@dataclass(frozen=True)
class AssetInfo:

    coin: str
    depositAllEnable: bool
    free: Decimal
    freeze: Decimal
    ipoable: Decimal
    ipoing: Decimal
    isLegalMoney: bool
    locked: Decimal
    name: str
    networkList: List[NetworkInfo]
    storage: Decimal
    trading: bool
    withdrawAllEnable: bool
    withdrawing: Decimal

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(AssetInfo)


if __name__ == "__main__":
    print(AssetInfo.strategy().example())
