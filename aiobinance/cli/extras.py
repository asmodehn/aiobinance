import asyncio

import click

import aiobinance.binance as binance
import aiobinance.hummingbot as hummingbot
from aiobinance.api.ohlcview import OHLCView
from aiobinance.api.rawapi import Binance
from aiobinance.cli.cli_group import cli


@cli.command(
    name="hummingbot"
)  # TODO : move this to and "external" group and later into some kind of plugin...
@click.argument("filename", type=click.Path(exists=True), required=True)
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def hummingbot_instance(ctx, filename, html=False):
    """provide a report of hummingbot trades"""

    trades = hummingbot.trades_from_csv(click.format_filename(filename))

    symbol = trades.symbol

    api = Binance()

    ohlcv = OHLCView(api=api, symbol=symbol)

    first_trade = trades[trades.id[0]]
    last_trade = trades[trades.id[-1]]

    asyncio.run(
        ohlcv.request(
            start_time=first_trade.time_utc,
            stop_time=last_trade.time_utc,
        )
    )

    if html:
        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        report = aiobinance.web.trades_layout(ohlcv=ohlcv, trades=trades)
        output_file(f"{filename}_report.html")
        show(report)

    print(trades)


if __name__ == "__main__":
    # testing only this cli command
    cli()
