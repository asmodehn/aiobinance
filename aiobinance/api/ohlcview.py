from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import hypothesis.strategies as st

from aiobinance.api.model.ohlcframe import OHLCFrame
from aiobinance.api.model.pricecandle import PriceCandle
from aiobinance.api.model.trade import Trade
from aiobinance.api.pure.ohlcviewbase import OHLCViewBase
from aiobinance.api.rawapi import Binance


@dataclass(frozen=False)
class OHLCView(OHLCViewBase):
    """ An updateable candles list """

    api: Binance = field(init=True, default=Binance())
    symbol: Optional[str] = field(init=True, default=None)

    @staticmethod
    def strategy(max_size=5):
        return st.builds(
            OHLCView,
            api=st.none(),
            symbol=st.text(max_size=5),
            frame=OHLCFrame.strategy(max_size=max_size),
        )

    async def __call__(
        self,
        start_time: datetime = None,
        stop_time: datetime = None,
        interval=None,
        **kwargs
    ):
        """ this retrieves recent trades"""
        if start_time is not None:
            # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
            assert start_time.tzinfo is not None
            start_timestamp = int(start_time.timestamp() * 1000)
        else:
            start_timestamp = None
        if stop_time is not None:
            assert stop_time.tzinfo is not None
            stop_timestamp = int(stop_time.timestamp() * 1000)
        else:
            stop_timestamp = None

        interval = (
            interval
            if interval is not None
            else self.api.interval(start_timestamp, stop_timestamp)
        )

        res = self.api.call_api(
            command="klines",
            symbol=self.symbol,
            interval=interval,
            startTime=start_timestamp,
            endTime=stop_timestamp,
            limit=1000,
        )

        if res.is_ok():
            res = res.value

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        candles = [
            PriceCandle(
                open_time=r[0],
                open=r[1],
                high=r[2],
                low=r[3],
                close=r[4],
                volume=r[5],
                close_time=r[6],
                qav=r[7],
                num_trades=r[8],
                taker_base_vol=r[9],
                taker_quote_vol=r[10],
                is_best_match=r[11],
            )
            for r in res
        ]

        frame = OHLCFrame.from_candleslist(*candles)

        # We aggregate all formatted ohlcframes into this OHLCView
        super(OHLCView, self).__call__(frame=self.frame + frame)

        # and return self
        return self


if __name__ == "__main__":
    import asyncio

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())
    tv = OHLCView(api=api, symbol="COTIBNB")

    print(tv)

    async def update():
        # Just because I have data there, put in your own symbol & timeinterval to test
        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        end_time = start_time + timedelta(days=1)

        await tv(start_time=start_time, stop_time=end_time)

    asyncio.run(update())
    print(tv)
