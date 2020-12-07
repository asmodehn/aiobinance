from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from hypothesis.strategies import SearchStrategy

from aiobinance.api.model.account_info import AccountInfo
from aiobinance.api.pure.accountbase import AccountBase
from aiobinance.api.rawapi import Binance


@dataclass(frozen=False)
class Account(AccountBase):

    """ A class to simplify interacting with binance account through the REST API."""

    api: Binance = field(init=True, default=Binance())
    test: bool = field(init=True, default=True)

    @classmethod
    def strategy(cls, **kwargs) -> SearchStrategy:
        raise RuntimeError(
            "Strategy should not be used with real implementation. Build an instance from actual data instead."
        )

    # interactive behavior

    async def __call__(
        self, *, update_delta: Optional[timedelta] = None, **kwargs
    ) -> Account:

        # TMP simulating future async api...
        await asyncio.sleep(0.1)

        info = kwargs.get(
            "info", None
        )  # we get the info param as override if present in kwargs

        if info is None:

            if self.api.creds is None:
                raise RuntimeError("Credentials not specified !")

            res = self.api.call_api(command="account")

            if res.is_ok():
                res = res.value
            else:
                # TODO : handle API error properly
                raise RuntimeError(res.value)

            # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
            # We do not want to change the semantics of the exchange exposed models here.
            info = AccountInfo(
                makerCommission=res["makerCommission"],
                takerCommission=res["takerCommission"],
                buyerCommission=res["buyerCommission"],
                sellerCommission=res["sellerCommission"],
                canTrade=res["canTrade"],
                canWithdraw=res["canWithdraw"],
                canDeposit=res["canDeposit"],
                updateTime=res["updateTime"],
                accountType=res["accountType"],  # should be "SPOT"
                balances=res["balances"],
                permissions=res["permissions"],
            )

            # we update the current frozen instance (base class know how to)
            super(Account, self).__call__(info=info)

        return self


if __name__ == "__main__":

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())

    # Testing with actual values and network connection here (only retrieving information)
    acc = Account(api=api, test=True)
    now = datetime.now(tz=timezone.utc)

    async def run_accnt():
        global now
        print(f"update_time: {acc.update_time}")
        print(f"now: {now}")

        newnow = datetime.now(tz=timezone.utc)
        await acc(update_delta=newnow - now)
        print(f"update_time: {acc.update_time}")
        now = newnow
        print(f"now: {now}")

        # TODO : something needs to happen for the account to get updated and get a new updated time...
        await asyncio.sleep(1)

        newnow = datetime.now(tz=timezone.utc)
        await acc(update_delta=newnow - now)
        print(f"update_time: {acc.update_time}")
        now = newnow
        print(f"now: {now}")

    asyncio.run(run_accnt())
