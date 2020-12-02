import os
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner
from hypothesis import given

from aiobinance.cli.cli_group import cli
from aiobinance.config import BINANCE_API_KEYFILE, credentials_strategy

""" cli group is tested with user environment, as it is the main command modifying it.

Other commands will use recorded cassettes, and fake requests with a fake apikey

"""


def test_cli_expected():
    """ testing authentication via cli group depending on user's environment """
    runner = CliRunner()
    # Result and output depends on the environment of the user running the tests
    if os.path.exists(BINANCE_API_KEYFILE):
        result = runner.invoke(cli, "".split(), input="2")
        assert (
            "apikey: " in result.output
        )  # we cannot know the api key without depending on user system
    else:
        result = runner.invoke(
            cli, "--apikey My4P1K3y --secret T3sTS3cr3T".split(), input="2"
        )
        assert "apikey: My4P1K3y" in result.output
    assert result.exit_code == 0


def test_cli_pathological():
    """  testing authentication via cli group depending on user's environment """
    runner = CliRunner()
    # Result and output depends on the environment of the user running the tests
    if os.path.exists(BINANCE_API_KEYFILE):
        result = runner.invoke(
            cli, "--apikey My4P1K3y --secret T3sTS3cr3T".split(), input="2"
        )
        assert (
            "apikey: My4P1K3y" in result.output
        )  # verify we override stored credentials
        assert result.exit_code == 0
    else:
        result = runner.invoke(cli, "".split(), input="2")
        assert result.exit_code == 1
        assert f"{BINANCE_API_KEYFILE} Not Found !" in result.output


# TODO : test --store !!!

if __name__ == "__main__":
    pytest.main(["-s", __file__, "--block-network"])
