# A running "server" providing:
# - A local repl to interact with the running server (tmuxable, screenable, dockerable)
# - A websocket terminal backend for remote repl control, provided via terminado
# - A (remote) graphical interface provided via bokeh, served by async tornado 5
#
# Usecase workflow :
# An app (typically a trading bot, lets call it 'tradebot') depends on aiobinance.
# 1. 'tradebot' is launched (optionally remotely), and runs as a process which exposes a repl (local only, potentially inside a docker container)
# 2. a known user connects (ssh) to the machine, and can dynamically order 'tradebot' via the repl, to expose it via websocket.
# 3. Via the repl, a user can also dynamically order 'tradebot' to expose a webpage presenting various graphics regarding tradebot performance...
#
#
#  Run 'tradebot' -> REPL longrunning  ---?--->  Bokeh Webpage.
#        |               /   /                        /
#  SSH remote access ---/ --/-- via text webbrowser -/
#                          /                        /
#  WebBrowser ------------/------------------------/
#
# characteristics:
# - when local connect -> enable remote for current user (some way to make that simple & intuitive yet secure ??)
# - when web connects -> refuse, unless user is "known"...
# - when local disconnect -> keep running local, drop remote, connections
# - when web disconnect -> drop remote connections
#

# => exchange account authentication should be provided on startup, and stay in memory, encrypted...
# => this __main__ module should start the repl by default (current unix user, exchange account already accessible)
# => repl should provide access to functions to enable webconnections (authentication details)
# => __main__ should provide long arguments to allow webconnections (authentication details)
# => webconnection should not be possible without authentication (given exchange account details is stored in running process)



import aiobinance.binance as binance

# TODO
# binance.trades_from_binance()

import aiobinance.csv as csv
import aiobinance.binance as binance

trades = csv.trades_from_csv("../binance-COTI-BNB_files/hummingbot_data/trades_conf_pure_mm_coti_bnb_binance.csv")
print(trades.head())


ohlcv = binance.ohlcv_from_binance(
    startTime = trades.Timestamp.iloc[0],
    endTime = trades.Timestamp.iloc[-1],
    symbol = "COTIBNB"
)

import aiobinance.web
report = aiobinance.web.trades_layout(ohlcv=ohlcv, trades=trades)

from bokeh.io import output_file
output_file("report.html")

from bokeh.plotting import show
show(report)







