from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

import click
from click import Choice

import aiobinance.binance as binance
from aiobinance.cli.params.date import Date

local_tz = datetime.now(tz=timezone.utc).astimezone().tzinfo


@click.group()
def market():
    """ provides cli access to a specific market """
    pass


@market.command()  # TODO : this should return immediate price from ticker for ALL markets. specific market should move into market group
@click.argument("market_pair", required=True)
@click.option(
    "--from", "from_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to yesterday
@click.option(
    "--to", "to_date", type=Date(formats=["%Y-%m-%d"]), default=str(date.today())
)  # default to today
@click.option(
    "--interval",
    "-i",
    type=Choice(
        choices=[
            "1M",
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
        ]
    ),
    default=None,
    required=False,
)  # default to nothing -> calculated based on max data point (for one request only)
@click.option("--utc", default=False, is_flag=True)
@click.option("--html", default=False, is_flag=True)
@click.pass_context
def price(
    ctx,
    market_pair,
    from_date: date,
    to_date: date,
    interval: Optional[str] = None,
    utc=False,
    html=True,
):
    """display prices"""

    time_zero = time(tzinfo=timezone.utc) if utc else time(tzinfo=local_tz)
    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time_zero)
    from_datetime = datetime.combine(from_date, time_zero)

    # quick help to debug datetime tricky issues
    # print(f"from: {from_datetime}")
    # print(f"to: {to_datetime}")

    ohlcv = binance.price_from_binance(
        symbol=market_pair,
        start_time=from_datetime,
        end_time=to_datetime,
        interval=interval,
    )

    if html:

        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        report = aiobinance.web.price_plot(ohlcv=ohlcv)
        output_file(f"{market_pair}_{from_date}_{to_date}_price.html")
        show(report)
    else:
        # TODO : terminal plot ??

        # TODO : daily ticker instead of OHLCV ???
        # tkr = binance.ticker24_from_binance(
        #     symbol=market_pair
        # )
        # print(tkr)
        pass
    print(ohlcv)


if __name__ == "__main__":
    # testing only this cli command
    market()
