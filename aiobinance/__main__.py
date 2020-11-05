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

from datetime import date, datetime

import click

import aiobinance.binance as binance
import aiobinance.hummingbot as hummingbot
import aiobinance.repl as repl
from aiobinance._cli_params import Date

# TODO
# binance.trades_from_binance()


@click.group()
def cli():
    pass


@cli.command(name="hummingbot")
@click.argument("filename", type=click.Path(exists=True), required=False)
@click.pass_context
def hummingbot_instance(ctx, filename):
    "provide a report of hummingbot trades"

    trades = hummingbot.trades_from_csv(click.format_filename(filename))
    print(trades.head())

    base = trades.Base.unique()
    quote = trades.Quote.unique()

    symbol = base[0] + quote[0]  # assuming only one value

    print(symbol)

    ohlcv = binance.price_from_binance(
        start_time=trades.datetime.iloc[0].timestamp(),
        end_time=trades.datetime.iloc[-1].timestamp(),
        symbol=symbol,
    )

    import aiobinance.web

    report = aiobinance.web.trades_layout(ohlcv=ohlcv, trades=trades)

    from bokeh.io import output_file

    output_file(f"{filename}_report.html")

    from bokeh.plotting import show

    show(report)


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
        print(f"{BINANCE_API_KEYFILE} not found !")
        # TODO : check for interactive terminal...
        apikey = input("APIkey: ")
        secret = input("secret: ")
        store = input(f"Store it in {BINANCE_API_KEYFILE} [Y/n] ? ")
        if not store:
            store = "Y"
        if store in ["Y", "y"]:
            keystruct = save_api_keyfile(apikey=apikey, secret=secret)
        else:
            keystruct = {"key": apikey, "secret": secret}

    # modifying parent context if present (to return)
    if verbose:
        print(
            f"apikey and secret stored in {BINANCE_API_KEYFILE}.\nRemove it and re-run this command to replace it."
        )
    if ctx.parent:
        ctx.parent.params["apikey"] = keystruct.get("key")
        ctx.parent.params["secret"] = keystruct.get("secret")

        if keystruct:
            print(f"apikey: {keystruct.get('key')}")
        else:  # should come from context
            print(f"apikey: {ctx.apikey}")

    return 0  # exit status code


@cli.command()
@click.option("--apikey", default=None)
@click.option("--secret", default=None)
@click.pass_context
def balance(ctx, apikey, secret):
    """ retrieve balance for an authentified user"""

    if apikey is None or secret is None:
        ctx.invoke(auth, verbose=False)  # this should fill up arguments
        apikey = ctx.params.get("apikey")
        secret = ctx.params.get("secret")

    # we always have the key here (otherwise it has been stored already)
    binance.balance_from_binance(key=apikey, secret=secret)


def positions():
    """display existing positions of the authenticated user"""
    raise NotImplementedError


### COMMAND that rely on some timeframe ###


@click.argument("market_pair", required=True)
@click.option(
    "--from", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def price(
    ctx, market_pair, from_date: datetime, to_date: datetime, interval: str, html=True
):

    ohlcv = binance.price_from_binance(
        symbol=market_pair,
        start_time=from_date.timestamp(),
        end_time=to_date.timestamp(),
        interval=interval,
    )

    if html:
        import aiobinance.web

        report = aiobinance.web.price_plot(ohlcv=ohlcv)

        from bokeh.io import output_file

        output_file(f"{market_pair}_{from_date}_{to_date}_price.html")

        from bokeh.plotting import show

        show(report)
    else:
        # TODO : some kind of terminal plot...
        raise NotImplementedError


@click.argument("market_pair", required=False)
@click.option(
    "--from", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def trades(
    ctx, market_pair, from_date: datetime, to_date: datetime, interval: str, html=True
):
    "display trades"
    raise NotImplementedError


### GROUP by human concerns over long time: daily, weekly, monthly ###


@cli.group()
@click.argument("market_pair", required=True)
@click.option(
    "--from", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def daily(ctx, market_pair, from_date, to_date, html):
    """display OHLC"""

    # compute interval to fit one request data into one day
    # ohlc(market_pair, from_date, to_date, interval, html=True)
    raise NotImplementedError


@cli.group()
@click.argument("market_pair", required=True)
@click.option(
    "--from", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to last week
@click.option(
    "--to", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def weekly(ctx, market_pair, from_date, to_date, html):
    """display OHLC"""
    # compute interval to fit one request data into one week
    # ohlc(market_pair, from_date, to_date, interval, html=True)
    raise NotImplementedError


@cli.group()
@click.argument("market_pair", required=True)
@click.option(
    "--from", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to lst month
@click.option(
    "--to", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def monthly(ctx, market_pair, from_date, to_date, html):
    """display OHLC"""

    # compute interval to fit one request data into one month
    # ohlc(market_pair, from_date, to_date, interval, html=True)
    raise NotImplementedError


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # we use click to run a simple command -> result
        cli()
    else:
        # or we go full interactive mode (no args)
        repl.embedded_repl()
