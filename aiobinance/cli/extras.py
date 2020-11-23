import click

import aiobinance.binance as binance
import aiobinance.hummingbot as hummingbot


@click.group()
def extras():
    """ command group for extra stuff"""
    pass


@extras.command(
    name="hummingbot"
)  # TODO : move this to and "external" group and later into some kind of plugin...
@click.argument("filename", type=click.Path(exists=True), required=True)
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def hummingbot_instance(ctx, filename, html=False):
    """provide a report of hummingbot trades"""

    trades = hummingbot.trades_from_csv(click.format_filename(filename))

    symbol = trades[0].symbol  # assuming only one symbol !

    ohlcv = binance.price_from_binance(
        start_time=trades[0].time,
        end_time=trades[-1].time,
        symbol=symbol,
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
    extras()
