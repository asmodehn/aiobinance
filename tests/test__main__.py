import os
import unittest

import pytest
from click.testing import CliRunner

from aiobinance.__main__ import cli
from aiobinance.config import BINANCE_API_KEYFILE


class TestAIOBinanceCLI(unittest.TestCase):
    def test_auth(self):

        runner = CliRunner()
        result = runner.invoke(cli, "auth".split(), input="2")
        if os.path.exists(BINANCE_API_KEYFILE):
            self.assertEqual(0, result.exit_code)
            self.assertIn("apikey: ", result.output)
        else:
            self.assertEqual(1, result.exit_code)
            self.assertIn(f"{BINANCE_API_KEYFILE} Not Found !", result.output)

    def test_auth_verbose(self):

        runner = CliRunner()
        result = runner.invoke(cli, "auth --verbose".split(), input="2")

        if os.path.exists(BINANCE_API_KEYFILE):
            self.assertEqual(0, result.exit_code)
            self.assertIn(f"{BINANCE_API_KEYFILE}", result.output)
            self.assertIn("apikey: ", result.output)
        else:
            self.assertEqual(1, result.exit_code)
            self.assertIn(f"{BINANCE_API_KEYFILE} Not Found !", result.output)

    def test_balance(self):

        runner = CliRunner()
        result = runner.invoke(cli, "balance".split(), input="2")

        if os.path.exists(BINANCE_API_KEYFILE):
            self.assertEqual(0, result.exit_code)
            self.assertIn("accountType:", result.output)
            self.assertIn("canTrade:", result.output)
            self.assertIn("canWithdraw:", result.output)
            self.assertIn("canDeposit:", result.output)
            self.assertIn("balances:", result.output)
            # Are there any constraints on balance that we can test ?
            self.assertIn("updateTime:", result.output)
            self.assertIn("permissions:", result.output)
            self.assertIn("makerCommission:", result.output)
            self.assertIn("takerCommission:", result.output)

        else:
            self.assertEqual(1, result.exit_code)
            self.assertIn(f"{BINANCE_API_KEYFILE} Not Found !", result.output)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
