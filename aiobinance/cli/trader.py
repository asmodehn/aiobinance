import asyncio
import sys
from decimal import Decimal

import click
from pydantic import typing

from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.cli.cli_group import cli, pass_creds
from aiobinance.config import Credentials
from aiobinance.trader import Trader

# Ref : https://click.palletsprojects.com/en/7.x/complex/#interleaved-commands
pass_account = click.make_pass_decorator(Account)


@cli.command()
@click.argument(
    "amount", type=str
)  # Note we use str here to not loose precision until decimal conversion
@click.argument("currency", type=str)
@click.option("--using", type=(str, str), required=True)
@click.option("--confirm", default=False, is_flag=True)
@pass_creds
def buy(
    creds: Credentials,
    amount: str,
    currency: str,
    using: typing.Tuple[str, str],
    confirm: bool = False,
):
    """buy for this account"""

    api = Binance(credentials=creds)  # we need private requests here !

    exchange = Exchange(api=api, test=not confirm)

    amount = Decimal(amount)

    if using is None:  # TODO: interactive confirmation
        raise NotImplementedError("automated best market detection not implemented yet")

    using_amount = Decimal(using[0])

    # retrieve market
    asyncio.run(exchange())
    smbl = currency + using[1]

    trdr = Trader(account=exchange.account, market=exchange.markets[smbl])

    trade = trdr.buy(amount=amount, total_expected=using_amount)

    print(trade)

    # TODO : short trade analysis


@cli.command()
@click.argument(
    "amount", type=str
)  # Note we use str here to not loose precision until decimal conversion
@click.argument("currency", type=str)
@click.option("--receive", type=(str, str), required=True)
@click.option("--confirm", default=False, is_flag=True)
@pass_creds
def sell(
    creds: Credentials,
    amount: str,
    currency: str,
    receive: typing.Tuple[str, str],
    confirm: bool = False,
):
    """buy for this account"""

    api = Binance(credentials=creds)  # we need private requests here !

    exchange = Exchange(api=api, test=not confirm)

    amount = Decimal(amount)

    if receive is None:  # TODO: interactive confirmation
        raise NotImplementedError("automated best market detection not implemented yet")

    using_amount = Decimal(receive[0])

    # retrieve market
    asyncio.run(exchange())
    smbl = currency + receive[1]

    trdr = Trader(account=exchange.account, market=exchange.markets[smbl])

    trade = trdr.sell(amount=amount, total_expected=using_amount)
    # TODO : this is currently an order (as registered.) Trader needs to wait for trade...
    print(trade)

    # TODO : short trade analysis


if __name__ == "__main__":
    # testing only this cli command
    cli()
