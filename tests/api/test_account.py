import pytest

import aiobinance.binance
from aiobinance.api.account import Account
from aiobinance.api.rawapi import Binance


@pytest.mark.asyncio
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
async def test_balance_from_binance(keyfile):
    """ get binance balances"""

    api = Binance(credentials=keyfile)  # we need private requests here !

    account = Account(api=api, test=True)
    assert isinstance(account, Account)
    assert account.info is None

    await account()  # update from actual data !

    assert isinstance(account, Account)
    assert account.info is not None

    assert account.info.accountType == "SPOT"

    # property !
    assert account.balances == {
        b.asset: b
        for b in account.info.balances
        if not (
            b.free.is_zero() and b.locked.is_zero()
        )  # we dont want empty balances to appear !
    }
    assert len(account.balances) == 6

    assert account.info.buyerCommission == 0
    assert account.info.canDeposit is True
    assert account.info.canTrade is True
    assert account.info.canWithdraw is True
    assert account.info.makerCommission == 10
    assert "SPOT" in account.info.permissions
    assert account.info.sellerCommission == 0
    assert account.info.takerCommission == 10

    # cached property !
    assert account.info.updateTime == account.update_time
    assert hasattr(account.info, "updateTime")


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
