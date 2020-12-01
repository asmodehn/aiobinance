import pytest
from click.testing import CliRunner

from aiobinance.cli.trader import trader


@pytest.mark.skip  # TMP !
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_buy_test(keyfile):

    """ testing buy command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} "
    # Buy test order overpriced => will readjust !
    cmd = cmd + "buy 300 COTI --using 0.50 BNB"
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0

    #
    # assert order and isinstance(order, LimitOrder)
    # assert order.clientOrderId == ""
    # assert order.cummulativeQuoteQty.is_zero()
    # assert order.executedQty.is_zero()
    # assert order.fills == []
    # assert order.icebergQty is None
    # assert order.order_id == -1
    # assert order.order_list_id == -1
    # assert order.origQty == Decimal("300")
    # assert order.price == Decimal(
    #     "0.00142200"
    # )  # calculated price from expectation & readjusted, at correct precision.
    # assert order.side == "BUY"
    # assert order.status == "TEST"
    # assert order.symbol == "COTIBNB"
    # assert order.timeInForce == "GTC"
    #
    # # transac time has a dynamic value because it does not depend on recorded traffic !
    # # This is measuring with second precision a time in ms
    # assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} "
    # Buy test order underpriced
    cmd = cmd + "buy 300 COTI --using 0.45 BNB"
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0

    # assert order and isinstance(order, LimitOrder)
    # assert order.clientOrderId == ""
    # assert order.cummulativeQuoteQty.is_zero()
    # assert order.executedQty.is_zero()
    # assert order.fills == []
    # assert order.icebergQty is None
    # assert order.order_id == -1
    # assert order.order_list_id == -1
    # assert order.origQty == Decimal("300")
    # assert order.price == Decimal(
    #     "0.00140000"
    # )  # calculated price from expectation, with correct precision.
    # assert order.side == "BUY"
    # assert order.status == "TEST"
    # assert order.symbol == "COTIBNB"
    # assert order.timeInForce == "GTC"
    #
    # # transac time has a dynamic value because it does not depend on recorded traffic !
    # # This is measuring with second precision a time in ms
    # assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # TODO : recording when appropriate time/price
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_buy(keyfile):

    """ testing buy command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} --confirm "
    # Buy test order overpriced => will readjust !
    cmd = cmd + "buy 300 COTI --using 0.45 BNB"
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0

    # TODO: Buy test order underpriced


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_sell_test(keyfile):

    """ testing sell command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} "

    # Sell test order overpriced
    cmd = cmd + "sell 300 COTI --receive 0.51 BNB"
    # TODO : ARGH it seems PRICE_FILTER is triggered with calculated prices like 0.00163333 WORAROUND ?
    #  Info from : https://binance-docs.github.io/apidocs/spot/en/#filters
    #  (price-minPrice) % tickSize == 0 for price filter to be happy !!
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0

    #
    # # Decimal of float here to test precision. it should be built from string instead !
    # order = trader.sell(amount=Decimal(300), total_expected=Decimal(0.45), test=True)
    # assert order and isinstance(order, LimitOrder)
    # assert order.clientOrderId == ""
    # assert order.cummulativeQuoteQty.is_zero()
    # assert order.executedQty.is_zero()
    # assert order.fills == []
    # assert order.icebergQty is None
    # assert order.order_id == -1
    # assert order.order_list_id == -1
    # assert order.origQty == Decimal("300")
    # assert order.price == Decimal(
    #     "0.00150000"
    # )  # calculated price from expectation, with correct precision.
    # assert order.side == "SELL"
    # assert order.status == "TEST"
    # assert order.symbol == "COTIBNB"
    # assert order.timeInForce == "GTC"
    #
    # # transac time has a dynamic value because it does not depend on recorded traffic !
    # # This is measuring with second precision a time in ms
    # assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} "

    # Sell test order underpriced => will readjust !
    cmd = cmd + "sell 300 COTI --receive 0.45 BNB"
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0

    # assert order and isinstance(order, LimitOrder)
    # assert order.clientOrderId == ""
    # assert order.cummulativeQuoteQty.is_zero()
    # assert order.executedQty.is_zero()
    # assert order.fills == []
    # assert order.icebergQty is None
    # assert order.order_id == -1
    # assert order.order_list_id == -1
    # assert order.origQty == Decimal("300")
    # assert order.price == Decimal(
    #     "0.00142300"
    # )  # calculated price from expectation & adjusted, with correct precision.
    # assert order.side == "SELL"
    # assert order.status == "TEST"
    # assert order.symbol == "COTIBNB"
    # assert order.timeInForce == "GTC"
    #
    # # transac time has a dynamic value because it does not depend on recorded traffic !
    # # This is measuring with second precision a time in ms
    # assert order.transactTime // 1000 == int(datetime.now(tz=timezone.utc).timestamp())


@pytest.mark.skip  # TODO: record when appropriate time/price
@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_sell(keyfile):

    """ testing sell command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} --confirm sell "
    result = runner.invoke(
        trader,
        cmd.split(),
        input="2",
    )

    assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
