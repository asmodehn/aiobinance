import functools
from asyncio import QueueEmpty
from dataclasses import dataclass, field
from functools import cache, cached_property, partial
from typing import Dict, List, Optional

from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.model import Model
from bokeh.models import Button, Column, RadioButtonGroup, Row
from bokeh.plotting import Figure

from aiobinance.api.model.timeinterval import TimeInterval, TimeIntervalDelta, TimeStep
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.tradesview import TradesView
from aiobinance.web.layouts.plots.ohlcstep import OHLCStepPlots


@dataclass
class SingleScreen:

    document: Document
    ohlcv: OHLCView
    trades: Optional[TradesView] = field(default=None)

    # relevant graphical component for each timestep
    plots: Dict[TimeStep, OHLCStepPlots] = field(default_factory=dict)

    tslist: Optional[List[TimeStep]] = field(
        default_factory=lambda: list(
            TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)
        )
    )
    _selected: Optional[TimeStep] = field(default=TimeStep(TimeIntervalDelta.minutely))

    # # cache and modifiable content
    # _model: Optional[Model] = None
    # _widgets: Optional[Row] = None
    # _plot: Optional[Row] = None
    # _ohlc: Optional[Figure] = None

    # Lens based layout...
    # TODO : maybe some hierarchy of classes to get the same composability effect for seamless updates ??
    @functools.cached_property  # a cache, hidden behind a property accessor
    def model(self) -> Model:
        return column(self.widgets, self.ohlcplot, sizing_mode="scale_width")

    # @model.setter
    # def model(self, newmodel: Model):
    #     self._model = newmodel  # this modifies the cache
    #     # TODO: maybe we need to have a "container" concept to trigger update ourselves inside it ?

    @functools.cached_property
    def widgets(self) -> Row:

        lprb = RadioButtonGroup(
            labels=[str(ts) for ts in self.tslist],
            active=self.tslist.index(self.selected),
        )
        lprb.on_click(partial(self.on_center_radio_timestep_click, tslist=self.tslist))

        # Note : we need to scale the row like the button to avoid overlapping buttons...
        return row(lprb, sizing_mode="scale_width")

    #
    # @widgets.setter
    # def widgets(self, newrow: Row):
    #     self._widgets = newrow
    #     self.model.children[0] = self._widgets

    # @functools.cached_property
    @property  # TMP cache not working
    def ohlcplot(self) -> Row:
        return row(self.ohlcfig, sizing_mode="scale_width")

    # @ohlcplot.setter
    # def ohlcplot(self, newrow: Row):
    #     self._plot = newrow
    #     self.model.children[1] = self._plot

    @property
    def ohlcfig(self) -> Figure:
        if self.selected not in self.plots:
            # create it
            self.plots[self.selected] = OHLCStepPlots(
                document=self.document, ohlcv=self.ohlcv, selected_tf=self.selected
            )

        return self.plots[self.selected].fig

    # This is not settable, it is managed by OHLCStepPlots

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value  # changing selection

        tmpplot = self.ohlcplot  # from property TMP (since not in cache...)
        tmpplot.children[0] = self.ohlcfig  # updating show figure
        # TMP : just because ohlcplot is not in cache ??? TODO : FIX BUG...
        self.model.children[1] = tmpplot

    # click events
    def on_center_radio_timestep_click(self, radio_button_index, *, tslist):
        # this alone should trigger update
        self.selected = tslist[radio_button_index]
        print(f"RadioButton selected {self.selected}")

    #
    # def __init__(
    #     self,
    #     document: Document,
    #     ohlcv: OHLCView,
    #     trades: Optional[TradesView] = None,
    #     tslist: Optional[List[TimeStep]] = None,
    #     selected: Optional[TimeStep] = None,
    # ):
    #
    #     self.document = document
    #     self.ohlcv = ohlcv
    #     self.trades = trades
    #
    #     self.tslist = (
    #         [TimeStep(step=ti) for ti in reversed(TimeIntervalDelta)]
    #         if tslist is None
    #         else tslist
    #     )
    #     self._selected = max(self.tslist) if selected is None else selected
    #
    #     # When this is created, we do not have any plots
    #     self.plots = {}


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
        screens: List[SingleScreen] = []

        print(f"Starting data update loop for {symbol}...", end="")
        # retrieving data in background (once, then will loop forever)
        await dataview.loop()
        print(" OK.")

        def appfun(doc: Document):
            nonlocal dataview

            # Building OHLCLayout  (for this symbol) and storing it
            # Note: models must be owned by a single document
            TS = SingleScreen(document=doc, ohlcv=dataview)
            screens.append(TS)

            doc.add_root(TS.model)  # note : this will create the layout dynamically
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
