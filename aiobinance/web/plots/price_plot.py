from typing import Optional

from bokeh.document import Document
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource
from bokeh.plotting import Figure

from ...api.model.order import OrderSide
from ...api.ohlcview import OHLCView
from ...api.pure.ohlcviewbase import OHLCViewBase
from ...api.tradesview import TradesView


class PricePlot:
    # TODO : maybe more  document, than only the plot, given we need to synchronise callbacks for any change...
    _doc: Document
    _fig: Figure
    _dataview: OHLCViewBase
    _ohlc_source: ColumnDataSource

    def __init__(self, doc: Document, ohlcv: OHLCViewBase):
        self._doc = doc
        self._dataview = ohlcv

        self._fig = Figure(
            plot_height=320,
            tools="pan, wheel_zoom",
            toolbar_location="left",
            x_axis_type="datetime",
            y_axis_location="right",
            sizing_mode="scale_width",
        )

        self._ohlc_source = ohlcv.as_datasource(compute_mid_time=True)

        self._fig.segment(
            source=self._ohlc_source,
            legend_label="OHLC H/L",
            x0="mid_time",
            x1="mid_time",
            y0="low",
            y1="high",
            line_width=1,
            color="black",
        )
        # TODO : is it possible to setup a filter that works dynamically on later datasources when streamed ??
        updown = [
            o < c
            for o, c in zip(
                self._ohlc_source.data["open"], self._ohlc_source.data["close"]
            )
        ]

        # here we assume the time interval is regular and uniform
        timeinterval = (
            self._ohlc_source.data["open_time"][1]
            - self._ohlc_source.data["open_time"][0]
        )

        # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
        # This would simplify python code regarding update of this simple filter
        # by transferring hte load to javascript on the client side...
        self._fig.vbar(
            legend_label="OHLC Up",
            source=self._ohlc_source,
            view=CDSView(source=self._ohlc_source, filters=[BooleanFilter(updown)]),
            width=timeinterval,
            x="mid_time",
            bottom="open",
            top="close",
            fill_color="#D5E1DD",
            line_color="black",
        )

        self._fig.vbar(
            legend_label="OHLC Down",
            source=self._ohlc_source,
            view=CDSView(
                source=self._ohlc_source,
                filters=[BooleanFilter([not b for b in updown])],
            ),
            width=timeinterval,
            x="mid_time",
            top="open",
            bottom="close",
            fill_color="#F2583E",
            line_color="black",
        )

        self._fig.legend.location = "top_left"
        self._fig.legend.click_policy = "hide"

    def __call__(
        self,
    ):  # Note : parameters here are for web-initiated information/actions
        def newstream():
            # current ohlcview has already everything we need to update the plot
            newsource = self._dataview.as_datasource(compute_mid_time=True)

            # For now: let bokeh refresh entirely from new datasource...
            self._ohlc_source.stream(newsource.data)
            # update/patch is an optimization... later.

        # need to have lock on document when updating.
        self._doc.add_next_tick_callback(newstream)

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
