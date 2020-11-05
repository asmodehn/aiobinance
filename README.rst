aiobinance
==========

Interactive async client for binance.

Usage
-----

Use it with a file as argument::

  python -m aiobinance mytrades.csv

this willl produce a detailed performance report regarding these trades, as an html file.

Use it without any argument::

  python -m aiobinance

this will provide a REPL to interactively gather data from binance, and send orders.


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
  - pre-commit
  - Nox
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
