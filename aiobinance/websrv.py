import asyncio
import functools
import os
from datetime import datetime, timedelta, timezone
from typing import List

import bokeh
from bokeh.application import Application
from bokeh.server.server import Server
from tornado.web import StaticFileHandler

from aiobinance.api.exchange import Exchange
from aiobinance.api.rawapi import Binance
from aiobinance.web.exchange import ExchangeHandler
from aiobinance.web.market import MarketHandler


# a simple background task generating output
async def display_date():
    while True:
        print(datetime.now())
        await asyncio.sleep(1)


async def websrv(exchange: Exchange):

    """ async function to start server, so it uses the current event loop instead of creating his own. """

    # retrieving markets to determine application structure
    await exchange()

    print(
        "Starting Tornado Server with embedded Bokeh application on http://localhost:5006/"
    )
    # We leverage Bokeh Server (so we dont mess with HTTP server things...)
    # Server will take current runnin asyncio loop as his own.
    server = Server(
        applications={
            **{
                f"/markets/{s}": Application(MarketHandler(m))
                for s, m in exchange.markets.items()
            }
        },
        # standard tornado things
        extra_patterns=[
            # because markets needs their own static directory ??? TODO : investigate...
            # Related issue : https://github.com/bokeh/bokeh/issues/9671
            (
                "/markets/static/(.*)",
                StaticFileHandler,
                {
                    "path": os.path.normpath(
                        os.path.dirname(bokeh.server.__file__) + "/static/"
                    )
                },
            ),
            ("/", ExchangeHandler, {"exchange": exchange}),
            # TODO: status of the server (uptime, binance connection, etc.)
        ],
        # ioloop must remain to none, num_procs must be default (1)
    )
    server.start()  # this schedule the server to ru in background...

    # We can schedule other background tasks here if needed...

    # Enable this is we want browser popup...
    # print(        "Opening Browser to connect to Tornado backend on http://localhost:5006/")
    # server.io_loop.add_callback(server.show, "/")

    # THIS is already the loop that is currently running !!!
    assert (
        server.io_loop.asyncio_loop == asyncio.get_running_loop()
    ), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
    # server.io_loop.start()  # DONT NEED !

    await asyncio.sleep(3600)  # running for one hour.
    # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)


if __name__ == "__main__":
    from aiobinance.config import load_api_keyfile

    creds = load_api_keyfile()

    exchange = Exchange(api=Binance(credentials=creds), test=True)

    asyncio.run(websrv(exchange))
