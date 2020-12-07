from __future__ import annotations

from dataclasses import dataclass, field
from datetime import MINYEAR, datetime
from typing import List, Optional

import hypothesis.strategies as st
from cached_property import cached_property
from hypothesis.strategies import SearchStrategy

from aiobinance.api.model.account_info import AccountInfo, AssetAmount


@dataclass(frozen=False)
class AccountBase:

    info: Optional[AccountInfo] = field(init=True, default=None)

    @classmethod
    def strategy(
        cls, info=st.one_of(st.none(), AccountInfo.strategy()), **kwargs
    ) -> SearchStrategy:
        return st.builds(cls, info=info)

    @cached_property
    def update_time(self) -> datetime:  # monotonically increase -> start in the past.
        return (
            self.info.updateTime
            if self.info is not None
            else datetime(year=MINYEAR, month=1, day=1)
        )

    @cached_property
    def balances(
        self,
    ) -> List[AssetAmount]:  # monotonically increase -> start in the past.
        return self.info.balances if self.info is not None else []

    def __call__(self, *, info: Optional[AccountInfo] = None, **kwargs) -> AccountBase:
        # return same instance if no change
        if info is None:
            return self

        popping = []
        if self.info is None:
            # because we may have cached invalid values from initialization (self.info was None)
            popping.append("update_time")
            popping.append("balances")
        else:  # otherwise we detect change with equality on frozen dataclass fields
            if self.info.updateTime != info.updateTime:
                popping.append("update_time")
            if self.info.balances != info.balances:
                popping.append("balances")

        # updating by updating data
        self.info = info

        # and invalidating related caches
        for p in popping:
            self.__dict__.pop(p, None)

        # returning self to allow chaining
        return self


if __name__ == "__main__":
    eb = AccountBase.strategy().example()
    print(eb)
    eb_updated = eb(info=AccountInfo.strategy().example())
    print(eb_updated)
