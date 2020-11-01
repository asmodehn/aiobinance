import pandas as pd
from .model.trades import Trades
from .model.ohlcv import OHLCV


def trades_from_csv(csv_filepath: str) -> Trades:
    """ This is the format used by hummingbot when outputting trades in csv... """
    trades_df = pd.read_csv(csv_filepath,
                     usecols=[
        "Timestamp",
        "Base",
        "Quote",
        "Trade",
        "Type",
        "Price",
        "Amount",
        "Fee",
        "Age",
        "Order ID"
    ])
    return Trades(trades_df)


def ohlcv_from_csv() -> OHLCV:
    raise NotImplementedError
    return OHLCV()


def trades_to_csv(trades: Trades):
    raise NotImplementedError
    pass


def ohlcv_to_csv(ohlcv: OHLCV):
    raise NotImplementedError
    pass
