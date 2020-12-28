import functools
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import bokeh
import tornado.web
from bokeh.application.handlers import FunctionHandler
from bokeh.document import Document
from bokeh.layouts import row
from bokeh.server.contexts import BokehServerContext, BokehSessionContext
from bokeh.server.server import Server
from bokeh.themes import Theme

from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.web.docs.price import PriceDocument
from aiobinance.web.plots.price_plot import PricePlot


class MarketHandler(bokeh.application.handlers.Handler):

    market: Market
    plots: List[PriceDocument]

    def __init__(self, market: Market, *args, **kwargs):
        self.market = market
        self.plots = []  # TODO : can we keep only one and share it between client ?
        super(MarketHandler, self).__init__(*args, **kwargs)

    def modify_document(self, doc: Document):
        # new web request -> new doc

        # p= ohlc_1m.plot(doc)  # pass the document to update

        # price = PricePlot(doc, self.market.price)  # trades=self.market.trades)
        # fig = bokeh.layouts.grid([price._fig])
        #
        # doc.add_root(row(fig, sizing_mode="scale_width"))
        # doc.theme = Theme(
        #     filename=os.path.join(os.path.dirname(__file__), "theme.yaml")
        # )

        doc.theme = Theme(
            filename=os.path.join(os.path.dirname(__file__), "theme.yaml")
        )

        price = PriceDocument(document=doc, ohlcv=self.market.price.frame)
        self.plots.append(price)

    async def docs_update(self):
        # TODO : this should be done somewhere else... (and the same as on_session_created !)
        if len(self.plots) > 0:  # only retrieve price ohlc if necessary
            before = datetime.now(tz=timezone.utc) - timedelta(hours=1)
            now = datetime.now(tz=timezone.utc)
            await self.market.price(start_time=before, stop_time=now)

        for p in self.plots:
            # TODO: stop updating some plots after some "inactivity" time... ??
            p.document.add_next_tick_callback(
                functools.partial(p, ohlcv=self.market.price.frame)
            )  # trigger update on next tick !

    def on_server_loaded(self, server_context: BokehServerContext):
        # driving data retrieval (TMP) and plot stream update
        # TODO : let this drive ONLY the plot update (not the data retrieval)
        server_context.add_periodic_callback(
            self.docs_update, period_milliseconds=30000
        )

        # TODO : callback scheduling can be done in on_session_created to avoid scheduling on unused markets

    async def on_session_created(self, session_context: BokehSessionContext):
        # retrieving new data at the beginning of the session
        before = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        now = datetime.now(tz=timezone.utc)
        await self.market.price(
            start_time=before, stop_time=now
        )  # to have data to show on request.
        await self.market.trades(
            start_time=before, stop_time=now
        )  # to have data to show on request.


if __name__ == "__main__":
    import asyncio

    from bokeh.util.browser import view

    from aiobinance.config import load_api_keyfile

    creds = load_api_keyfile()  # we need to authenticate to access our trades

    exchange = Exchange(api=Binance(credentials=creds), test=True)

    async def main():  # need async starting point for bokeh server ot hookup onto the existing eventloop

        # retrieving markets to determine application structure
        await exchange()

        # setting up server, only with markets application
        server = Server(
            {
                f"/{s}": bokeh.application.Application(MarketHandler(m))
                for s, m in exchange.markets.items()
            }
        )
        server.start()
        print(
            "Opening Tornado app with embedded Bokeh application on http://localhost:5006/"
        )

        server.io_loop.add_callback(view, "http://localhost:5006/")

        await asyncio.sleep(3600)

    asyncio.run(main())
