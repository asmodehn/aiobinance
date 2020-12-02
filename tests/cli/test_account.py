import os
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner
from hypothesis import given

from aiobinance.cli.account import cli


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_balance(keyfile):

    """ testing balance command with --keyfile or from cassettes """
    runner = CliRunner()

    # passing keyfile so the results do not depend on environment (arguably too complex with 2 levels of envs)
    # but on how pytest is called to run the tests. We're testing the --apikey and --secret options at the same time.
    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} balance"
    result = runner.invoke(
        cli,
        cmd.split(),
        input="2",
    )

    if result.exit_code == 0:
        assert "accountType: SPOT" in result.output
        assert "canTrade: True" in result.output
        assert "canWithdraw: True" in result.output
        assert "canDeposit: True" in result.output

        assert "balances:" in result.output
        assert " - 0.02084500 ETH (free: 0.02084500, locked: 0E-8)" in result.output
        assert " - 12.83529493 BNB (free: 12.83529493, locked: 0E-8)" in result.output
        assert " - 86.40000000 XRP (free: 86.40000000, locked: 0E-8)" in result.output
        assert " - 208.93330180 EUR (free: 208.93330180, locked: 0E-8)" in result.output
        assert (
            " - 416.00000000 COTI (free: 416.00000000, locked: 0E-8)" in result.output
        )
        assert " - 0.94611754 SXP (free: 0.94611754, locked: 0E-8)" in result.output

        assert "updateTime: 2020-11-02 20:15:07.791000+00:00" in result.output
        assert "permissions: ['SPOT']" in result.output
        assert "makerCommission: 10" in result.output
        assert "takerCommission: 10" in result.output
    else:
        print(f"CMD: {cmd}")
        raise result.exception


@pytest.mark.vcr(
    filter_headers=["X-MBX-APIKEY"], filter_query_parameters=["timestamp", "signature"]
)
def test_trades(keyfile):
    """ testing trades command with --keyfile or from cassettes """

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    cmd = f"--apikey {keyfile.key} --secret {keyfile.secret} trades COTIBNB --from {start_time.strftime('%Y-%m-%d')} --to {end_time.strftime('%Y-%m-%d')} --utc"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        cmd.split(),
        input="2",
    )

    if result.exit_code == 0:
        assert (
            "|    | time                             | symbol   |     id |    price |   qty |   quote_qty |   commission | commission_asset   | is_buyer   | is_maker   |   order_id |   order_list_id | is_best_match   |"
            in result.output
        )
        assert (
            "|  0 | 2020-08-27 10:32:20.409000+00:00 | COTIBNB  | 299167 | 0.003219 |   300 |    0.9657   |   0.00065495 | BNB                | True       | True       |   18441464 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  1 | 2020-08-27 10:57:44.478000+00:00 | COTIBNB  | 299229 | 0.003261 |   300 |    0.9783   |   0.00066035 | BNB                | False      | True       |   18443055 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  2 | 2020-08-27 11:07:34.459000+00:00 | COTIBNB  | 299244 | 0.003289 |   300 |    0.9867   |   0.00066602 | BNB                | False      | True       |   18446230 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  3 | 2020-08-27 11:07:34.459000+00:00 | COTIBNB  | 299246 | 0.00329  |   300 |    0.987    |   0.00066622 | BNB                | False      | True       |   18441463 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  4 | 2020-08-27 11:23:34.060000+00:00 | COTIBNB  | 299456 | 0.003285 |   300 |    0.9855   |   0.00068733 | BNB                | True       | True       |   18448574 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  5 | 2020-08-27 11:37:23.670000+00:00 | COTIBNB  | 299815 | 0.003245 |   300 |    0.9735   |   0.00065593 | BNB                | True       | True       |   18454107 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  6 | 2020-08-27 13:41:13.140000+00:00 | COTIBNB  | 300255 | 0.003209 |    61 |    0.195749 |   0.0001322  | BNB                | True       | True       |   18478551 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  7 | 2020-08-27 13:41:22.243000+00:00 | COTIBNB  | 300256 | 0.003209 |    97 |    0.311273 |   0.00021023 | BNB                | True       | True       |   18478551 |              -1 | True            |"
            in result.output
        )
        assert (
            "|  8 | 2020-08-27 17:06:47.354000+00:00 | COTIBNB  | 300607 | 0.003125 |   300 |    0.9375   |   0.00063539 | BNB                | True       | True       |   18506959 |              -1 | True            |"
            in result.output
        )
    else:
        print(f"CMD: {cmd}")
        raise result.exception


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
