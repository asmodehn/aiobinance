import unittest
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import click
from hypothesis import given

from aiobinance.cli.params.date import Date


class TestDate(unittest.TestCase):
    def test_get_metavar_default(self):
        d = Date()
        dummy_opt = click.Option(param_decls=["--somedate"])
        assert (
            d.get_metavar(param=dummy_opt)
            == "[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%dT%H:%M:%S%z]"
        )

    def test_get_metavar_custom(self):
        d = Date(
            formats=["%Y", "%m", "%d"]
        )  # do we need to verify proper/wrong formats here ?
        dummy_opt = click.Option(param_decls=["--somedate"])
        assert d.get_metavar(param=dummy_opt) == "[%Y|%m|%d]"

    def test_convert(self):
        d = Date()
        dummy_ctx = click.Context(command=click.Command("dummy_cmd"))
        dummy_opt = click.Option(param_decls=["--somedate"])
        assert d.convert("2020-08-08", param=dummy_opt, ctx=dummy_ctx) == date(
            year=2020, month=8, day=8
        )
        assert d.convert(
            "2020-08-08T01:01:01", param=dummy_opt, ctx=dummy_ctx
        ) == datetime(year=2020, month=8, day=8, hour=1, minute=1, second=1)

        # defining CET timezone as per instructions in https://docs.python.org/3/library/datetime.html#datetime.tzinfo
        cet = timezone(timedelta(hours=1), name="CET")
        assert d.convert(
            "2020-08-08T01:01:01+01:00", param=dummy_opt, ctx=dummy_ctx
        ) == datetime(year=2020, month=8, day=8, hour=1, minute=1, second=1, tzinfo=cet)
        assert d.convert(
            "2020-08-08T01:01:01+00:00", param=dummy_opt, ctx=dummy_ctx
        ) == datetime(
            year=2020, month=8, day=8, hour=1, minute=1, second=1, tzinfo=timezone.utc
        )
