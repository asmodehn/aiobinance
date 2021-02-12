import functools
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from bokeh.document import Document
from bokeh.layouts import column, row
from bokeh.model import Model
from bokeh.models import Button, Column, RadioButtonGroup, Row
from bokeh.plotting import Figure

from aiobinance.api.model.timeinterval import TimeIntervalDelta, TimeStep
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.tradesview import TradesView
from aiobinance.web.layouts.plots.ohlcstep import OHLCStepPlots
from aiobinance.web.layouts.singlescreen import SingleScreen


@dataclass
class LeftScreen(SingleScreen):

    activated: bool = field(default=False)

    @functools.cached_property
    def add_button(self) -> Button:
        return Button(label="+", width_policy="min")

    @functools.cached_property
    def minus_button(self) -> Button:
        return Button(label="-", width_policy="min")

    @functools.cached_property
    def timestep_radio(self) -> RadioButtonGroup:
        return RadioButtonGroup(labels=[])

    @functools.cached_property
    def widgets(self) -> Row:

        self.timestep_radio.labels = [str(ts) for ts in self.tslist]
        self.timestep_radio.active = self.tslist.index(self.selected)
        self.timestep_radio.visible = self.activated
        self.timestep_radio.on_click(
            functools.partial(self.on_center_radio_timestep_click, tslist=self.tslist)
        )

        self.add_button.visible = not self.activated
        self.add_button.on_click(self.on_plus)

        self.minus_button.visible = self.activated
        self.minus_button.on_click(self.on_minus)

        return row(
            self.add_button,
            self.minus_button,
            self.timestep_radio,
            sizing_mode="scale_width",
        )

    @property
    def ohlcfig(self) -> Figure:
        if self.selected not in self.plots:
            # create it
            self.plots[self.selected] = OHLCStepPlots(
                document=self.document,
                ohlcv=self.ohlcv,
                selected_tf=self.selected,
            )
            self.plots[self.selected].fig.visible = self.activated
            self.plots[self.selected].fig.disabled = not self.activated

        return self.plots[self.selected].fig

    # def __init__(
    #         self,
    #         document: Document,
    #         ohlcv: OHLCView,
    #         trades: Optional[TradesView] = None,
    #         tslist: Optional[List[TimeStep]] = None,
    #         selected: Optional[TimeStep] = None,
    #         activated: bool = False,
    #         side: str = "left",
    # ):
    #     self.activated = activated
    #     self.side = side
    #     super(LeftScreen, self).__init__(document=document, ohlcv=ohlcv, trades=trades, tslist=tslist, selected=selected)

    # click events
    def on_plus(self):
        print("on_plus")
        self.activated = True
        self.plots[self.selected].fig.visible = True
        self.plots[self.selected].fig.disabled = False
        self.add_button.visible = False
        self.add_button.disabled = True
        self.minus_button.visible = True
        self.minus_button.disabled = False
        self.timestep_radio.visible = True
        self.timestep_radio.disabled = False

    def on_minus(self):
        print("on_minus")
        self.activated = False
        self.plots[self.selected].fig.visible = False
        self.plots[self.selected].fig.disabled = True
        self.add_button.visible = True
        self.add_button.disabled = False
        self.minus_button.visible = False
        self.minus_button.disabled = True
        self.timestep_radio.visible = False
        self.timestep_radio.disabled = True


@dataclass
class RightScreen(LeftScreen):
    @functools.cached_property  # it is different, and not linked to the LeftScreen one
    def timestep_radio(self) -> RadioButtonGroup:
        return RadioButtonGroup(labels=[])

    @functools.cached_property
    def widgets(self) -> Row:

        self.timestep_radio.labels = [str(ts) for ts in self.tslist]
        self.timestep_radio.active = self.tslist.index(self.selected)
        self.timestep_radio.visible = self.activated
        self.timestep_radio.on_click(
            functools.partial(self.on_center_radio_timestep_click, tslist=self.tslist)
        )

        self.add_button.visible = not self.activated
        self.add_button.on_click(self.on_plus)

        self.minus_button.visible = self.activated
        self.minus_button.on_click(self.on_minus)

        return row(
            self.timestep_radio,
            self.minus_button,
            self.add_button,
            sizing_mode="scale_width",
        )


@dataclass
class TripleScreen:

    document: Document
    ohlcv: OHLCView
    trades: Optional[TradesView] = field(default=None)

    # relevant graphical component for each timestep
    plots: Dict[TimeStep, OHLCStepPlots] = field(default_factory=dict)

    # Properties based layout...
    # TODO : maybe some hierarchy of classes to get the same composability effect for seamless updates ??
    @functools.cached_property
    def model(self) -> Model:
        return column(
            row(
                self.left_screen.model,
                self.center_screen.model,
                self.right_screen.model,
                sizing_mode="scale_width",
            )
        )

    # @model.setter
    # def model(self, newmodel: Model):
    #     self._model = newmodel  # this modifies the cache
    #     # TODO: maybe we need to have a "container" concept to trigger update ourselves inside it ?

    @functools.cached_property
    def left_screen(self) -> LeftScreen:
        return LeftScreen(
            ohlcv=self.ohlcv,
            document=self.document,
            # plots=self.plots,  # sharing plots for efficiency (BUT breaking itneraction !)
            activated=False,
        )

    # @left_screen.setter
    # def left_screen(self, newmodel: SingleScreen):
    #     self._left_screen = newmodel
    #     self.model.children[0] = self._left_screen.model

    @functools.cached_property
    def center_screen(self):
        return SingleScreen(
            ohlcv=self.ohlcv,
            document=self.document,
            # plots=self.plots,  # sharing plots for efficiency (BUT breaking itneraction !)
        )

    # @center_screen.setter
    # def center_screen(self, newmodel: SingleScreen):
    #     self._center_screen = newmodel  # this modifies the cache
    #     self.model.children[1] = self._center_screen.model

    @functools.cached_property
    def right_screen(self):
        return RightScreen(
            ohlcv=self.ohlcv,
            document=self.document,
            # plots=self.plots,  # sharing plots for efficiency (BUT breaking itneraction !)
            activated=False,
        )

    # @right_screen.setter
    # def right_screen(self, newmodel: SingleScreen):
    #     self._right_screen = newmodel  # this modifies the cache
    #     self.model.children[2] = self._right_screen.model


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta, timezone

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
