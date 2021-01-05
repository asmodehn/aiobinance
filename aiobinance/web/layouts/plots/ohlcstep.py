from __future__ import annotations

import functools
from asyncio import QueueEmpty
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

import numpy as np
from bokeh.document import Document
from bokeh.io import save, show
from bokeh.layouts import column, grid, row
from bokeh.models import (
    BooleanFilter,
    Button,
    CDSView,
    Column,
    ColumnDataSource,
    CustomJSFilter,
    GlyphRenderer,
    GroupFilter,
    Select,
)
from bokeh.plotting import Figure

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.timeinterval import (
    TimeInterval,
    TimeIntervalDelta,
    TimeStep,
    timeinterval_to_timedelta,
)
from aiobinance.api.model.tradeframe import TradeFrame
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.tradesview import TradesView


class OHLCStepPlots:

    fig: Figure

    document: Document
    ohlcv: OHLCView
    trades: TradesView
    selected_tf: TimeStep
    num_candles: int

    framesource: OHLCFrame
    datasource: ColumnDataSource
    tradesource: Optional[ColumnDataSource]

    update_needed: asyncio.Event

    highlow: GlyphRenderer
    upbar: GlyphRenderer
    downbar: GlyphRenderer

    def __init__(
        self,
        document: Document,
        ohlcv: OHLCView,
        selected_tf: Optional[TimeStep] = TimeStep(timedelta(minutes=1)),
        num_candles: int = 120,
        trades: Optional[TradesView] = None,
    ):
        """
        An OHLC Plot, mostly self driven...
        :param document: needed to be able to schedule view updates
        :param ohlcv: data storage used for driving data updates
        :param selected_tf: to know which Frame in the (dynamic) OHLCView we should consider
        :param trades: optional
        """
        self.document = document
        self.ohlcv = ohlcv
        self.trades = trades
        self.selected_tf = selected_tf
        self.num_candles = num_candles

        # TODO : this needs to work with empty columsn, as we need it for dynamically adding plots...
        # if ohlcv.empty:
        #     raise RuntimeWarning(
        #         f"{ohlcv} is Empty! Plot might be broken...\n => Pass a non-empty Frame to make sure OHLC plot works as expected."
        #     )

        self.framesource = self.ohlcv[self.selected_tf]
        # because we need to keep a copy of what is diplayed for update compuation later on

        self.datasource = self.framesource.as_datasource(
            compute_mid_time=True, compute_upwards=True
        )
        self.tradesource = self.trades.frame.as_datasource() if self.trades else None

        # send a request for this timeframe (as we would do on change)
        self.ohlcv.expectations.put_nowait(TimeInterval(step=self.selected_tf))

        fig = Figure(
            plot_height=320,
            tools="pan, wheel_zoom",
            toolbar_location="left",
            x_axis_type="datetime",
            y_axis_location="right",
            sizing_mode="scale_width",
        )

        self.highlow = fig.segment(
            source=self.datasource,
            legend_label="OHLC H/L",
            x0="mid_time",
            x1="mid_time",
            y0="low",
            y1="high",
            line_width=1,
            color="black",
        )

        # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
        # This would simplify python code regarding update of this simple filter
        # by transferring hte load to javascript on the client side...

        upview = CDSView(
            source=self.datasource,
            filters=[GroupFilter(column_name="upwards", group="UP")],
        )

        self.upbar = fig.vbar(
            legend_label="OHLC Up",
            source=self.datasource,
            view=upview,
            width=self.selected_tf.delta.value,  # Note: may change with first update !!
            x="mid_time",
            bottom="open",
            top="close",
            fill_color="#D5E1DD",
            line_color="black",
        )

        downview = CDSView(
            source=self.datasource,
            filters=[GroupFilter(column_name="upwards", group="DOWN")],
        )

        self.downbar = fig.vbar(
            legend_label="OHLC Down",
            source=self.datasource,
            view=downview,
            width=self.selected_tf.delta.value,
            x="mid_time",
            top="open",
            bottom="close",
            fill_color="#F2583E",
            line_color="black",
        )
        # we can pass trades to plot together...
        if self.tradesource is not None:
            fig.triangle(
                legend_label="BOUGHT",
                source=self.tradesource,
                view=CDSView(
                    source=self.tradesource,
                    filters=[
                        GroupFilter(column_name="price_boughtsold", group="BOUGHT")
                    ],
                ),
                x="time_utc",
                y="price",
                size=10,
                color="green",
            )

            fig.inverted_triangle(
                legend_label="SOLD",
                source=self.tradesource,
                view=CDSView(
                    source=self.tradesource,
                    filters=[GroupFilter(column_name="upwards", group="SOLD")],
                ),
                x="time_utc",
                y="price",
                size=10,
                color="red",
            )
        fig.legend.location = "top_left"
        fig.legend.click_policy = "hide"

        self.fig = fig

        # TODO : adjust zoom, to make only num_candles visible...

        # Scheduling periodic refresh check :
        print(f"Starting plot update loop for {self.document}...", end="")
        # updating plot in background if necessary
        self.document.add_periodic_callback(
            functools.partial(self, num_candles=self.num_candles),
            period_milliseconds=150,  # quick plot update to refresh display asap
        )
        # Note: for simplicity here we retrieve and update all data, even if there is no request to it
        print(" OK.")

    def _bokeh_update(self, frameupdate: OHLCFrame) -> OHLCStepPlots:
        """ View updates, need to be in sync with document tick... """
        # proceed with the update of this tf...

        newsource = frameupdate.as_datasource(
            compute_mid_time=True, compute_upwards=True
        )

        # TODO: PATCH existing candles in plot...
        # new elements : we stream new data
        # patch method cannot add data BUT it cleans up potential graphical artifacts from previous stream/patches

        # let bokeh refresh entirely from new datasource...
        self.datasource.stream(newsource.data)

        # In all cases:
        # manual patch (somehow bokeh stream fails to patch properly)

        # TODO : Optimization : Later...
        # # computing difference to only get meaningful patches to apply
        # ohlcvpatch = ohlcv.difference(self.ohlcv)
        # # DEBUG
        # # print(ohlcvpatch)
        #
        # if len(ohlcvpatch) > 0 and len(self.ohlcv) > 0:  # otherwise stream has already done the job
        #     prev_close_time = np.datetime64(self.ohlcv.close_time.replace(tzinfo=None))
        #
        #     # compute indexes depending on open_time
        #     idxs = []
        #     for (
        #         ot
        #     ) in (
        #         ohlcvpatch.df.index
        #     ):  # since we are playing with numpy here, lets access the dataframe directly
        #         npot = ot.to_datetime64()
        #         if npot < prev_close_time:  # if opentime is in previous data
        #             # exactly matching open_time on previous datasource and recover numeric index
        #             idx = np.where(self.datasource.data["open_time"] == npot)[
        #                 0
        #             ]  # one dimension
        #             idxs += idx.tolist()
        #         # else we skip those (stream should have handled them, no need to patch)
        #
        #     if idxs:  # only attempting update if there is any difference in past data
        #         dspatch = ohlcvpatch.as_datasource(
        #             compute_mid_time=True, compute_upwards=True
        #         )
        #         # DEBUG
        #         # print(dspatch.data)
        #
        #         # applying indexes to al columns
        #         patches = {
        #             col: [(idx, v) for idx, v in zip(idxs, valarray)]
        #             for col, valarray in dspatch.data.items()
        #         }
        #         self.datasource.patch(patches)
        #
        #     # updating base value in all case when difference detected
        #     # Note: we want to attempt recomputing the same patch on next tick if something fails for some reason
        #     self.ohlcv = ohlcv

        # otherwise nothing changes

        if self.trades is not None:
            # we can use trades to plot together...
            new_tradesource = self.trades.frame.as_datasource()
            if (
                new_tradesource.data != self.tradesource.data
            ):  # detecting difference in datasource (working ? optimal ?)

                # let bokeh refresh entirely from new datasource...
                self.tradesource.stream(new_tradesource.data)

                # is this needed ? probably not...
                # self.tradesource = new_tradesource

        return self

    def __call__(
        self,
        num_candles: int = 120,
    ):
        # determining if we need update... between before and now
        # TODO :this should be adjusted to reflect user interactions with plot
        now = datetime.now(tz=timezone.utc)
        before = now - num_candles * self.selected_tf.delta.value

        plot_close = self.ohlcv[self.selected_tf].close_time
        # request more data if needed, and the queue is empty
        if (
            plot_close is not None
            and now > plot_close + self.selected_tf.delta.value
            and self.ohlcv.expectations.empty()
        ):
            self.ohlcv.expectations.put_nowait(
                TimeInterval(start=before, stop=now, step=self.selected_tf)
            )
        # TODO : shall we move this to the plot itself ?

        try:
            tint = self.ohlcv.updates.get_nowait()

            if tint.step == self.selected_tf:
                # computing differences on ohlcFrame as we cannot trust datasource delta computation :/
                frameupdate = self.ohlcv[self.selected_tf].difference(self.framesource)
                # TODO : OPTIMIZE THIS ! Difference Computation is too slow...
                # let the plot get the updates when it is tick time
                self.document.add_next_tick_callback(
                    functools.partial(self._bokeh_update, frameupdate=frameupdate)
                )
                # storing new framesource for later diff computation
                self.framesource = self.ohlcv[self.selected_tf]
                # Note : datasource will be updated on doc tick, to keep track of that is displayed by document

                # consuming updates
                self.ohlcv.updates.task_done()
            # TODO : what about skipped updates (maybe if two plots on same ohlcview...)
        except QueueEmpty:
            pass

        # TODO : soft shutdown...


