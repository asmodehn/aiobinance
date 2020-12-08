import sys
from datetime import date, datetime, time, timedelta, timezone

import click

import aiobinance.binance as binance
from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.rawapi import Binance
from aiobinance.api.tradesview import TradesView
from aiobinance.cli.cli_group import cli, pass_creds
from aiobinance.cli.params.date import Date
from aiobinance.config import Credentials

local_tz = datetime.now(tz=timezone.utc).astimezone().tzinfo

pass_exchange = click.make_pass_decorator(Exchange)


@cli.command()
@pass_creds
def balance(creds: Credentials):
    """ retrieve balance for the account"""

    api = Binance(credentials=creds)  # we need private requests here !

    account = Account(api=api)

    import asyncio

    asyncio.run(account())

    print(
        account.info
    )  # need to print the account data structure, until we have a better idea of what to do here...


@cli.command()  # TODO : this should return ALL trades. trades for a specific market should be in a market
@click.argument("market_pair", required=True, default=None)
@click.option(
    "--from", "from_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", "to_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--utc", "utc", default=False, is_flag=True)
@click.option("--html", default=False, is_flag=True)
@pass_creds
def trades(
    creds: Credentials,
    market_pair: str,
    from_date: date,
    to_date: date,
    utc=False,
    html=True,
):
    """display trades for this account"""
    import asyncio

    time_zero = time(tzinfo=timezone.utc) if utc else time(tzinfo=local_tz)
    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time_zero)
    from_datetime = datetime.combine(from_date, time_zero)

    api = Binance(credentials=creds)  # we need private requests here !

    trades = TradesView(api=api, symbol=market_pair)

    # while we are moving to an async interface
    asyncio.run(trades(start_time=from_datetime, stop_time=to_datetime))

    if html:
        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        ohlcv = OHLCView(api=api, symbol=market_pair)

        # while we are moving to an async interface
        asyncio.run(ohlcv(start_time=from_datetime, stop_time=to_datetime))

        report = aiobinance.web.price_plot(ohlcv=ohlcv.frame, trades=trades.frame)
        output_file(f"{market_pair}_{from_date}_{to_date}_price.html")
        show(report)

    # TODO : terminal plot ??

    print(trades)


if __name__ == "__main__":
    # testing only these commands
    cli()
