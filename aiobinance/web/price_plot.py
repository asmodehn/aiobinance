
from ..model import OHLCV, Trades

from bokeh.models import ColumnDataSource, CDSView, BooleanFilter
from bokeh.plotting import Figure, figure


def price_plot(ohlcv: OHLCV, trades: Trades =None) -> Figure:
    timeinterval = (ohlcv['open_time'][1] - ohlcv['open_time'][0])
    ohlcv['mid_time'] = ohlcv['open_time'] + timeinterval / 2

    print(ohlcv['mid_time'][0])

    ohlc_source = ColumnDataSource(ohlcv.df)

    figure = Figure(plot_height=320, tools='pan, wheel_zoom', toolbar_location="left",
                    x_axis_type="datetime", y_axis_location="right",
                    sizing_mode="scale_width")

    figure.segment(source=ohlc_source, legend_label="OHLC H/L",
                   x0='mid_time', x1='mid_time',
                   y0='low', y1='high',
                   line_width=1, color='black')

    updown = [o < c for o, c in zip(ohlc_source.data['open'], ohlc_source.data['close'])]

    # TODO : https://docs.bokeh.org/en/latest/docs/user_guide/data.html#customjsfilter
    # This would simplify python code regarding update of this simple filter
    # by transferring hte load to javascript on the client side...
    figure.vbar(legend_label="OHLC Up",
                source=ohlc_source,
                view=CDSView(source=ohlc_source, filters=[BooleanFilter(updown)]),
                width=timeinterval,
                x='mid_time',
                bottom='open', top='close',
                fill_color="#D5E1DD", line_color="black",
                )

    figure.vbar(legend_label="OHLC Down",
                source=ohlc_source,
                view=CDSView(source=ohlc_source, filters=[BooleanFilter([not b for b in updown])]),
                width=timeinterval,
                x='mid_time',
                top='open', bottom='close',
                fill_color="#F2583E", line_color="black",
                )

    figure.legend.location = "top_left"
    figure.legend.click_policy = "hide"

    # we can pass trades to plot together...
    if trades is not None:
        bought_source = ColumnDataSource(trades.loc[trades['Trade'] == "BUY"])
        sold_source = ColumnDataSource(trades.loc[trades['Trade'] == "SELL"])

        figure.triangle(legend_label="BOUGHT",
                        source=bought_source,
                        x='datetime',
                        y='Price',
                        size=10,
                        color='green')

        figure.inverted_triangle(legend_label="SOLD",
                                 source=sold_source,
                                 x='datetime',
                                 y='Price',
                                 size=10,
                                 color='red')

    return figure

    # TODO compute historical midprices