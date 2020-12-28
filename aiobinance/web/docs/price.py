from typing import Optional

import numpy as np
from bokeh.document import Document
from bokeh.io import save, show
from bokeh.layouts import grid, row
from bokeh.models import (
    BooleanFilter,
    CDSView,
    ColumnDataSource,
    CustomJSFilter,
    GlyphRenderer,
    GroupFilter,
)
from bokeh.plotting import Figure

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.ohlcview import OHLCView


class PriceDocument:

    document: Document
    ohlcv: OHLCFrame
    datasource: ColumnDataSource

    highlow: GlyphRenderer
    upbar: GlyphRenderer
    downbar: GlyphRenderer

    def __init__(self, document: Document, ohlcv: OHLCFrame):
        self.document = document
        self.ohlcv = ohlcv

        if ohlcv.empty:
            raise RuntimeWarning(
                f"{ohlcv} is Empty! Plot might be broken...\n => Pass a non-empty Frame to make sure OHLC plot works as expected."
            )

        self.datasource = self.ohlcv.as_datasource(compute_mid_time=True)

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
            width=ohlcv.interval,  # Note: may change with first update !!
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
            width=ohlcv.interval,  # Note: may change with first update !!
            x="mid_time",
            top="open",
            bottom="close",
            fill_color="#F2583E",
            line_color="black",
        )

        fig.legend.location = "top_left"
        fig.legend.click_policy = "hide"

        fig = grid([fig])

        self.document.add_root(row(fig, sizing_mode="scale_width"))

    def save(self):
        """ shortcut to save document content """
        return save(self.document.roots[0])  # only one root in doc

    def show(self):
        """ shortcut to show document content """
        return show(self.document.roots[0])  # only one root in doc

    def __call__(
        self, ohlcv: OHLCFrame
    ):  # Note : parameters here are for web-initiated information/actions

        assert (
            self.ohlcv.interval is None  # we had no data defining interval
            or ohlcv.interval == self.ohlcv.interval
        )  # or the interval is the same
        # TODO: otherwise ??

        if len(ohlcv) > len(self.ohlcv):  # new elements : we stream new data
            # patch method cannot add data + it cleans up potential graphical artifacts from previous patches

            newsource = ohlcv.as_datasource(compute_mid_time=True, compute_upwards=True)

            try:
                # let bokeh refresh entirely from new datasource...
                self.datasource.stream(newsource.data)
            except RuntimeError:
                # if we dont have document lock
                self.document.add_next_tick_callback(self)
                return self  # early return : no point to attempt patching here

        # In all cases:
        # manual patch (somehow bokeh stream fails to patch properly)

        # computing difference to only get meaningful patches to apply
        ohlcvpatch = ohlcv.difference(self.ohlcv)
        print(ohlcvpatch)

        if len(ohlcvpatch) > 0:

            prev_close_time = np.datetime64(self.ohlcv.close_time.replace(tzinfo=None))

            # compute indexes depending on open_time
            idxs = []
            for (
                ot
            ) in (
                ohlcvpatch.df.index
            ):  # since we are playing with numpy here, lets access the dataframe directly
                npot = ot.to_datetime64()
                if npot < prev_close_time:  # if opentime is in previous data
                    # exactly matching open_time on previous datasource and recover numeric index
                    idx = np.where(self.datasource.data["open_time"] == npot)[
                        0
                    ]  # one dimension
                    idxs += idx.tolist()
                # else we skip those (stream should have handled them, no need to patch)

            if idxs:  # only attempting update if there is any difference in past data
                dspatch = ohlcvpatch.as_datasource(
                    compute_mid_time=True, compute_upwards=True
                )
                print(dspatch.data)

                # applying indexes to al columns
                patches = {
                    col: [(idx, v) for idx, v in zip(idxs, valarray)]
                    for col, valarray in dspatch.data.items()
                }
                self.datasource.patch(patches)

            # updating base value in all case when difference detected
            # Note: we want to attempt recomputing the same patch on next tick if something fails for some reason
            self.ohlcv = ohlcv

        # otherwise nothing changes

        # TODO : reactivat LATER...
        # # we can pass trades to plot together...
        # if trades is not None and len(trades) > 0:
        #     bought_source = trades.as_datasource(side=OrderSide.BUY)  # TODO : boolean filter for this as well
        #     sold_source = trades.as_datasource(side=OrderSide.SELL)
        #
        #     self._fig.triangle(
        #         legend_label="BOUGHT",
        #         source=bought_source,
        #         x="time_utc",
        #         y="price",
        #         size=10,
        #         color="green",
        #     )
        #
        #     self._fig.inverted_triangle(
        #         legend_label="SOLD",
        #         source=sold_source,
        #         x="time_utc",
        #         y="price",
        #         size=10,
        #         color="red",
        #     )

        return self


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta, timezone
    from typing import Dict

    from bokeh.server.server import Server

    timeframe: timedelta = timedelta(minutes=1)  # candle width, ie. timeframe precision
    num_candles: int = 120  # number of candle of data we want to retrieve

    # storing all data here
    views: Dict[str, OHLCView] = {}

    async def dataupdate(v: OHLCView, trampoline_period: Optional[timedelta] = None):
        global num_candles, timeframe

        if trampoline_period:
            # periodic
            await asyncio.sleep(trampoline_period.total_seconds())

        # retieving data for num_candles
        before = datetime.now(tz=timezone.utc) - num_candles * timeframe
        now = datetime.now(tz=timezone.utc)

        # now actually retrieving up-to-date data
        await v(start_time=before, stop_time=now)

        if trampoline_period:
            # trampoline
            asyncio.get_event_loop().create_task(
                dataupdate(v=v, trampoline_period=trampoline_period)
            )

    async def symbolapp(symbol: str = "BTCEUR"):
        global views

        if symbol not in views:
            # setup empty data proxy for symbol
            views[symbol] = OHLCView(symbol=symbol)
            print(f"Retrieving data for {symbol}...", end="")
            await dataupdate(views[symbol])  # retrieving data on startup
            # Note: for simplicity here we retrieve and update all data, even if there is no request to it
            print(" OK.")
            asyncio.get_event_loop().create_task(
                dataupdate(views[symbol], trampoline_period=timeframe / 2)
            )
            print(f"Periodic update for {symbol} has been scheduled.")

        def appfun(doc: Document):
            global views

            # Building PriceDocument
            price = PriceDocument(doc, views[symbol].frame)

            def update():
                # updating plot (sync method -> has to be disjoint from the actual OHLC data update)
                price(views[symbol].frame)

            # doc will drive periodic plot update loop
            doc.add_periodic_callback(
                update, period_milliseconds=int((timeframe / 2).total_seconds() * 1000)
            )

        return appfun

    async def server():
        """ starting a bokeh server from async """
        server = Server({"/BTCEUR": await symbolapp(symbol="BTCEUR")})
        server.start()

        print("Opening Bokeh application on http://localhost:5006/")

        server.io_loop.add_callback(server.show, "/")

        # waiting 5 minutes before shutdown...
        await asyncio.sleep(3600)

    asyncio.run(server())
