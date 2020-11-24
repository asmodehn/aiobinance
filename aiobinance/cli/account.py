import sys
from datetime import date, datetime, time, timedelta, timezone

import click

import aiobinance.binance as binance
from aiobinance.api.account import retrieve_account
from aiobinance.api.exchange import Exchange
from aiobinance.api.rawapi import Binance
from aiobinance.cli.params.date import Date
from aiobinance.config import Credentials

local_tz = datetime.now(tz=timezone.utc).astimezone().tzinfo

# Ref : https://click.palletsprojects.com/en/7.x/complex/#interleaved-commands
pass_creds = click.make_pass_decorator(Credentials)  # TODO use ensure for defaults ?
pass_exchange = click.make_pass_decorator(Exchange)


@click.group()
@click.option("--apikey", default=None)
@click.option("--secret", default=None)
@click.pass_context
def account(ctx, apikey=None, secret=None):
    """ Managing user account """
    from aiobinance.config import BINANCE_API_KEYFILE, load_api_keyfile

    if apikey is not None and secret is not None:
        creds = Credentials(key=apikey, secret=secret)
    else:
        # tentative loading of the API key
        creds = load_api_keyfile()

        if creds.key is None:
            # no keyfile found
            print(f"{BINANCE_API_KEYFILE} Not Found !")
            # check for interactive terminal
            if hasattr(sys, "ps1"):
                print(
                    "- Interactive Terminal detected. Now Entering Binance APIkey and secret - "
                )
                apikey = input("APIkey: ")
                secret = input("secret: ")
                creds = Credentials(key=apikey, secret=secret)
            else:
                print("Interactive terminal mandatory to enter credentials.")
                sys.exit(1)  # exit status code

    ctx.obj = creds


@account.command()
@click.option("--store", default=False, is_flag=True)
@pass_creds
def auth(creds, store):
    """ simple command to verify auth credentials and optionally store them. """

    from aiobinance.config import BINANCE_API_KEYFILE, save_api_keyfile

    if store:
        stored = save_api_keyfile(credentials=creds)
        assert stored == creds
        print(
            f"apikey and secret stored in {BINANCE_API_KEYFILE}.\nRemove it and re-run this command to replace it."
        )

    print(f"apikey: {creds}")

    sys.exit(0)  # exit status code


@account.command()
@pass_creds
def balance(creds):
    """ retrieve balance for the account"""

    api = Binance(credentials=creds)  # we need private requests here !

    account = retrieve_account(api=api)

    print(
        account._model
    )  # need to print the account data structure, until we have a better idea of what to do here...


@account.command()  # TODO : this should return ALL trades. trades for a specific market should be in a market
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
    creds,
    market_pair: str,
    from_date: date,
    to_date: date,
    utc=False,
    html=True,
):
    """display trades for this account"""

    time_zero = time(tzinfo=timezone.utc) if utc else time(tzinfo=local_tz)
    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time_zero)
    from_datetime = datetime.combine(from_date, time_zero)

    # api = Binance(credentials=creds)  # we need private requests here !

    # TODO : call trades

    trades = binance.trades_from_binance(
        symbol=market_pair,
        start_time=from_datetime,
        end_time=to_datetime,
        credentials=creds,
    )

    if html:
        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        ohlcv = binance.price_from_binance(
            symbol=market_pair,
            start_time=from_datetime,
            end_time=to_datetime,
        )

        report = aiobinance.web.price_plot(ohlcv=ohlcv, trades=trades)
        output_file(f"{market_pair}_{from_date}_{to_date}_price.html")
        show(report)

    # TODO : terminal plot ??

    print(trades)


if __name__ == "__main__":
    # testing only this cli command
    account()
