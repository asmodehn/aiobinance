from typing import Optional

import numpy as np
from bokeh.document import Document
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

    def __init__(self, document: Document, ohlcv: OHLCFrame):
        self.document = document
        self.ohlcv = ohlcv

        self.datasource = self.ohlcv.as_datasource(compute_mid_time=True)
        # TODO : view could be a self-updating datasource ??

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

        # we need this, likely until we get the jsfilter to work:
        self.upview = CDSView(
            source=self.datasource,
            filters=[GroupFilter(column_name="upwards", group="UP")],
        )

        fig.vbar(
            legend_label="OHLC Up",
            source=self.datasource,
            view=self.upview,
            width=ohlcv.interval,  # Note: doesnt change with update
            x="mid_time",
            bottom="open",
            top="close",
            fill_color="#D5E1DD",
            line_color="black",
        )

        self.downview = CDSView(
            source=self.datasource,
            filters=[GroupFilter(column_name="upwards", group="DOWN")],
        )

        fig.vbar(
            legend_label="OHLC Down",
            source=self.datasource,
            view=self.downview,
            width=ohlcv.interval,  # Note: doesnt change with update
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

        assert ohlcv.interval == self.ohlcv.interval  # TODO: otherwise ??

        if len(ohlcv) > len(
            self.ohlcv
        ):  # new elements : we stream new data (patch method cannot add data)

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

            prev_close_time = np.datetime64(self.ohlcv.close_time)

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

    from bokeh.io import curdoc, output_file, save, show

    # export the document as html
    output_file("price.html")

    # setup data proxy for BTCEUR symbol
    ohlc = OHLCView(symbol="BTCEUR")

    # TODO : let a simple bokeh server manage the update (cli option)
    # data update
    async def update():
        # now actually retrieving data
        before = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        now = datetime.now(tz=timezone.utc)

        # doing an update with a full set of data to test it as much as possible.
        await ohlc(start_time=before, stop_time=now)

    # get data BEFORE building doc.
    asyncio.run(update())

    # Building Price Document
    price = PriceDocument(curdoc(), ohlc.frame)

    # Outputting
    price.show()

    # Note : dynamic update is not testable in this simple doc output mode.
    # Use modules in aiobinance.web for dynamic plots.
