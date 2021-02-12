from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, List, Optional

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
    DataRange1d,
    GlyphRenderer,
    GroupFilter,
    Legend,
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


@dataclass
class OHLCStepPlots:

    document: Document
    ohlcv: OHLCView
    trades: Optional[TradesView] = field(default=None)

    selected_tf: TimeStep = field(default=TimeIntervalDelta.minutely)
    num_candles: int = field(default=120)

    # update_needed: asyncio.Event = field(default_factory=asyncio.Event)

    @functools.cached_property  # cached here for consistency in plot
    def framesource(self) -> OHLCFrame:
        return self.ohlcv[self.selected_tf]  # for dynamic data, access it directly.

    @functools.cached_property
    def datasource(self) -> ColumnDataSource:
        return self.framesource.as_datasource(
            compute_mid_time=True, compute_upwards=True
        )

    @functools.cached_property
    def tradesource(self) -> Optional[ColumnDataSource]:
        if self.trades:
            return self.trades.frame.as_datasource()

    @functools.cached_property
    def fig(self) -> Figure:

        date_xrange = DataRange1d(  # TODO : improve x_range here...
            follow="end",
            follow_interval=self.num_candles * self.selected_tf.delta.value,
            # computation  is somehow wrong here ??
            min_interval=(self.num_candles // 2) * self.selected_tf.delta.value,
            max_interval=self.num_candles * 2 * self.selected_tf.delta.value,
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
    def highlow(self) -> GlyphRenderer:
        return self.fig.segment(
            source=self.datasource,
            legend_label="OHLC H/L",
            x0="mid_time",
            x1="mid_time",
            y0="low",
            y1="high",
            line_width=1,
            color="black",
        )

    @functools.cached_property
    def upbar(self) -> GlyphRenderer:
        source = self.datasource
        return self.fig.vbar(
            legend_label="OHLC Up",
            source=source,  # has to be same as in CDSView
            view=CDSView(
                source=source,
                filters=[GroupFilter(column_name="upwards", group="UP")],
                # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
                # This would simplify python code regarding update of this simple filter
                # by transferring hte load to javascript on the client side...
            ),
            width=self.selected_tf.delta.value,  # Note: may change with first update !!
            x="mid_time",
            bottom="open",
            top="close",
            fill_color="#D5E1DD",
            line_color="black",
        )

    @functools.cached_property
    def downbar(self) -> GlyphRenderer:
        source = self.datasource
        return self.fig.vbar(
            legend_label="OHLC Down",
            source=source,  # has to be same as in CDSView
            view=CDSView(
                source=source,
                filters=[GroupFilter(column_name="upwards", group="DOWN")],
                # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
                # This would simplify python code regarding update of this simple filter
                # by transferring hte load to javascript on the client side...
            ),
            width=self.selected_tf.delta.value,
            x="mid_time",
            top="open",
            bottom="close",
            fill_color="#F2583E",
            line_color="black",
        )

    @functools.cached_property
    def bought(self) -> Optional[GlyphRenderer]:
        if self.tradesource is not None:
            return self.fig.triangle(
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

    @functools.cached_property
    def sold(self) -> Optional[GlyphRenderer]:
        if self.tradesource is not None:
            return self.fig.inverted_triangle(
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

    # def __init__(
    #     self,
    #     document: Document,
    #     ohlcv: OHLCView,
    #     selected_tf: Optional[TimeStep] = TimeStep(timedelta(minutes=1)),
    #     num_candles: int = 120,
    #     trades: Optional[TradesView] = None,
    #     **figure_kwargs  # to pass extra arguments to the figure,
    #     # but maybe the whold class should inherit from it and describe components with properties
    #     # similar to what bokeh does ?
    # ):
    #     """
    #     An OHLC Plot, mostly self driven...
    #     :param document: needed to be able to schedule view updates
    #     :param ohlcv: data storage used for driving data updates
    #     :param selected_tf: to know which Frame in the (dynamic) OHLCView we should consider
    #     :param trades: optional
    #     """
    #     self.document = document
    #     self.ohlcv = ohlcv
    #     self.trades = trades
    #     self.selected_tf = selected_tf
    #     self.num_candles = num_candles
    #
    #     # TODO : this needs to work with empty columsn, as we need it for dynamically adding plots...
    #     # if ohlcv.empty:
    #     #     raise RuntimeWarning(
    #     #         f"{ohlcv} is Empty! Plot might be broken...\n => Pass a non-empty Frame to make sure OHLC plot works as expected."
    #     #     )
    #
    #
    #     # because we need to keep a copy of what is displayed for update computation later on

    def on_xrange_start_changed(self, attr, old, new):
        if (
            old is not None
        ):  # might be none when the data was not there at the start (first draw)
            old = datetime.fromtimestamp(old * 0.001, tz=timezone.utc)

        if new is not None:  # old is needed only for print debug...
            new = datetime.fromtimestamp(new * 0.001, tz=timezone.utc)
            print(f"{attr}: {old} -> {new}")

            # CAREFUL : we dont want the framesource cached version, but the original dynamic one...
            open_time = self.ohlcv[self.selected_tf].open_time
            # only realistic if expectation Q is empty:  (duplicate test, but better not to pileup calls when it is knosn to be useless)
            if open_time > new and self.ohlcv.expectations.empty():
                # new data needed
                earliest = min(
                    open_time - self.num_candles * self.selected_tf.delta.value, new
                )
                # maybe requesting new data
                self(from_date=earliest, til_date=open_time)

    def __post_init__(self):

        # register update hook
        self.ohlcv.update_hook(ts=self.selected_tf, callback=self._update_hook)

        # send a request for this timeframe (as we would do on change)
        self.ohlcv.expectations.put_nowait(TimeInterval(step=self.selected_tf))

        # # NOT WORKING :-/
        # fig.on_change(
        #     "x_range",
        #     lambda attr, old, new: print(f"{attr}: {old} -> {new} : x_range_changed !"),
        # )

        # calling plots to draw them and create legend
        self.highlow
        self.upbar
        self.downbar
        self.bought
        self.sold

        # modifying fig (in cache, after legend creation)
        self.fig.legend.location = "top_left"
        self.fig.legend.click_policy = "hide"

        # TODO : adjust zoom, to make only num_candles visible...

        # Scheduling periodic refresh check :
        print(
            f"Starting plot update loop for {self.ohlcv.symbol} {self.selected_tf}...",
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

    def _bokeh_update(self, frameupdate: OHLCFrame) -> OHLCStepPlots:
        """ View updates, need to be in sync with document tick... """
        # proceed with the update of this tf...

        newsource = frameupdate.as_datasource(
            compute_mid_time=True, compute_upwards=True
        )

        # TODO: PATCH existing candles in plot...
        # new elements : we stream new data
        # patch method cannot add data BUT it cleans up potential graphical artifacts from previous stream/patches
        try:
            # let bokeh refresh entirely from new datasource...
            self.datasource.stream(newsource.data)
        except Exception as e:
            raise e
        # In all cases:
        # manual patch (somehow bokeh stream fails to patch properly)

        # TODO : Optimization : Later...
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

    def _update_hook(self, frameupdate: OHLCFrame) -> Any:

        # datasource will be patched by bokeh datasource.patch and .stream

        # let the plot get the updates when it is tick time
        self.document.add_next_tick_callback(
            functools.partial(self._bokeh_update, frameupdate=frameupdate)
        )
        # Note : datasource will be updated on doc tick, to keep track of that is displayed by document

        return True  # TODO : something useful to do with the return here ?

    def __call__(self, from_date: datetime = None, til_date: datetime = None):
        # determining if we need update... between before and now
        # TODO :this should be adjusted to reflect user interactions with plot
        #  if possible should be done reactively, instead of having quick polling like here...
        til_date = datetime.now(tz=timezone.utc) if til_date is None else til_date
        from_date = (
            til_date - self.num_candles * self.selected_tf.delta.value
            if from_date is None
            else from_date
        )

        # CAREFUL : we dont want the framesource cached version, but the original dynamic one...
        plot_close = self.ohlcv[self.selected_tf].close_time
        plot_open = self.ohlcv[self.selected_tf].open_time

        # request more data if the queue is empty
        if self.ohlcv.expectations.empty():
            if (  # after known data
                plot_close is not None
                and plot_close + self.selected_tf.delta.value < til_date
                and plot_close + self.selected_tf.delta.value
                < datetime.fromtimestamp(self.fig.x_range.end * 0.001, tz=timezone.utc)
                # only interesting if we dont have hte data yet and we are looking at it right now
            ) or (  # before known data
                plot_open is not None
                and plot_open - self.selected_tf.delta.value > from_date
                and plot_open - self.selected_tf.delta.value
                > datetime.fromtimestamp(
                    self.fig.x_range.start * 0.001, tz=timezone.utc
                )
                # only interesting if we dont have hte data yet and we are looking at it right now
            ):
                # Here we request more data from ohlcview
                self.ohlcv.expectations.put_nowait(
                    TimeInterval(start=from_date, stop=til_date, step=self.selected_tf)
                )
        # TODO : shall we move this to the plot itself ?

        # TODO : soft shutdown...


if __name__ == "__main__":
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
