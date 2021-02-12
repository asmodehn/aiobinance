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
from typing import Optional

import click
from click import Choice

import aiobinance.binance as binance
import aiobinance.hummingbot as hummingbot
import aiobinance.repl as repl
from aiobinance import websrv
from aiobinance.cli.account import account
from aiobinance.cli.extras import extras
from aiobinance.cli.market import market
from aiobinance.config import Credentials


@click.group()
def base_cli():
    pass


@base_cli.command()  # Maybe this is more generic ?
@click.pass_context
def webview(
    ctx,
):
    """runs only the webserver, displaying all informations retrievable from the exchange."""

    # Retrieving basic informations on the exchange
    exg = binance.exchange_from_binance()

    # starting websrv in foreground, passing symbols to provide web structure
    # This allows simple debugging of only the webserver
    asyncio.run(websrv.main(exg.symbols))


async def interactive():
    """ Running aiobinance in interactive mode """

    # Retrieving basic informations on the exchange
    # exg = binance.exchange_from_binance()

    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.layout import Layout
    from ptterm import Terminal

    def done():
        application.exit()

    term_container = Terminal(done_callback=done)
    log_buffer = Buffer(read_only=True)

    application = Application(
        layout=Layout(
            container=VSplit(
                [
                    term_container,
                    Window(width=1, char="|"),
                    Window(content=BufferControl(buffer=log_buffer)),
                ]
            ),
            focused_element=term_container,
        ),
        full_screen=True,
    )

    # generating output from the websrv...
    asyncio.create_task(websrv.display_date())

    await application.run_async()

    # repl keeps running until the end
    # await repl.embedded_ptpython()


cli = click.CommandCollection(sources=[base_cli, account, market, extras])


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) > 1:
        # we use click to run a simple command -> result
        cli()
    else:
        # or we go full interactive mode (no args)
        asyncio.run(interactive())


# CLI design:
#   aiobinance [--key KEY, --secret SECRET] [--no/only-repl] [--no/only-web] [--no/only-bot]
#       => interactive web & repl (& bot to come)
#   aiobinance [--key KEY, --secret SECRET] auth
#       => verify auth & exit
#   aiobinance [--key KEY, --secret SECRET] balance
#       => prints balance & exit

#   aiobinance [--key KEY, --secret SECRET] price
#       => price via tickers, for all assets
#   aiobinance [--key KEY, --secret SECRET] price --symbol COTIBNB
#       => OHLC for this asset

#   aiobinance [--key KEY, --secret SECRET] trades
#       => trades for all assets
#   aiobinance [--key KEY, --secret SECRET] trades --symbol COTIBNB
#       => trades for this asset

#   aiobinance [--key KEY, --secret SECRET] trade buy/sell  19123.12313 COTI 58.56 BNB
#       => trades for this asset

# NO UNSUPERVISED ORDER FROM CLI ! needs some minimal supervision by the bot...
# TODO....
