import os
from datetime import datetime, timedelta, timezone

import bokeh
import tornado.web
from bokeh.application.handlers import FunctionHandler
from bokeh.layouts import row
from bokeh.server.server import Server
from bokeh.themes import Theme

from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.rawapi import Binance
from aiobinance.web.plots.price_plot import price_plot


class MarketHandler(bokeh.application.handlers.Handler):
    def __init__(self, market: Market, *args, **kwargs):
        self.market = market
        super(MarketHandler, self).__init__(*args, **kwargs)

    def modify_document(self, doc):

        # p= ohlc_1m.plot(doc)  # pass the document to update

        price = price_plot(self.market.price, trades=self.market.trades)
        fig = bokeh.layouts.grid([price])
        # TODO : dynamic update ???
        doc.add_root(row(fig, sizing_mode="scale_width"))
        doc.theme = Theme(
            filename=os.path.join(os.path.dirname(__file__), "theme.yaml")
        )

    def on_server_loaded(self, server_context):
        # retrieving market info (mostly constant at human timeframe)
        # server_context.io_loop.create_task(self.market())
        # not needed it seems (exchange provided the info already)
        pass

    async def on_session_created(self, session_context):
        # retrieving new data at the beginning of the session
        yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
        now = datetime.now(tz=timezone.utc)
        await self.market.price(
            start_time=yesterday, stop_time=now
        )  # to have data to show on request.
        await self.market.trades(
            start_time=yesterday, stop_time=now
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
