import unittest

from hypothesis import given

from aiobinance.api.pure.account import (
    Account,
    AssetAmount,
    st_accounts,
    st_assetamounts,
)


class TestAssetAmount(unittest.TestCase):
    @given(assetamount=st_assetamounts())
    def test_str(self, assetamount):
        # Check sensible information is displayed
        assert f"{assetamount.free + assetamount.locked} {assetamount.asset}" in str(
            assetamount
        )
        assert f"free: {assetamount.free}" in str(assetamount)
        assert f"locked: {assetamount.locked}" in str(assetamount)

    @given(assetamount=st_assetamounts())
    def test_dir(self, assetamount: AssetAmount):
        # check all information is exposed
        assert {a for a in dir(assetamount)}.issuperset({"asset", "free", "locked"})

        # check no extra information is exposed
        assert {a for a in dir(assetamount) if not a.startswith("__")}.issubset(
            {"asset", "free", "locked"}
        )


class TestAccount(unittest.TestCase):
    @given(account=st_accounts())
    def test_str(self, account: Account):
        # Check sensible information is displayed
        assert f"accountType: {account.accountType}" in str(account)
        assert f"canTrade: {account.canTrade}" in str(account)
        assert f"canWithdraw: {account.canWithdraw}" in str(account)
        assert f"canDeposit: {account.canDeposit}" in str(account)

        for ab in account.balances:
            if not (ab.free + ab.locked).is_zero():
                assert f"- {ab}" in str(account)

        assert f"updateTime: {account.updateTime}" in str(account)
        assert f"permissions: {account.permissions}" in str(account)
        assert f"makerCommission: {account.makerCommission}" in str(account)
        assert f"takerCommission: {account.takerCommission}" in str(account)

        if account.buyerCommission > 0:
            assert f"buyerCommission: {account.buyerCommission}" in str(account)

        if account.sellerCommission > 0:
            assert f"sellerCommission: {account.sellerCommission}" in str(account)

    @given(account=st_accounts())
    def test_dir(self, account: Account):

        # check all information is exposed
        assert {a for a in dir(account)}.issuperset(
            {
                "accountType",
                "canTrade",
                "canWithdraw",
                "canDeposit",
                "balances",
                "updateTime",
                "permissions",
                "makerCommission",
                "takerCommission",
                "buyerCommission",
                "sellerCommission",
            }
        )

        # check no extra information is exposed
        assert {a for a in dir(account) if not a.startswith("__")}.issubset(
            {
                "accountType",
                "canTrade",
                "canWithdraw",
                "canDeposit",
                "balances",
                "updateTime",
                "permissions",
                "makerCommission",
                "takerCommission",
                "buyerCommission",
                "sellerCommission",
            }
        )


if __name__ == "__main__":
    unittest.main()