if __name__ == "__main__":
    import asyncio

    from bokeh.server.server import Server

    async def symbolapp(symbol: str = "BTCEUR"):

        default_timeframe: TimeStep = TimeStep(
            timedelta(minutes=1)
        )  # candle width, ie. timeframe precision
        # num_candles: int = 120  # number of candles of data we want to retrieve

        # setup empty data proxy for symbol
        dataview: OHLCView = OHLCView(symbol=symbol)

        # display data there
        docs: List[Document] = []
        ohlcvs: List[OHLCStepPlots] = []

        print(f"Starting data update loop for {symbol}...", end="")
        # retrieving data in background (once, then will loop forever)
        await dataview.loop()
        print(" OK.")

        def appfun(doc: Document):
            nonlocal dataview

            # Building OHLCLayout  (for this symbol) and storing it
            # Note: models must be owned by a single document
            plots = OHLCStepPlots(
                document=doc, ohlcv=dataview, selected_tf=default_timeframe
            )
            ohlcvs.append(plots)

            # Creating layout and storing doc
            doc.add_root(column([plots.fig]))
            docs.append(doc)

        return appfun

    async def server():
        """ starting a bokeh server from async """
        server = Server({"/BTCEUR": await symbolapp(symbol="BTCEUR")})
        server.start()

        print("Opening Bokeh application on http://localhost:5006/")

        server.io_loop.add_callback(server.show, "/")

        # waiting 5 minutes before shutdown...
        await asyncio.sleep(3600)

    asyncio.run(server(), debug=True)
