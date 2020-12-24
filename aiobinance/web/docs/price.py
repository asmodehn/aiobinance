from typing import Optional

from bokeh.document import Document
from bokeh.layouts import grid, row
from bokeh.models import (
    BooleanFilter,
    CDSView,
    ColumnDataSource,
    CustomJSFilter,
    GlyphRenderer,
)
from bokeh.plotting import Figure

from aiobinance.api.ohlcview import OHLCView


class PriceDocument:

    document: Document
    ohlcv: OHLCView
    datasource: ColumnDataSource

    highlow: GlyphRenderer

    def __init__(self, document: Document, ohlcview: OHLCView):
        self.document = document
        self.ohlcv = ohlcview

        self.datasource = self.ohlcv.frame.as_datasource(compute_mid_time=True)
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

        # up_filter = CustomJSFilter(code='''
        # var indices = [];
        # for (var i = 0; i <= source.data['upwards'].length; i++){
        #     if (source.data['upwards'][i]) {
        #         indices.push(i)
        #     }
        # }
        # return indices;
        # ''')

        fig.vbar(
            legend_label="OHLC Up",
            source=self.datasource,
            view=CDSView(
                source=self.datasource,
                filters=[BooleanFilter(self.datasource.data["upwards"])],
            ),
            width=ohlcview.frame.interval,  # Note: doesnt change with update
            x="mid_time",
            bottom="open",
            top="close",
            fill_color="#D5E1DD",
            line_color="black",
        )

        # down_filter = CustomJSFilter(code='''
        # const indices = [];
        # for (let i = 0; i <= source.data.upwards.length; i++) {
        #     if (! source.data.upwards[i]) {
        #         indices.push(i);
        #     }
        # }
        # return indices;
        # ''')

        fig.vbar(
            legend_label="OHLC Down",
            source=self.datasource,
            view=CDSView(
                source=self.datasource,
                filters=[BooleanFilter(~self.datasource.data["upwards"])],
            ),
            width=ohlcview.frame.interval,  # Note: doesnt change with update
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
        self,
    ):  # Note : parameters here are for web-initiated information/actions
        # TODO : check if we hold document lock
        try:
            # current ohlcview has already everything we need to update the plot
            newsource = self.ohlcv.frame.as_datasource(compute_mid_time=True)

            # For now: let bokeh refresh entirely from new datasource...
            self.datasource.stream(newsource.data)
            # self.highlow.data_source.stream(newsource.data)

            # update/patch is an optimization... later.
        except RuntimeError:
            # if we dont have document lock
            self.document.add_next_tick_callback(self)
        #
        # updown = [
        #     o < c for o, c in zip(delta.open, delta.close)
        # ]
        #
        # # here we assume the time interval is regular and uniform
        # timeinterval = delta.index[1] - delta.index[0]
        #
        # # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
        # # This would simplify python code regarding update of this simple filter
        # # by transferring hte load to javascript on the client side...
        # self._fig.vbar(
        #     legend_label="OHLC Up",
        #     source=delta.as_datasource(),
        #     view=CDSView(source=delta.as_datasource(), filters=[BooleanFilter(updown)]),
        #     width=timeinterval,
        #     x="mid_time",
        #     bottom="open",
        #     top="close",
        #     fill_color="#D5E1DD",
        #     line_color="black",
        # )
        #
        # self._fig.vbar(
        #     legend_label="OHLC Down",
        #     source=delta.as_datasource(),
        #     view=CDSView(
        #         source=delta.as_datasource(), filters=[BooleanFilter([not b for b in updown])]
        #     ),
        #     width=timeinterval,
        #     x="mid_time",
        #     top="open",
        #     bottom="close",
        #     fill_color="#F2583E",
        #     line_color="black",
        # )
        #
        # self._fig.legend.location = "top_left"
        # self._fig.legend.click_policy = "hide"

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

        # TODO compute historical midprices


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta, timezone

    from bokeh.io import curdoc, output_file, save, show

    # export the document as html
    output_file("price.html")

    # setup data proxy for BTCEUR symbol
    ohlc = OHLCView(symbol="BTCEUR")

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
    price = PriceDocument(curdoc(), ohlc)

    # Outputting
    price.show()

    # Note : dynamic update is not testable in this simple doc output mode.
    # Use modules in aiobinance.web for dynamic plots.
