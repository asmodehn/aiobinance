from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import hypothesis.strategies as st
from hypothesis.strategies import SearchStrategy
from pydantic.dataclasses import dataclass

from aiobinance.api.pure.filters import Filter
from aiobinance.api.pure.order import LimitOrder, MarketOrder, OrderSide


@dataclass
class PureMarket:
    """this is the pure part of a market.
    No side effect => test can be run automatically against this class.
    """

    # TODO   a lot of str can be changed to enum and properly type checked.
    symbol: str
    status: str
    base_asset: str
    base_asset_precision: int
    quote_asset: str
    quote_precision: int
    quote_asset_precision: int

    base_commission_precision: int
    quote_commission_precision: int

    order_types: List[str]

    iceberg_allowed: bool
    oco_allowed: bool
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    quote_order_qty_market_allowed: bool

    filters: List[Filter]

    permissions: List[str]

    @classmethod
    def strategy(cls) -> SearchStrategy:
        return st.builds(
            cls,
            #       "symbol": "ETHBTC",
            symbol=st.text(
                alphabet=st.characters(whitelist_categories=["Lu"]),
                min_size=2,
                max_size=8,
            ),
            #       "status": "TRADING",
            status=st.sampled_from(["TRADING"]),  # TODO: add other statuses
            #       "baseAsset": "ETH",
            base_asset=st.text(
                alphabet=st.characters(whitelist_categories=["Lu"]),
                min_size=1,
                max_size=4,
            ),
            #       "baseAssetPrecision": 8,
            base_asset_precision=st.integers(min_value=0, max_value=16),
            #       "quoteAsset": "BTC",
            quote_asset=st.text(
                alphabet=st.characters(whitelist_categories=["Lu"]),
                min_size=1,
                max_size=4,
            ),
            #       "quotePrecision": 8,
            quote_precision=st.integers(min_value=0, max_value=16),
            # Note : this will be dropped soon, replaced by quote_asset_precision
            #       "quoteAssetPrecision": 8,
            quote_asset_precision=st.integers(min_value=0, max_value=16),
            base_commission_precision=st.integers(min_value=0, max_value=16),
            quote_commission_precision=st.integers(min_value=0, max_value=16),
            #       "orderTypes": [
            #         "LIMIT",
            #         "LIMIT_MAKER",
            #         "MARKET",
            #         "STOP_LOSS",
            #         "STOP_LOSS_LIMIT",
            #         "TAKE_PROFIT",
            #         "TAKE_PROFIT_LIMIT"
            #       ],
            order_types=st.lists(
                elements=st.sampled_from(
                    [
                        "LIMIT",
                        "LIMIT_MAKER",
                        "MARKET",
                        "STOP_LOSS",
                        "STOP_LOSS_LIMIT",
                        "TAKE_PROFIT",
                        "TAKE_PROFIT_LIMIT",
                    ]
                ),
                unique=True,
            ),
            #       "icebergAllowed": true,
            iceberg_allowed=st.booleans(),
            #       "ocoAllowed": true,
            oco_allowed=st.booleans(),
            #       "isSpotTradingAllowed": true,
            is_spot_trading_allowed=st.booleans(),
            #       "isMarginTradingAllowed": true,
            is_margin_trading_allowed=st.booleans(),
            quote_order_qty_market_allowed=st.booleans(),
            #       "filters": [
            #         //These are defined in the Filters section.
            #         //All filters are optional
            #       ],
            filters=st.lists(
                elements=Filter.strategy_symbol(), unique_by=lambda f: f.filter_type
            ),
            #       "permissions": [
            #          "SPOT",
            #          "MARGIN"
            #       ]
            permissions=st.lists(
                elements=st.sampled_from(["SPOT", "TRADING"]), unique=True
            ),
        )

    def market_order_base(
        self,
        *,
        side: OrderSide,
        quantity: Optional[Decimal] = None,  # Base asset
    ) -> Tuple[Dict[str, str], MarketOrder]:
        """ A market order passing without any side effect. """

        sent_params = {
            "symbol": self.symbol,
            "side": side.value,
            "type": "MARKET",
            # Ref : https://github.com/sammchardy/python-binance/issues/57#issuecomment-354062222
            "quantity": "{:0.0{}f}".format(quantity, self.base_asset_precision),
        }

        return sent_params, MarketOrder(
            symbol=sent_params["symbol"],
            side=OrderSide(sent_params["side"]),
            type=sent_params["type"],
            origQty=Decimal(sent_params["quantity"]),
            # fake attr for test order
            order_id=-1,
            order_list_id=-1,
            clientOrderId="",
            transactTime=int(datetime.now(tz=timezone.utc).timestamp() * 1000),
            executedQty=Decimal(0),
            cummulativeQuoteQty=Decimal(0),
            status="TEST",
            fills=[],
        )

    def market_order_quote(
        self,
        *,
        side: OrderSide,
        quantity: Optional[Decimal] = None,  # Quote asset
    ) -> Tuple[Dict[str, str], MarketOrder]:
        """ A market order passing without any side effect. """

        sent_params = {
            "symbol": self.symbol,
            "side": side,
            "type": "MARKET",
            # Ref : https://github.com/sammchardy/python-binance/issues/57#issuecomment-354062222
            "quoteOrderQty": "{:0.0{}f}".format(quantity, self.base_asset_precision),
        }
        raise NotImplementedError  # This needs to be reviewed and used...
        return sent_params, MarketOrder(
            symbol=sent_params["symbol"],
            side=sent_params["side"],
            type=sent_params["type"],
            # origQty=quantity,  # TODO : some calculation based on price is needed here...
            # fake attr for test order
            order_id=-1,
            order_list_id=-1,
            clientOrderId="",
            transactTime=int(datetime.now(tz=timezone.utc).timestamp() * 1000),
            executedQty=Decimal(0),
            cummulativeQuoteQty=Decimal(0),
            status="TEST",
            fills=[],
        )

    def limit_order(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        timeInForce="GTC",
        icebergQty: Optional[Decimal] = None,
    ) -> Tuple[Dict[str, str], LimitOrder]:
        """ A limit order passing without any side effect. """

        sent_params = {
            "symbol": self.symbol,
            "side": side.value,  # reconverting to enum from sent string
            "type": "LIMIT",
            "timeInForce": timeInForce,
            # Ref : https://github.com/sammchardy/python-binance/issues/57#issuecomment-354062222
            "quantity": "{:0.0{}f}".format(quantity, self.base_asset_precision),
            "price": "{:0.0{}f}".format(price, self.quote_asset_precision),
        }
        if icebergQty is not None:
            sent_params.update(
                {
                    "icebergQty": icebergQty,
                }
            )

        # filling up with order info, as it has been accepted
        return sent_params, LimitOrder(
            symbol=sent_params["symbol"],
            side=OrderSide(sent_params["side"]),
            type=sent_params["type"],
            timeInForce=sent_params["timeInForce"],
            # we recreate decimal from passed string to adjust precision...
            origQty=Decimal(sent_params["quantity"]),
            price=Decimal(sent_params["price"]),
            # fake attr for test order
            order_id=-1,
            order_list_id=-1,
            clientOrderId="",
            transactTime=int(datetime.now(tz=timezone.utc).timestamp() * 1000),
            executedQty=Decimal(0),
            cummulativeQuoteQty=Decimal(0),
            status="TEST",
            fills=[],
        )
