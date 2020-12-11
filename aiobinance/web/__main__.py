import asyncio
import functools
from typing import List

import bokeh.application
import tornado
import tornado.web
from bokeh.server.server import Server

from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.config import load_api_keyfile
from aiobinance.web.exchange import ExchangeHandler
from aiobinance.web.market import MarketHandler


async def main(exchange: Exchange):

    """ async function to start server, so it uses the current event loop instead of creating his own. """

    # retrieving markets to determine application structure
    await exchange()

    print("Starting Tornado Server...")
    # We leverage Bokeh Server (so we dont mess with HTTP server things...)
    # Server will take current runnin asyncio loop as his own.
    server = Server(
        applications={
            **{
                f"/markets/{s}": bokeh.application.Application(MarketHandler(m))
                for s, m in exchange.markets.items()
            }
        },
        # standard tornado things
        extra_patterns=[
            ("/exchange", ExchangeHandler, {"exchange": exchange}),
            # TODO: status of the server (uptime, binance connection, etc.)
        ],
    )
    server.start()
    print(
        "Opening Tornado app with embedded Bokeh application on http://localhost:5006/"
    )

    print("Serving Bokeh application on http://localhost:5006/")
    server.io_loop.add_callback(server.show, "/")

    # THIS is already the loop that is currently running !!!
    assert (
        server.io_loop.asyncio_loop == asyncio.get_running_loop()
    ), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
    # server.io_loop.start()  # DONT NEED !

    await asyncio.sleep(3600)  # running for one hour.
    # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)


creds = load_api_keyfile()

exchange = Exchange(api=Binance(credentials=creds), test=True)

asyncio.run(main(exchange))
