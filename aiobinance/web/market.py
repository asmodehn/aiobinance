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
from aiobinance.web.layouts.triplescreen import TripleScreen


class MarketHandler(bokeh.application.handlers.Handler):

    market: Market

    def __init__(self, market: Market, *args, **kwargs):
        self.market = market
        self.docs = []  # needed ??
        super(MarketHandler, self).__init__(*args, **kwargs)

    def modify_document(self, doc: Document):
        doc.theme = Theme(
            filename=os.path.join(os.path.dirname(__file__), "theme.yaml")
        )

        # we pass document to the layout to let it drive its update cycle...
        price = TripleScreen(
            document=doc, ohlcv=self.market.price, trades=self.market.trades
        )
        doc.add_root(model=price.model)

    async def on_session_created(self, session_context: BokehSessionContext):
        # retrieving data

        print(f"Starting data update loop for {self.market.info.symbol}...", end="")
        # retrieving data in background (once, then will loop forever)
        await self.market.price.run()
        print(" OK.")

        # TODO: retrieve user trades from Account (Not Market !)
        # # to have data to show on request.
        # await self.market.trades(
        #     start_time=before, stop_time=now # TODO : only the current symbol !
        # )  # to have data to show on request.


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
