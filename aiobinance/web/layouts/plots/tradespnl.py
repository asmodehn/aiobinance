from __future__ import annotations

import functools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import numpy as np
from bokeh.document import Document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, DataRange1d, GlyphRenderer
from bokeh.plotting import Figure

from aiobinance.api.ledgerview import LedgerView
from aiobinance.api.model.timeinterval import TimeInterval
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.tradesview import TradesView


@dataclass
class TradesPnL:

    document: Document
    trades: TradesView

    @functools.cached_property
    def datasource(self) -> ColumnDataSource:
        return self.trades.frame.as_datasource()

    @functools.cached_property
    def fig(self) -> Figure:

        date_xrange = DataRange1d(  # TODO : improve x_range here...
            follow="end",
            follow_interval=timedelta(weeks=1),
            min_interval=timedelta(days=1),
            max_interval=timedelta(weeks=2),
            # range_padding= 3* self.selected_tf.delta.value
        )
        date_xrange.on_change("start", self.on_xrange_start_changed)
        return Figure(
            plot_height=320,
            tools="pan, wheel_zoom",
            toolbar_location="left",
            x_axis_type="datetime",
            x_range=date_xrange,
            y_axis_location="right",
            sizing_mode="scale_width",
        )

    @functools.cached_property
    def pnl(self) -> GlyphRenderer:
        return self.fig.line(x="time_utc", y="cumvalue", source=self.datasource)

    def __post_init__(self):

        # register update hook
        self.trades.update_hook(callback=self._update_hook)

        # send a request for this timeframe (as we would do on change)
        # Just because I have data there, put in your own symbol & timeinterval to test

        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        stop_time = start_time + timedelta(days=1)
        self.trades.expectations.put_nowait(
            TimeInterval(start=start_time, stop=stop_time)
        )  # simple testing with existing data
        # TODO : dynamic data retrieval
        # self.trades.expectations.put_nowait(TimeInterval())

        # to draw plots
        self.pnl

        # Scheduling periodic refresh check :
        print(
            f"Starting plot update loop for {self.trades.symbol}...",
            end="",
        )
        # updating plot in background if necessary
        self.document.add_periodic_callback(
            functools.partial(self),
            period_milliseconds=5_000,  # quick plot update to refresh display asap
            # attempting to request data from view...
        )
        # Note: for simplicity here we retrieve and update all data, even if there is no request to it
        print(" OK.")

    def _bokeh_update(self, frameupdate: TradeFrame) -> TradesPnL:
        """ View updates, need to be in sync with document tick... """
        # proceed with the update of this tf...

        newsource = frameupdate.as_datasource()

        # PATCH existing plot...
        # for trade in frameupdate:
        #     if trade.time_utc < self.trades.frame.time_utc[0]:
        #         raise NotImplementedError
        #     elif trade.time_utc > self.trades.frame.time_utc[-1]:
        #         raise NotImplementedError

        # new elements : we stream new data
        # patch method cannot add data BUT it cleans up potential graphical artifacts from previous stream/patches
        try:
            # let bokeh refresh entirely from new datasource...
            self.datasource.stream(newsource.data)
        except Exception as e:
            raise e

        return self

    def _update_hook(self, frameupdate: TradeFrame) -> Any:

        # datasource will be patched by bokeh datasource.patch and .stream

        # let the plot get the updates when it is tick time
        self.document.add_next_tick_callback(
            functools.partial(self._bokeh_update, frameupdate=frameupdate)
        )
        # Note : datasource will be updated on doc tick, to keep track of that is displayed by document

        return True  # TODO : something useful to do with the return here ?

    def on_xrange_start_changed(self, attr, old, new):
        print(f"{attr}: {old} -> {new}")
        if (
            old is not None
        ):  # might be none when the data was not there at the start (first draw)
            old = datetime.fromtimestamp(old * 0.001, tz=timezone.utc)

        if new is not None:  # old is needed only for print debug...
            new = datetime.fromtimestamp(new * 0.001, tz=timezone.utc)
            print(f"{attr}: {old} -> {new}")

            # CAREFUL : we dont want the framesource cached version, but the original dynamic one...
            open_time = self.trades.frame.time_utc[0]
            # only realistic if expectation Q is empty:  (duplicate test, but better not to pileup calls when it is knosn to be useless)
            if open_time > new and self.trades.expectations.empty():
                # new data needed
                earliest = min(open_time, new)
                # maybe requesting new data
                self(from_date=earliest, til_date=open_time)

    def __call__(self, from_date: datetime = None, til_date: datetime = None):
        # determining if we need update... between before and now
        # TODO :this should be adjusted to reflect user interactions with plot
        #  if possible should be done reactively, instead of having quick polling like here...
        # til_date = datetime.now(tz=timezone.utc) if til_date is None else til_date
        # from_date = (
        #     til_date - self.num_candles * self.selected_tf.delta.value
        #     if from_date is None
        #     else from_date
        # )
        #
        # # CAREFUL : we dont want the framesource cached version, but the original dynamic one...
        # plot_close = self.trades.time_utc
        # plot_open = self.ohlcv[self.selected_tf].open_time
        #
        # request more data if the queue is empty
        if self.trades.expectations.empty():
            #     if (  # after known data
            #             plot_close is not None
            #             and plot_close + self.selected_tf.delta.value < til_date
            #             and plot_close + self.selected_tf.delta.value
            #             < datetime.fromtimestamp(self.fig.x_range.end * 0.001, tz=timezone.utc)
            #             # only interesting if we dont have hte data yet and we are looking at it right now
            #     ) or (  # before known data
            #             plot_open is not None
            #             and plot_open - self.selected_tf.delta.value > from_date
            #             and plot_open - self.selected_tf.delta.value
            #             > datetime.fromtimestamp(
            #         self.fig.x_range.start * 0.001, tz=timezone.utc
            #     )
            #             # only interesting if we dont have hte data yet and we are looking at it right now
            #     ):
            # Here we request more data from ohlcview
            self.trades.expectations.put_nowait(
                TimeInterval(start=from_date, stop=til_date)
            )

        # TODO : shall we move this to the plot itself ?

        # TODO : soft shutdown...


if __name__ == "__main__":
    import asyncio

    from bokeh.server.server import Server

    from aiobinance.api import BinanceRaw
    from aiobinance.config import load_api_keyfile

    api = BinanceRaw(credentials=load_api_keyfile())
    # We need one api to access private data...

    async def assettradeapp(symbol: str = "COTIBNB"):

        # setup empty data proxy for symbol
        dataview: TradesView = TradesView(api=api, symbol=symbol)

        # display data there
        docs: List[Document] = []
        ohlcvs: List[TradesPnL] = []

        print(f"Starting data update loop for {symbol}...", end="")
        # retrieving data in background (once, then will loop forever)
        await dataview.loop()
        print(" OK.")

        def appfun(doc: Document):
            nonlocal dataview

            # Building OHLCLayout  (for this symbol) and storing it
            # Note: models must be owned by a single document
            plots = TradesPnL(document=doc, trades=dataview)
            ohlcvs.append(plots)

            # Creating layout and storing doc
            doc.add_root(column([plots.fig]))
            docs.append(doc)

        return appfun

    async def server():
        """ starting a bokeh server from async """
        server = Server({"/COTIBNB": await assettradeapp(symbol="COTIBNB")})
        server.start()

        print("Opening Bokeh application on http://localhost:5006/")

        server.io_loop.add_callback(server.show, "/")

        # waiting 5 minutes before shutdown...
        await asyncio.sleep(3600)

    asyncio.run(server(), debug=True)
