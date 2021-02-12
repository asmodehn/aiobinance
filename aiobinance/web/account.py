import os
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Optional

import bokeh.application.handlers
import tornado.ioloop
import tornado.web
from bokeh.layouts import row
from bokeh.server.server import Server
from bokeh.themes import Theme

from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.model.account_info import AssetAmount
from aiobinance.api.rawapi import Binance
from aiobinance.config import load_api_keyfile


class AccountHandler(tornado.web.RequestHandler):
    """ tornado Request handler, created on every request. """

    account: Optional[Account]  # late initialize on request

    def initialize(self, account: Account):
        self.account = account

    async def get(self):
        # retrieve data if needed
        await self.account()
        # Ref : https://www.tornadoweb.org/en/stable/guide/templates.html
        await self.render("account.html", title="Account", account=account)


if __name__ == "__main__":
    # Running this as a basic tornado app, to ensure base functionality is working.

    credentials = load_api_keyfile()
    account = Account(api=Binance(credentials=credentials), test=True)

    app = tornado.web.Application(
        [
            (r"/", AccountHandler, {"account": account}),
        ]
    )
    app.listen(8888)
    print("Tornado is listening on http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
