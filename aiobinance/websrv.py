import asyncio
import functools
import os
from datetime import datetime, timedelta, timezone
from typing import List

from bokeh.layouts import row
from bokeh.server.server import Server as BokehServer
from bokeh.themes import Theme

from aiobinance import price_from_binance, web
from aiobinance.model.ohlcv import OHLCV


# Fake background task I got from here:
# https://docs.python.org/3/library/asyncio-task.html#sleeping
async def display_date():
    while True:
        print(datetime.now())
        await asyncio.sleep(1)


def start_tornado(symbols: List[str]):
    # Server will take current runnin asyncio loop as his own.
    server = BokehServer(
        {f"/{s}": functools.partial(symbol_page, symbol=s) for s in symbols}
    )  # iolopp must remain to none, num_procs must be default (1)
    server.start()
    # app = make_app()
    # app.listen(8888)
    return server


def symbol_page(doc, symbol: str):

    yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
    now = datetime.now(tz=timezone.utc)

    # p= ohlc_1m.plot(doc)  # pass the document to update

    fig = web.symbol_layout(symbol=symbol, from_datetime=yesterday, to_datetime=now)

    doc.add_root(row(fig, sizing_mode="scale_width"))
    doc.theme = Theme(
        filename=os.path.join(os.path.dirname(__file__), "web", "theme.yaml")
    )

    # TODO : some way to close the ohlc subscription when we dont need it anymore...


async def main():

    # # Client can be global: there is only one.
    # rest = RestClient(server=Server())
    #
    # XBTUSD = (await rest.retrieve_assetpairs())['XBTUSD']
    #
    # # ohlc data can be global (one per market*timeframe only)
    # # retrieving data (and blocking control flow)
    # ohlc_1m = OHLCV(pair=XBTUSD, rest=rest)
    # # TODO : use implicit retrieval (maybe by accessing slices of OHLC from bokeh doc/fig update??)
    #

    # TODO : build a layout to explore different TF

    print("Starting Tornado Server...")
    server = start_tornado(symbols=["COTIBNB", "BNBEUR"])
    # Note : the bkapp is run for each request to the url...

    # bg task...
    asyncio.create_task(display_date())

    print("Serving Bokeh application on http://localhost:5006/")
    # server.io_loop.add_callback(server.show, "/")

    # THIS is already the loop that is currently running !!!
    assert (
        server.io_loop.asyncio_loop == asyncio.get_running_loop()
    ), f"{server.io_loop.asyncio_loop} != {asyncio.get_running_loop()}"
    # server.io_loop.start()  # DONT NEED !

    await asyncio.sleep(3600)  # running for one hour.
    # TODO : scheduling restart (crontab ? cli params ?) -> GOAL: ensure resilience (erlang-style)


if __name__ == "__main__":
    # This module taken independently starts the repl, as an interactive test.
    # It is connected to the binance but without any authentication or configuration.
    # These could be done interactively however...

    asyncio.run(main(), debug=True)
