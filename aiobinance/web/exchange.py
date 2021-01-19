from typing import Any, Optional

import tornado.ioloop
import tornado.web
from tornado import httputil

from aiobinance.api.exchange import Exchange
from aiobinance.api.rawapi import Binance


class ExchangeHandler(tornado.web.RequestHandler):
    """ tornado Request handler, created on every request. """

    exchange: Optional[Exchange]  # late initialize on request

    def initialize(self, exchange: Exchange):
        self.exchange = exchange

    async def get(self):
        await self.exchange()  # refresh data
        # Ref : https://www.tornadoweb.org/en/stable/guide/templates.html
        await self.render("exchange.html", title="Exchange", exchange=self.exchange)


if __name__ == "__main__":
    # Running this as a basic tornado app, to ensure base functionality is working.

    app = tornado.web.Application(
        [
            (r"/", ExchangeHandler, {"exchange": Exchange(api=Binance(), test=True)}),
        ]
    )
    app.listen(8888)
    print("Tornado is listening on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
