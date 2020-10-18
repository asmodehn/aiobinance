import pandas as pd

from .rawapi import Binance

from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, Legend
from bokeh.plotting import Figure


class OHLCV:

    df: pd.DataFrame

    def __init__(self, startTime, endTime, symbol):
        self.api = Binance(API_KEY="", API_SECRET="")  # we dont need private requests here
        # Ref : https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

        interval = Binance.interval(startTime, endTime)

        res = self.api.call_api(command='klines', symbol=symbol, interval=interval, startTime=startTime, endTime=endTime,
                       limit=1000)

        # Ref : https://gist.github.com/ashwinimaurya/06728a31bcfb08209ef4fb13fd058163#file-binance_ohlc-py
        columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol',
                   'taker_quote_vol', 'is_best_match']
        self.df = pd.DataFrame(data=res, columns=columns)

        self.df.open_time = pd.to_datetime(self.df.open_time, unit='ms')
        self.df.close_time = pd.to_datetime(self.df.close_time, unit='ms')

    def head(self):
        return self.df.head()

    def plot(self, trades=None) -> Figure:

        timeinterval = (self.df['open_time'][1] - self.df['open_time'][0])
        self.df['mid_time'] = self.df['open_time'] + timeinterval / 2

        print(self.df['mid_time'][0])

        ohlc_source = ColumnDataSource(self.df)

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