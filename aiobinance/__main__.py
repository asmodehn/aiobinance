# A running "server" providing:
# - A local repl to interact with the running server (tmuxable, screenable, dockerable)
# - A websocket terminal backend for remote repl control, provided via terminado
# - A (remote) graphical interface provided via bokeh, served by async tornado 5
#
# Usecase workflow :
# An app (typically a trading bot, lets call it 'tradebot') depends on aiobinance.
# 1. 'tradebot' is launched (optionally remotely), and runs as a process which exposes a repl (local only, potentially inside a docker container)
# 2. a known user connects (ssh) to the machine, and can dynamically order 'tradebot' via the repl, to expose it via websocket.
# 3. Via the repl, a user can also dynamically order 'tradebot' to expose a webpage presenting various graphics regarding tradebot performance...
#
#
#  Run 'tradebot' -> REPL longrunning  ---?--->  Bokeh Webpage.
#        |               /   /                        /
#  SSH remote access ---/ --/-- via text webbrowser -/
#                          /                        /
#  WebBrowser ------------/------------------------/
#
# characteristics:
# - when local connect -> enable remote for current user (some way to make that simple & intuitive yet secure ??)
# - when web connects -> refuse, unless user is "known"...
# - when local disconnect -> keep running local, drop remote, connections
# - when web disconnect -> drop remote connections
#

# => exchange account authentication should be provided on startup, and stay in memory, encrypted...
# => this __main__ module should start the repl by default (current unix user, exchange account already accessible)
# => repl should provide access to functions to enable webconnections (authentication details)
# => __main__ should provide long arguments to allow webconnections (authentication details)
# => webconnection should not be possible without authentication (given exchange account details is stored in running process)

from datetime import date, datetime, time, timedelta, timezone

import click

import aiobinance.binance as binance
import aiobinance.hummingbot as hummingbot
import aiobinance.repl as repl
from aiobinance._cli_params import Date
from aiobinance.config import Credentials


@click.group()
def cli():
    pass


@cli.command(name="hummingbot")
@click.argument("filename", type=click.Path(exists=True), required=True)
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def hummingbot_instance(ctx, filename, html=False):
    """provide a report of hummingbot trades"""

    trades = hummingbot.trades_from_csv(click.format_filename(filename))

    symbol = trades[0].symbol  # assuming only one symbol !

    ohlcv = binance.price_from_binance(
        start_time=trades[0].time,
        end_time=trades[-1].time,
        symbol=symbol,
    )

    if html:
        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        report = aiobinance.web.trades_layout(ohlcv=ohlcv, trades=trades)
        output_file(f"{filename}_report.html")
        show(report)

    print(trades)


@cli.command()
@click.option("--verbose", default=False, is_flag=True)
@click.pass_context
def auth(ctx, verbose):
    """ simple command to verify auth credentials and optionally store them. """
    from aiobinance.config import (
        BINANCE_API_KEYFILE,
        load_api_keyfile,
        save_api_keyfile,
    )

    # tentative loading of the API key
    keystruct = load_api_keyfile()

    if keystruct is None:
        # no keyfile found
        print(f"{BINANCE_API_KEYFILE} Not Found !")
        # check for interactive terminal
        if hasattr(sys, "ps1"):
            apikey = input("APIkey: ")
            secret = input("secret: ")
            creds = Credentials(key=apikey, secret=secret)
            store = input(f"Store it in {BINANCE_API_KEYFILE} [Y/n] ? ")
            if not store:
                store = "Y"
            if store in ["Y", "y"]:
                keystruct = save_api_keyfile(credentials=creds)
            else:
                keystruct = creds
        else:
            print("Run the auth command to create it.")
            return 1  # exit status code

    # modifying parent context if present (to return)
    if verbose:
        print(
            f"apikey and secret stored in {BINANCE_API_KEYFILE}.\nRemove it and re-run this command to replace it."
        )
    if ctx.parent:
        ctx.parent.params["apikey"] = keystruct.key
        ctx.parent.params["secret"] = keystruct.secret

        if keystruct:
            print(f"apikey: {keystruct}")
        else:  # should come from context
            print(f"apikey: {ctx.apikey}")

    return 0  # exit status code


@cli.command()
@click.option("--apikey", default=None)
@click.option("--secret", default=None)
@click.pass_context
def balance(ctx, apikey, secret):
    """ retrieve balance for the authentified user"""

    if apikey is None or secret is None:
        ctx.invoke(auth, verbose=False)  # this should fill up arguments
        creds = Credentials(
            key=ctx.params.get("apikey"), secret=ctx.params.get("secret")
        )
    else:
        creds = Credentials(key=apikey, secret=secret)

    # we always have the key here (otherwise it has been stored already)
    print(binance.balance_from_binance(credentials=creds))


@cli.command()
@click.argument("market_pair", required=True, default=None)
@click.option(
    "--from", "from_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", "to_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--apikey", default=None)
@click.option("--secret", default=None)
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def trades(
    ctx, market_pair: str, from_date: date, to_date: date, apikey, secret, html=True
):
    """display trades"""

    if apikey is None or secret is None:
        ctx.invoke(auth, verbose=False)  # this should fill up arguments
        creds = Credentials(
            key=ctx.params.get("apikey"), secret=ctx.params.get("secret")
        )
    else:
        creds = Credentials(key=apikey, secret=secret)

    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time())
    from_datetime = datetime.combine(from_date, time())

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


def positions():
    """display existing positions of the authenticated user"""
    raise NotImplementedError


@cli.command()
@click.argument("market_pair", required=True)
@click.option(
    "--from", "from_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", "to_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def price(ctx, market_pair, from_date: date, to_date: date, html=True):
    """display prices"""

    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time())
    from_datetime = datetime.combine(from_date, time())

    ohlcv = binance.price_from_binance(
        symbol=market_pair,
        start_time=from_datetime,
        end_time=to_datetime,
    )

    if html:

        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        report = aiobinance.web.price_plot(ohlcv=ohlcv)
        output_file(f"{market_pair}_{from_date}_{to_date}_price.html")
        show(report)
    else:
        # TODO : terminal plot ??

        # TODO : daily ticker instead of OHLCV ???
        # tkr = binance.ticker24_from_binance(
        #     symbol=market_pair
        # )
        # print(tkr)
        pass
    print(ohlcv)


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) > 1:
        # we use click to run a simple command -> result
        cli()
    else:
        # or we go full interactive mode (no args)
        asyncio.run(repl.embedded_ptpython())
