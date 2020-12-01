aiobinance
==========

An interactive async client for Binance.

Note: This is an opinionated trading client, it might not fit your style.
Here are a few design choices we made::

- Spot and Margin only: we aim to support beginners with basic trading activities, minimizing risk.
- Discourage MARKET order, preventing potentially large slippage on large bait orders.
- Mono-Account: One machine's user where the `python -m aiobinance` process is running.
- Simple Data Model: we want a clean, binance-specific, data model, leveraging python's dataclasses and types
- Various Human Machine Interfaces: we aim to support skilled technical folks, and provide CLI and Web interfaces
- Various integration points: we leverage our Data Model as a clean interface between various component for your trading activities.


Usage
-----

Use it without any argument::

  python -m aiobinance

this will provide a REPL to interactively gather data from binance, and send orders.


Use it with the hummingbot command and a file as argument::

  python -m aiobinance hummingbot mytrades.csv

this will produce a detailed performance report regarding these trades, as an html file.


You can also use it with various commands to get an idea of aiobinance capabilities::

    python -m aiobinance --help

    Usage: __main__.py [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      auth        simple command to verify auth credentials and optionally
                  store...

      balance     retrieve balance for an authentified user
      daily       display OHLC
      hummingbot  provide a report of hummingbot trades
      monthly     display OHLC
      weekly      display OHLC


Web GUI
-------

Along with the interactive repl, aiobinance provides a webgui by leveraging bokeh.
Just point a webbrowser to the endpoint and you'll get nice plots.



Test
----

To run tests::

  TODO




Develop
-------

Want to signal a problem ? head to the issues section to get the discussion going...
Want to propose a feature ? head to the issues section to get the discussion going...

Tools used::

  - direnv
  - pipenv
  - pre-commit (isort, black, flake8)
  - Nox (pytest)
  - Sphinx

Roadmap
-------

Note : The aim is to get feature parity with aiokraken, and vice versa.
This package takes the top-down, user centric, approach, for better or worse.

- Long running REPL
- Long running webserver (bokeh tornado)
- REPL over the web (terminado)
- Config for binance account
- gather trades from binance
