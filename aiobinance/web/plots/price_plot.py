from bokeh.models import BooleanFilter, CDSView, ColumnDataSource
from bokeh.plotting import Figure

from ...api.ohlcview import OHLCView
from ...api.tradesview import TradesView


def price_plot(ohlcv: OHLCView, trades: TradesView = None) -> Figure:
    ohlc_source = ohlcv.as_datasource(compute_mid_time=True)

    figure = Figure(
        plot_height=320,
        tools="pan, wheel_zoom",
        toolbar_location="left",
        x_axis_type="datetime",
        y_axis_location="right",
        sizing_mode="scale_width",
    )

    figure.segment(
        source=ohlc_source,
        legend_label="OHLC H/L",
        x0="mid_time",
        x1="mid_time",
        y0="low",
        y1="high",
        line_width=1,
        color="black",
    )

    updown = [
        o < c for o, c in zip(ohlc_source.data["open"], ohlc_source.data["close"])
    ]

    # here we assume the time interval is regular and uniform
    timeinterval = ohlc_source.data["open_time"][1] - ohlc_source.data["open_time"][0]

    # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
    # This would simplify python code regarding update of this simple filter
    # by transferring hte load to javascript on the client side...
    figure.vbar(
        legend_label="OHLC Up",
        source=ohlc_source,
        view=CDSView(source=ohlc_source, filters=[BooleanFilter(updown)]),
        width=timeinterval,
        x="mid_time",
        bottom="open",
        top="close",
        fill_color="#D5E1DD",
        line_color="black",
    )

    figure.vbar(
        legend_label="OHLC Down",
        source=ohlc_source,
        view=CDSView(
            source=ohlc_source, filters=[BooleanFilter([not b for b in updown])]
        ),
        width=timeinterval,
        x="mid_time",
        top="open",
        bottom="close",
        fill_color="#F2583E",
        line_color="black",
    )

    figure.legend.location = "top_left"
    figure.legend.click_policy = "hide"

    # we can pass trades to plot together...
    if trades is not None and len(trades) > 0:
        opt_trades = trades.frame.optimized()

        bought_source = ColumnDataSource(opt_trades.loc[opt_trades["is_buyer"]])
        sold_source = ColumnDataSource(opt_trades.loc[~opt_trades["is_buyer"]])

        figure.triangle(
            legend_label="BOUGHT",
            source=bought_source,
            x="time",
            y="price",
            size=10,
            color="green",
        )

        figure.inverted_triangle(
            legend_label="SOLD",
            source=sold_source,
            x="time",
            y="price",
            size=10,
            color="red",
        )

    return figure

    # TODO compute historical midprices
