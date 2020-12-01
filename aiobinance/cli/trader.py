import asyncio
import sys
from decimal import Decimal

import click
from pydantic import typing

from aiobinance.api.account import Account, retrieve_account
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.config import Credentials
from aiobinance.trader import Trader

# Ref : https://click.palletsprojects.com/en/7.x/complex/#interleaved-commands
pass_account = click.make_pass_decorator(Account)


@click.group()
@click.option("--apikey", default=None)
@click.option("--secret", default=None)
@click.option("--confirm", default=False, is_flag=True)
@click.pass_context
def trader(ctx, apikey=None, secret=None, confirm=False):
    """ Managing user account """
    from aiobinance.config import BINANCE_API_KEYFILE, load_api_keyfile

    if apikey is not None and secret is not None:
        creds = Credentials(key=apikey, secret=secret)
    else:
        # tentative loading of the API key
        creds = load_api_keyfile()

    if not creds:
        print(
            "User not authenticated. Trade impossible. Please check the 'auth' command to fix this."
        )
        sys.exit(-1)

    api = Binance(credentials=creds)  # we need private requests here !

    account = retrieve_account(api=api, test=not confirm)
    print(account)  # TMP
    ctx.obj = account


@trader.command()
@click.argument(
    "amount", type=str
)  # Note we use str here to not loose precision until decimal conversion
@click.argument("currency", type=str)
@click.option("--using", type=(str, str), required=True)
@pass_account
def buy(
    account: Account,
    amount: str,
    currency: str,
    using: typing.Tuple[str, str],
    confirm: bool = False,
):
    """buy for this account"""

    amount = Decimal(amount)

    if using is None:  # TODO: interactive confirmation
        raise NotImplementedError("automated best market detection not implemented yet")

    using_amount = Decimal(using[0])

    # retrieve market
    smbl = currency + using[1]

    trdr = Trader(account=account, market=account.exchange.market[smbl])

    trade = trdr.buy(amount=amount, total_expected=using_amount)

    print(trade)

    # TODO : short trade analysis


@trader.command()
@click.argument(
    "amount", type=str
)  # Note we use str here to not loose precision until decimal conversion
@click.argument("currency", type=str)
@click.option("--receive", type=(str, str), required=True)
@pass_account
def sell(
    account: Account,
    amount: str,
    currency: str,
    receive: typing.Tuple[str, str],
):
    """buy for this account"""

    amount = Decimal(amount)

    if receive is None:  # TODO: interactive confirmation
        raise NotImplementedError("automated best market detection not implemented yet")

    using_amount = Decimal(receive[0])

    # retrieve market
    smbl = currency + receive[1]

    trdr = Trader(account=account, market=account.exchange.market[smbl])

    trade = trdr.sell(amount=amount, total_expected=using_amount)
    # TODO : this is currently an order (as registered.) Trader needs to wait for trade...
    print(trade)

    # TODO : short trade analysis


if __name__ == "__main__":
    # testing only this cli command
    trader()
