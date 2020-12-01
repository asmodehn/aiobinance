# Note : no cassette needed if we dont need to retrieve OHLC data(only required with html...)
import tempfile

import pytest
from click.testing import CliRunner

from aiobinance.cli.extras import extras


@pytest.mark.vcr
def test_hummingbot():
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

    cmd = f"hummingbot {fp.name}"
    runner = CliRunner()
    result = runner.invoke(extras, cmd.split(), input="2")

    if result.exit_code == 0:
        assert (
            "|    | time                             | symbol   |     id |    price |   qty |   quote_qty |   commission | commission_asset   | is_buyer   | is_maker   | order_id   | order_list_id   | is_best_match   |"
            in result.output
        )
        assert (
            "|  0 | 2020-08-27 10:32:20.551000+00:00 | COTIBNB  | 299167 | 0.003219 |   300 |      0.9657 |    0.0009657 | BNB                | True       | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  1 | 2020-08-27 10:57:44.613000+00:00 | COTIBNB  | 299229 | 0.003261 |   300 |      0.9783 |    0.0009783 | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  2 | 2020-08-27 11:07:34.594000+00:00 | COTIBNB  | 299244 | 0.003289 |   300 |      0.9867 |    0.0009867 | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
        assert (
            "|  3 | 2020-08-27 11:07:34.743000+00:00 | COTIBNB  | 299246 | 0.00329  |   300 |      0.987  |    0.000987  | BNB                | False      | True       |            |                 |                 |"
            in result.output
        )
    else:
        print(f"CMD: {cmd}")
        raise result.exception


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
