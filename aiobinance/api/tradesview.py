from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import hypothesis.strategies as st

from aiobinance.api.model.trade import Trade
from aiobinance.api.pure.tradesviewbase import TradeFrame, TradesViewBase
from aiobinance.api.rawapi import Binance


@dataclass(frozen=False)
class TradesView(TradesViewBase):
    """ An updateable trades list """

    api: Binance = field(init=True, default=Binance())

    @staticmethod
    def strategy(max_size=5):
        return st.builds(
            TradesView,
            api=st.none(),
            symbol=st.text(max_size=5),
            frame=TradeFrame.strategy(max_size=max_size),
        )

    async def __call__(
        self,
        symbol: str = None,
        start_time: datetime = None,
        stop_time: datetime = None,
        **kwargs
    ):
        """ this retrieves recent trades"""

        reqparams = {}

        if start_time is not None:
            # to make sure the timezone is set at this stage (otherwise timestamps will be ambiguous)
            assert start_time.tzinfo is not None
            start_timestamp = int(start_time.timestamp() * 1000)
            reqparams.update({"startTime": start_timestamp})

        if stop_time is not None:
            assert stop_time.tzinfo is not None
            stop_timestamp = int(stop_time.timestamp() * 1000)
            reqparams.update({"endTime": stop_timestamp})

        if symbol is None:
            symbol = self.market

        if (
            symbol is None
        ):  # we want all symbols, but this is not implemented in binance API ?
            raise NotImplementedError
        else:
            # It seems symbol is mandatory in the request params
            reqparams.update({"symbol": symbol})

        reqparams.update({"limit": 1000})

        res = self.api.call_api(command="myTrades", **reqparams)

        if res.is_ok():
            res = res.value
        else:
            raise res.err()  # TODO : a better way ?

        # Binance translation is only a matter of binance json -> python data structure && avoid data duplication.
        # We do not want to change the semantics of the exchange exposed models here.
        trades = [
            Trade(
                time_utc=r["time"],
                symbol=r["symbol"],
                id=r["id"],
                order_id=r["orderId"],
                order_list_id=r["orderListId"],
                price=r["price"],
                qty=r["qty"],
                quote_qty=r["quoteQty"],
                commission=r["commission"],
                commission_asset=r["commissionAsset"],
                is_buyer=r["isBuyer"],
                is_maker=r["isMaker"],
                is_best_match=r["isBestMatch"],
            )
            for r in res
        ]
        # TODO: probably better idea to store data in frame, before converting (but still verifying data type somehow...)
        frame = TradeFrame.from_tradeslist(*trades)
        # We let baseclasse aggregate tradeframes
        return super(TradesView, self).__call__(frame=frame)


if __name__ == "__main__":
    import asyncio

    from aiobinance.config import load_api_keyfile

    api = Binance(credentials=load_api_keyfile())
    tv = TradesView(api=api)

    print(tv)

    async def update():
        # Just because I have data there, put in your own symbol & timeinterval to test
        start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
        end_time = start_time + timedelta(days=1)

        await tv(symbol="COTIBNB", start_time=start_time, stop_time=end_time)

    asyncio.run(update())
    print(tv)
