# Binance API
# Credits to @Bablofil https://github.com/Bablofil/binance-api
import hashlib
import hmac
import json
import time
import urllib
from typing import Dict, Optional
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import requests
from result import Err, Ok, Result

from aiobinance.config import Credentials


class PrivateRequestNonAuthorized(Exception):
    pass


class Binance:

    methods = {
        #  Public methods
        "ping": {"url": "api/v3/ping", "method": "GET", "private": False},
        "time": {"url": "api/v3/time", "method": "GET", "private": False},
        "exchangeInfo": {
            "url": "api/v3/exchangeInfo",
            "method": "GET",
            "private": False,
        },
        "depth": {"url": "api/v3/depth", "method": "GET", "private": False},
        "trades": {"url": "api/v3/trades", "method": "GET", "private": False},
        "historicalTrades": {
            "url": "api/v3/historicalTrades",
            "method": "GET",
            "private": False,
        },
        "aggTrades": {"url": "api/v3/aggTrades", "method": "GET", "private": False},
        "klines": {"url": "api/v3/klines", "method": "GET", "private": False},
        "avgPrice": {"url": "api/v3/avgPrice", "method": "GET", "private": False},
        "ticker24hr": {"url": "api/v3/ticker/24hr", "method": "GET", "private": False},
        "tickerPrice": {
            "url": "api/v3/ticker/price",
            "method": "GET",
            "private": False,
        },
        "tickerBookTicker": {
            "url": "api/v3/ticker/bookTicker",
            "method": "GET",
            "private": False,
        },
        #  Private methods
        "createOrder": {"url": "api/v3/order", "method": "POST", "private": True},
        "testOrder": {"url": "api/v3/order/test", "method": "POST", "private": True},
        "orderInfo": {"url": "api/v3/order", "method": "GET", "private": True},
        "cancelOrder": {"url": "api/v3/order", "method": "DELETE", "private": True},
        "openOrders": {"url": "api/v3/openOrders", "method": "GET", "private": True},
        "allOrders": {"url": "api/v3/allOrders", "method": "GET", "private": True},
        "account": {"url": "api/v3/account", "method": "GET", "private": True},
        "myTrades": {"url": "api/v3/myTrades", "method": "GET", "private": True},
        # added aiobinance  TMP waiting refactor...
        "coins": {
            "url": "sapi/v1/capital/config/getall",
            "method": "GET",
            "private": True,
        },
    }

    def __init__(
        self,
        credentials: Optional[Credentials] = None,
    ):
        self.credentials = credentials
        self.shift_seconds = 0

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            kwargs.update(command=name)
            return self.call_api(**kwargs)

        return wrapper

    def set_shift_seconds(self, seconds):
        self.shift_seconds = seconds

    @staticmethod
    def interval(
        startTime: int, endTime: int, max_datapoints=240
    ):  # TODO: max datapoint clever default ??
        """
        binance intervals : 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
        :param startTime: in ms
        :param endTime: in ms
        :return:
        """
        interval_mins = (endTime - startTime) / 60_000  # ms to minutes

        interval = "1M"
        if 0 < interval_mins / max_datapoints <= 1:
            interval = "1m"
        elif 1 < interval_mins / max_datapoints <= 3:
            interval = "3m"
        elif 3 < interval_mins / max_datapoints <= 5:
            interval = "5m"
        elif 5 < interval_mins / max_datapoints <= 15:
            interval = "15m"
        elif 15 < interval_mins / max_datapoints <= 30:
            interval = "30m"
        elif 30 < interval_mins / max_datapoints <= 60:
            interval = "1h"
        elif 60 < interval_mins / max_datapoints <= 60 * 2:
            interval = "2h"
        elif 60 * 2 < interval_mins / max_datapoints <= 60 * 4:
            interval = "4h"
        elif 60 * 4 < interval_mins / max_datapoints <= 60 * 6:
            interval = "6h"
        elif 60 * 6 < interval_mins / max_datapoints <= 60 * 8:
            interval = "8h"
        elif 60 * 8 < interval_mins / max_datapoints <= 60 * 12:
            interval = "12h"
        elif 60 * 12 < interval_mins / max_datapoints <= 60 * 24:
            interval = "1d"
        elif 60 * 24 < interval_mins / max_datapoints <= 60 * 24 * 3:
            interval = "3d"
        elif 60 * 24 * 3 < interval_mins / max_datapoints <= 60 * 24 * 7:
            interval = "1w"
        # otherwise the original '1M' setting
        return interval

    def call_api(self, **kwargs) -> Result[Dict, Dict]:

        command = kwargs.pop("command")
        api_url = "https://api.binance.com/" + self.methods[command]["url"]
        payload = kwargs
        headers = {}

        payload_str = urllib.parse.urlencode(payload)
        if self.methods[command]["private"]:
            if self.credentials is None:
                raise PrivateRequestNonAuthorized(
                    f"{command} is a private request but credentials are {self.credentials}. Aborted."
                )
            payload.update(
                {"timestamp": int(time.time() + self.shift_seconds - 1) * 1000}
            )
            payload_str = urllib.parse.urlencode(payload).encode("utf-8")
            sign = hmac.new(
                key=bytearray(self.credentials.secret, encoding="utf-8"),
                msg=payload_str,
                digestmod=hashlib.sha256,
            ).hexdigest()

            payload_str = payload_str.decode("utf-8") + "&signature=" + str(sign)
            headers = {"X-MBX-APIKEY": self.credentials.key}

        if self.methods[command]["method"] == "GET":
            api_url += "?" + payload_str
        # TODO : review this... some commands put payload inside request body, which is not filtered on cassettes (annoyance...)
        # print(api_url, payload_str, self.methods[command])
        response = requests.request(
            method=self.methods[command]["method"],
            url=api_url,
            data="" if self.methods[command]["method"] == "GET" else payload_str,
            headers=headers,
        )

        if "code" in response.text:
            print(response.text)
            response = response.json()
            return Err(response)
        return Ok(response.json())
