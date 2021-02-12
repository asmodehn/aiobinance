from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

import click
from click import Choice

import aiobinance.binance as binance
from aiobinance.api.exchange import Exchange
from aiobinance.api.market import Market
from aiobinance.api.model.timeinterval import TimeStep
from aiobinance.api.rawapi import Binance
from aiobinance.cli.cli_group import cli
from aiobinance.cli.params.date import Date

local_tz = datetime.now(tz=timezone.utc).astimezone().tzinfo


@cli.command()  # TODO : this should return immediate price from ticker for ALL markets. specific market should move into market group
@click.argument("market", type=str, required=True)
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
            # "1M",  # not supported by aiobinance
            # one month is an ambiguous timedelta, and not really interesting for algo trading.
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
def price(
    market: str,
    from_date: date,
    to_date: date,
    interval: Optional[str] = None,
    utc=False,
    html=True,
):
    """display prices"""
    import asyncio

    # API for public endpoints only
    api = Binance()

    exchange = Exchange(api=api, test=True)

    # while we are moving to an async interface
    asyncio.run(exchange())  # retrieving data

    market = exchange.markets[market]

    time_zero = time(tzinfo=timezone.utc) if utc else time(tzinfo=local_tz)
    if to_date == date.today():
        to_datetime = datetime.now(tz=timezone.utc)
    else:
        to_datetime = datetime.combine(from_date + timedelta(days=1), time_zero)
    from_datetime = datetime.combine(from_date, time_zero)

    # quick help to debug datetime tricky issues
    # print(f"from: {from_datetime}")
    # print(f"to: {to_datetime}")

    # converting to TimeStep
    # TODO :  proper parser...
    if interval[-1] == "m":
        interval = timedelta(minutes=int(interval[:-1]))
    elif interval[-1] == "h":
        interval = timedelta(hours=int(interval[:-1]))
    elif interval[-1] == "d":
        interval = timedelta(days=int(interval[:-1]))
    elif interval[-1] == "w":
        interval = timedelta(weeks=int(interval[:-1]))
    else:
        raise RuntimeError(f"Cannot understand timestep {interval}")
    interval = TimeStep(interval)

    # while we are moving to an async interface
    ohlcv = asyncio.run(
        market.price.request(
            start_time=from_datetime, stop_time=to_datetime, interval=interval
        )
    )

    if html:

        from bokeh.io import output_file
        from bokeh.plotting import show

        import aiobinance.web

        # TODO : replace price_plot with recent working bokeh layout (triplescreen?)
        report = aiobinance.web.price_plot(ohlcv=ohlcv[interval])
        output_file(f"{market.info.symbol}_{from_date}_{to_date}_price.html")
        show(report)
    else:
        # TODO : terminal plot ??

        # TODO : daily ticker instead of OHLCV ???
        # tkr = binance.ticker24_from_binance(
        #     symbol=market_pair
        # )
        # print(tkr)
        pass
    print(ohlcv[interval])


if __name__ == "__main__":
    # testing only this cli command
    cli()
