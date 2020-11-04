import unittest

import pytest
from click.testing import CliRunner

from aiobinance.__main__ import cli


class TestAIOBinanceCLI(unittest.TestCase):

    def test_auth(self):

        runner = CliRunner()
        result = runner.invoke(
            cli, 'auth'.split(), input='2')
        self.assertEqual(0, result.exit_code)
        self.assertIn('apikey: ', result.output)

    def test_auth_verbose(self):

        runner = CliRunner()
        result = runner.invoke(
            cli, 'auth --verbose'.split(), input='2')
        self.assertEqual(0, result.exit_code)

        from aiobinance.config import BINANCE_API_KEYFILE
        self.assertIn(f'{BINANCE_API_KEYFILE}', result.output)
        self.assertIn('apikey: ', result.output)


if __name__ == "__main__":
    pytest.main(['-s', __file__])
