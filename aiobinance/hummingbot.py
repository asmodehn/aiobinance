import pandas as pd
from pandas.io import json

from aiobinance.api.model.tradeframe import Trade, TradeFrame


# TODO: maybe this should be less generic : hummingbot_csv
def trades_from_csv(csv_filepath: str) -> TradeFrame:
    """ This is the format used by hummingbot when outputting trades in csv... """

    # Using pandas csv reader as it is simplest.
    csv_df = pd.read_csv(
        csv_filepath,
        usecols=[
            "Timestamp",
            "Market",
            "Base",
            "Quote",
            "Trade",
            "Type",
            "Price",
            "Amount",
            "Fee",
            "Age",
            "Order ID",
            "Exchange Trade ID",
        ],
    )

    # To access attributes of rows later on, we remove spaces
    csv_df.rename(columns={c: c.replace(" ", "") for c in csv_df.columns}, inplace=True)
    csv_df.Fee = csv_df.Fee.apply(lambda s: json.loads(s.replace("'", '"')))

    # DDD : Translation layer...
    trades = [
        Trade(
            time_utc=r.Timestamp
            * 1e-3,  # change to float to have this identify as [s] with [ms] precision for python datetime
            symbol=r.Market,
            id=r.ExchangeTradeID,
            # order_id=r.OrderID,  # Order IDs are not compatible for some reason...
            price=r.Price,
            qty=r.Amount,
            quote_qty=r.Amount
            * r.Price,  # TODO : is there duplication in our data model??
            commission=r.Fee["percent"] * r.Amount * r.Price,
            commission_asset=r.Quote,
            is_buyer=r.Trade == "BUY",
            is_maker=r.Type == "LIMIT_MAKER",
        )
        for r in csv_df.itertuples()
    ]

    return TradeFrame.from_tradeslist(*trades)
