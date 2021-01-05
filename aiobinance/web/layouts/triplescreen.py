import functools
from asyncio import QueueEmpty
from typing import Dict, List, Optional

from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.model import Model
from bokeh.models import Button, RadioButtonGroup

from aiobinance.api.model.timeinterval import TimeInterval, TimeIntervalDelta, TimeStep
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.tradesview import TradesView
from aiobinance.web.layouts.plots.ohlcstep import OHLCStepPlots


class TripleScreen:

    document: Document
    ohlcv: OHLCView
    trades: TradesView

    # relevant graphical component for each timestep
    plots: Dict[TimeStep, OHLCStepPlots]

    @property
    def layout(self):
        """ returning the entire layout. this is useful for dynamic layout to keep track of updates..."""
        if not self.document.roots:
            return None
        return self.document.roots[0]

    @layout.setter
    def layout(self, newmodel):
        self.document.remove_root(self.layout)
        self.document.add_root(newmodel)

    # accessors, also managing layout updates
    # Layout as properties with setter to make updates seamless
    @property
    def left_model(self):
        if self.layout is None:
            return None
        # accessing the left column layout
        return self.layout.children[0]

    @left_model.setter
    def left_model(self, newmodel):
        self.layout = row(
            newmodel,
            self.layout.children[1],
            self.layout.children[2],
            sizing_mode="scale_width",
        )

    @property
    def right_model(self):
        if self.layout is None:
            return None
        # accessing the right column layout
        return self.layout.children[2]

    @right_model.setter
    def right_model(self, newmodel):
        self.layout = row(
            self.layout.children[0],
            self.layout.children[1],
            newmodel,
            sizing_mode="scale_width",
        )

    @property
    def center_model(self):
        if self.layout is None:
            return None
        # accessing the center column layout
        return self.layout.children[1]

    @center_model.setter
    def center_model(self, newmodel):
        if self.layout is None:
            left = self.empty_left_column()
            right = self.empty_right_column()
        else:
            left = self.layout.children[0]
            right = self.layout.children[2]

        self.layout = row(left, newmodel, right, sizing_mode="scale_width")

    def empty_left_column(
        self, tslist: List[TimeStep] = None, selected: TimeStep = None
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = max(tslist) if selected is None else selected

        # add button to add left column
        lb = Button(label="+", width_policy="min")
        lb.on_click(
            functools.partial(self.on_left_plus, tslist=tslist, selected=selected)
        )
        return column(lb)

    def empty_right_column(
        self, tslist: List[TimeStep] = None, selected: TimeStep = None
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = min(tslist) if selected is None else selected

        # add button to add right column
        rb = Button(label="+", width_policy="min")
        rb.on_click(
            functools.partial(self.on_right_plus, tslist=tslist, selected=selected)
        )
        return column(rb)

    def widget_right_column(
        self, tslist: List[TimeStep] = None, selected: TimeStep = None
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = min(tslist) if selected is None else selected

        # add button to add right column
        rb = Button(label="-", width_policy="min")
        rb.on_click(
            functools.partial(self.on_right_minus, tslist=tslist, selected=selected)
        )

        rprb = RadioButtonGroup(
            labels=[str(ts) for ts in tslist], active=tslist.index(selected)
        )
        rprb.on_click(
            functools.partial(self.on_right_radio_timestep_click, tslist=tslist)
        )

        # Note : we need to scale the row like the button to avoid overlapping buttons...
        widget_row = row(rprb, rb, sizing_mode="scale_width")
        return widget_row

    def plot_right_column(
        self, tslist: List[TimeStep] = None, selected: TimeStep = None
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = min(tslist) if selected is None else selected

        if selected not in self.plots:
            # create it
            self.plots[selected] = OHLCStepPlots(
                document=self.document, ohlcv=self.ohlcv, selected_tf=selected
            )

        plot_row = row(self.plots[selected].fig, sizing_mode="scale_width")
        return plot_row

    def right_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:
        widget_row = self.widget_right_column(tslist=tslist, selected=selected)
        plot_row = self.plot_right_column(tslist=tslist, selected=selected)

        return column(widget_row, plot_row, sizing_mode="scale_width")

    def widget_left_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = max(tslist) if selected is None else selected

        lb = Button(label="-", width_policy="min")
        lb.on_click(
            functools.partial(self.on_left_minus, tslist=tslist, selected=selected)
        )

        lprb = RadioButtonGroup(
            labels=[str(ts) for ts in tslist], active=tslist.index(selected)
        )
        lprb.on_click(
            functools.partial(self.on_left_radio_timestep_click, tslist=tslist)
        )

        # Note : we need to scale the row like the button to avoid overlapping buttons...
        widget_row = row(lb, lprb, sizing_mode="scale_width")

        return widget_row

    def plot_left_column(
        self, tslist: List[TimeStep] = None, selected: TimeStep = None
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = max(tslist) if selected is None else selected

        if selected not in self.plots:
            # create it
            self.plots[selected] = OHLCStepPlots(
                document=self.document, ohlcv=self.ohlcv, selected_tf=selected
            )

        plot_row = row(self.plots[selected].fig, sizing_mode="scale_width")

        return plot_row

    def left_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:

        widget_row = self.widget_left_column(tslist=tslist, selected=selected)
        plot_row = self.plot_left_column(tslist=tslist, selected=selected)

        return column(widget_row, plot_row, sizing_mode="scale_width")

    def widget_center_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = max(tslist) if selected is None else selected

        # No min button on center column

        lprb = RadioButtonGroup(
            labels=[str(ts) for ts in tslist], active=tslist.index(selected)
        )
        lprb.on_click(
            functools.partial(self.on_center_radio_timestep_click, tslist=tslist)
        )

        # Note : we need to scale the row like the button to avoid overlapping buttons...
        widget_row = row(lprb, sizing_mode="scale_width")

        return widget_row

    def plot_center_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:

        tslist = (
            [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
            if tslist is None
            else tslist
        )
        selected = max(tslist) if selected is None else selected

        if selected not in self.plots:
            # create it
            self.plots[selected] = OHLCStepPlots(
                document=self.document, ohlcv=self.ohlcv, selected_tf=selected
            )

        plot_row = row(self.plots[selected].fig, sizing_mode="scale_width")

        return plot_row

    def center_column(
        self,
        tslist: Optional[List[TimeStep]] = None,
        selected: Optional[TimeStep] = None,
    ) -> Model:

        widget_row = self.widget_center_column(tslist=tslist, selected=selected)
        plot_row = self.plot_center_column(tslist=tslist, selected=selected)

        return column(widget_row, plot_row, sizing_mode="scale_width")

    # click events
    def on_left_plus(self, tslist: List[TimeStep], selected: TimeStep):
        print("left +")
        self.left_model = self.left_column(tslist=tslist, selected=selected)

    def on_right_plus(self, tslist: List[TimeStep], selected: TimeStep):
        print("right +")
        self.right_model = self.right_column(tslist=tslist, selected=selected)

    def on_left_minus(self, tslist: List[TimeStep], selected: TimeStep):
        print("left -")
        self.left_model = self.empty_left_column(tslist=tslist, selected=selected)

    def on_right_minus(self, tslist: List[TimeStep], selected: TimeStep):
        print("right -")
        self.right_model = self.empty_right_column(tslist=tslist, selected=selected)

    def on_left_radio_timestep_click(self, radio_button_index, *, tslist):
        selected = tslist[radio_button_index]
        print(f"Left RadioButton selected {selected}")
        plot_row = self.plot_left_column(tslist=tslist, selected=selected)

        # setting second children in center model and replacing it
        self.left_model.children[1] = plot_row

    def on_right_radio_timestep_click(self, radio_button_index, *, tslist):
        selected = tslist[radio_button_index]
        print(f"Center RadioButton selected {selected}")
        plot_row = self.plot_right_column(tslist=tslist, selected=selected)

        # setting second children in center model and replacing it
        self.right_model.children[1] = plot_row

    def on_center_radio_timestep_click(self, radio_button_index, *, tslist):
        selected = tslist[radio_button_index]
        print(f"Center RadioButton selected {selected}")
        plot_row = self.plot_center_column(tslist=tslist, selected=selected)

        # setting second children in center model and replacing it
        self.center_model.children[1] = plot_row

    def __init__(
        self, document: Document, ohlcv: OHLCView, trades: Optional[TradesView] = None
    ):

        self.document = document
        self.ohlcv = ohlcv
        self.trades = trades

        # When this is created, we do not have any plots
        self.plots = {}

        # TODO : select existing timestep in ohlcv, if any...
        if len(ohlcv.keys()) <= 1:
            self.center_model = self.center_column()
        elif len(ohlcv.keys()) == 2:
            self.center_model = self.center_column()
            self.left_model = self.left_column()
        else:  # >= 3
            self.center_model = self.center_column()  # just pick the first in key list
            self.right_model = self.right_column()
            self.left_model = self.left_column()


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta, timezone
    from typing import Dict, List

    from bokeh.server.server import Server

    async def symbolapp(symbol: str = "BTCEUR"):

        # default_timeframe: TimeStep = TimeStep(
        #     timedelta(minutes=1)
        # )  # candle width, ie. timeframe precision
        # num_candles: int = 120  # number of candles of data we want to retrieve

        # setup empty data proxy for symbol
        dataview: OHLCView = OHLCView(symbol=symbol)
        # tradeview: TradesView = TradesView()  # TODO

        # display data there
        docs: List[Document] = []
        screens: List[TripleScreen] = []

        print(f"Starting data update loop for {symbol}...", end="")
        # retrieving data in background (once, then will loop forever)
        await dataview.loop()
        print(" OK.")

        def appfun(doc: Document):
            nonlocal dataview

            # Building OHLCLayout  (for this symbol) and storing it
            # Note: models must be owned by a single document
            TS = TripleScreen(document=doc, ohlcv=dataview)
            screens.append(TS)

            # storing doc
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
