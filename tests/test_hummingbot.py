import tempfile

import pytest

import aiobinance.hummingbot


def test_trades_from_csv():

    # make temporary file with hummingbot csv format
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
        fp.write(
            r"""Config File,Strategy,Exchange,Timestamp,Market,Base,Quote,Trade,Type,Price,Amount,Fee,Age,Order ID,Exchange Trade ID
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598524340551,COTIBNB,COTI,BNB,BUY,LIMIT_MAKER,0.003219,300.0,"{'percent': 0.001, 'flat_fees': []}",00:08:52,x-XEKWYICX-BCIBB1598523808006812,299167
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598525864613,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.003261,300.0,"{'percent': 0.001, 'flat_fees': []}",00:20:23,x-XEKWYICX-SCIBB1598524641006675,299229
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598526454594,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.003289,300.0,"{'percent': 0.001, 'flat_fees': []}",00:04:49,x-XEKWYICX-SCIBB1598526165003515,299244
conf_pure_mm_coti_bnb_binance.yml,pure_market_making,binance,1598526454743,COTIBNB,COTI,BNB,SELL,LIMIT_MAKER,0.00329,300.0,"{'percent': 0.001, 'flat_fees': []}",00:44:06,x-XEKWYICX-SCIBB1598523808007285,299246
"""
        )
        fp.seek(0)

    trades = aiobinance.hummingbot.trades_from_csv(csv_filepath=fp.name)

    assert trades


if __name__ == "__main__":
    pytest.main(["-s", __file__])
