import functools
from asyncio import QueueEmpty
from dataclasses import dataclass, field
from functools import cache, cached_property, partial
from typing import Dict, List, Optional

from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.model import Model
from bokeh.models import Button, Column, RadioButtonGroup, RadioGroup, Row
from bokeh.plotting import Figure

from aiobinance.api.account import Account
from aiobinance.api.exchange import Exchange
from aiobinance.api.ledgerview import LedgerView
from aiobinance.api.model.timeinterval import TimeInterval, TimeIntervalDelta, TimeStep
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.rawapi import Binance
from aiobinance.api.tradesview import TradesView
from aiobinance.web.layouts.plots.ohlcstep import OHLCStepPlots
from aiobinance.web.layouts.plots.tradespnl import TradesPnL


@dataclass
class AssetTrades:

    document: Document
    asset: str
    ledger: Optional[LedgerView] = field(default=None)

    # relevant graphical component for each market symbol
    plots: Dict[str, TradesPnL] = field(default_factory=dict)

    # for radio buttons
    base_symlist: List[str] = field(default_factory=list)
    quote_symlist: List[str] = field(default_factory=list)

    _selected: Optional[str] = field(default=None)

    def __post_init__(self):

        # self.symlist = [s for s in self.ledger.trades.keys()]  # TODO : maybe this is not needed ?
        if self.base_symlist:
            self.selected = self.base_symlist[0]

    # Lens based layout...
    # TODO : maybe some hierarchy of classes to get the same composability effect for seamless updates ??
    @functools.cached_property  # a cache, hidden behind a property accessor
    def model(self) -> Model:
        return row(self.widgets, self.tradeplot, sizing_mode="scale_width")

    # @model.setter
    # def model(self, newmodel: Model):
    #     self._model = newmodel  # this modifies the cache
    #     # TODO: maybe we need to have a "container" concept to trigger update ourselves inside it ?

    @functools.cached_property
    def widgets(self) -> Column:

        # Note : we need to scale the row like the button to avoid overlapping buttons...
        return column(
            self.base_radio_button, self.quote_radio_button, sizing_mode="scale_width"
        )

    @property
    def base_radio_button(self) -> RadioGroup:
        bsrb = RadioGroup(  # TODO :  RadioButtonGroup currently does not support vertical alignment ?
            # orientation='vertical',
            labels=[str(c) for c in self.base_symlist],
            active=self.base_symlist.index(self.selected)
            if self.selected in self.base_symlist
            else None,
        )
        bsrb.on_click(
            partial(self.on_base_radio_symbol_click, symlist=self.base_symlist)
        )
        return bsrb

    @property
    def quote_radio_button(self) -> RadioGroup:

        qsrb = RadioGroup(  # TODO :  RadioButtonGroup currently does not support vertical alignment ?
            # orientation='vertical',
            labels=[str(c) for c in self.quote_symlist],
            active=self.quote_symlist.index(self.selected)
            if self.selected in self.quote_symlist
            else None,
        )
        qsrb.on_click(
            partial(self.on_quote_radio_symbol_click, symlist=self.quote_symlist)
        )
        return qsrb

    #
    # @widgets.setter
    # def widgets(self, newrow: Row):
    #     self._widgets = newrow
    #     self.model.children[0] = self._widgets

    # @functools.cached_property
    @property  # TMP cache not working
    def tradeplot(self) -> Column:
        return column(self.tradefig, sizing_mode="scale_width")

    # @ohlcplot.setter
    # def ohlcplot(self, newrow: Row):
    #     self._plot = newrow
    #     self.model.children[1] = self._plot

    @property
    def tradefig(self) -> Figure:
        if self.selected not in self.plots:
            # create it
            if self.selected in self.ledger.base_trades:
                self.plots[self.selected] = TradesPnL(
                    document=self.document,
                    trades=self.ledger.base_trades[self.selected],
                )
            elif self.selected in self.ledger.quote_trades:
                self.plots[self.selected] = TradesPnL(
                    document=self.document,
                    trades=self.ledger.quote_trades[self.selected],
                )
            else:
                raise RuntimeError(
                    f"{self.selected} not in {self.ledger.base_trades.keys()} nor in {self.ledger.quote_trades.keys()}"
                )
        return self.plots[self.selected].fig

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value  # changing selection

        tmpplot = self.tradeplot  # from property TMP (since not in cache...)
        tmpplot.children[0] = self.tradefig  # updating show figure
        # TMP : just because ohlcplot is not in cache ??? TODO : FIX BUG...
        self.model.children[1] = tmpplot

    # click events
    def on_base_radio_symbol_click(self, radio_button_index: int, symlist: List[str]):
        if radio_button_index is not None:
            self.quote_radio_button.active = None  # update selection...

            # this alone should trigger update (careful :works for both radio groups !)
            self.selected = symlist[radio_button_index]
            print(f"RadioButton selected {self.selected}")

    # click events
    def on_quote_radio_symbol_click(self, radio_button_index: int, symlist: List[str]):
        if radio_button_index is not None:
            self.base_radio_button.active = None  # update selection...

            # this alone should trigger update (careful :works for both radio groups !)
            self.selected = symlist[radio_button_index]
            print(f"RadioButton selected {self.selected}")


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta, timezone
    from typing import Dict, List

    from bokeh.server.server import Server

    from aiobinance.config import load_api_keyfile

    credentials = load_api_keyfile()
    # Note account can be accessed via exchange, but doesnt have to be...
    binance_client = Binance(credentials=credentials)

    account = Account(api=binance_client)

    async def symbolapp(account: Account, coin: str = "BNB"):
        global binance_client

        # default_timeframe: TimeStep = TimeStep(
        #     timedelta(minutes=1)
        # )  # candle width, ie. timeframe precision
        # num_candles: int = 120  # number of candles of data we want to retrieve

        # retrieve ledger
        ledger: LedgerView = account.assets[coin].ledger

        # display data there
        docs: List[Document] = []
        screens: List[AssetTrades] = []

        print(f"Starting data update loop for {ledger.coininfo.coin}...", end="")
        # retrieving data in background (once, then will loop forever)
        await ledger.loop()
        print(" OK.")

        def appfun(doc: Document):
            nonlocal ledger

            # Building LedgerLayout  (for this symbol) and storing it
            # Note: models must be owned by a single document  # TODO : base and quote in same place ? quote might be empty...
            TS = AssetTrades(
                document=doc,
                ledger=ledger,
                asset=coin,
                base_symlist=list(ledger.base_trades.keys()),
                quote_symlist=list(ledger.quote_trades.keys()),
            )
            screens.append(TS)

            doc.add_root(TS.model)  # note : this will create the layout dynamically
            # storing doc
            docs.append(doc)

        return appfun

    async def server():
        """ starting a bokeh server from async """

        await account()  # required to retrieve info !!!  TODO : improve and unify API behaviors...

        # server = Server({"/COTI": await symbolapp(account=account, coin="COTI")})
        server = Server({"/BNB": await symbolapp(account=account, coin="BNB")})
        server.start()

        print("Opening Bokeh application on http://localhost:5006/")

        server.io_loop.add_callback(server.show, "/")

        # waiting 5 minutes before shutdown...
        await asyncio.sleep(3600)

    asyncio.run(server(), debug=True)
