from aiobinance.api.exchange import Exchange, retrieve_exchange
from aiobinance.api.rawapi import Binance
from aiobinance.model.account import Account as AccountModel
from aiobinance.model.order import Order


class Account:

    """ A class to simplify interacting with binance account through the REST API."""

    api: Binance
    _model: AccountModel

    # set of properties acting as translation layer for the outside

    @property
    def accountType(self):
        return self._model.accountType

    @property
    def balances(self):
        return self._model.balances

    @property
    def buyerCommission(self):
        return self._model.buyerCommission

    @property
    def canDeposit(self):
        return self._model.canDeposit

    @property
    def canTrade(self):
        return self._model.canTrade

    @property
    def canWithdraw(self):
        return self._model.canWithdraw

    @property
    def makerCommission(self):
        return self._model.makerCommission

    @property
    def permissions(self):
        return self._model.permissions

    @property
    def sellerCommission(self):
        return self._model.sellerCommission

    @property
    def takerCommission(self):
        return self._model.takerCommission

    @property
    def updateTime(self):
        return self._model.updateTime

    # interactive behavior

    def __init__(self, api: Binance, model: AccountModel):
        self.api = api
        self._model = model

        self._exchange = None

    @property
    def exchange(self) -> Exchange:
        if self._exchange is None:
            self._exchange = retrieve_exchange(api=self.api)
        return self._exchange


def retrieve_account(*, api: Binance) -> Account:

    if api.creds is not None:

        res = api.call_api(command="account")

        if res.is_ok():
            res = res.value
        else:
            # TODO : handle API error properly
            raise RuntimeError(res.value)

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        account = AccountModel(
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

        instance = Account(api=api, model=account)

    return instance
