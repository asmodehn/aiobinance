from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from aiobinance.cli.market import cli


@pytest.mark.vcr
def test_price(keyfile):

    """ testing price command with --keyfile or from cassettes """

    start_time = datetime.fromtimestamp(1598524340551 / 1000, tz=timezone.utc)
    end_time = start_time + timedelta(days=1)

    cmd = f"price COTIBNB --from {start_time.strftime('%Y-%m-%d')} --to {end_time.strftime('%Y-%m-%d')} --interval 3m --utc"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        cmd.split(),
        input="2",
    )

    if result.exit_code == 0:
        assert (
            "| open_time           |     open |     high |      low |    close |   volume | close_time                 |        qav |   num_trades |   taker_base_vol |   taker_quote_vol |   is_best_match |"
            in result.output
        )
        assert (
            "| 2020-08-26 22:00:00 | 0.003472 | 0.003472 | 0.003468 | 0.003468 |     1962 | 2020-08-26 22:02:59.999000 |   6.8054   |            3 |                0 |          0        |               0 |"
            in result.output
        )
        # testing first and last line only...
        assert (
            "| 2020-08-27 22:00:00 | 0.003153 | 0.003153 | 0.003153 | 0.003153 |        0 | 2020-08-27 22:02:59.999000 |   0        |            0 |                0 |          0        |               0 |"
            in result.output
        )
    else:

        print(f"CMD: {cmd}")
        raise result.exception


if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
