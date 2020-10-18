# Binance API
# Credits to @Bablofil https://github.com/Bablofil/binance-api
import time
import json
import urllib
import hmac, hashlib
import requests

from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

class Binance():
    
    methods = {
            #  Public methods     
            'ping':             {'url': 'ping', 'method': 'GET', 'private': False},                     
            'time':             {'url': 'time', 'method': 'GET', 'private': False},         
            'exchangeInfo':     {'url': 'exchangeInfo', 'method': 'GET', 'private': False},
            'depth':            {'url': 'depth', 'method': 'GET', 'private': False},
            'trades':           {'url': 'trades', 'method': 'GET', 'private': False},  
            'historicalTrades': {'url': 'historicalTrades', 'method': 'GET', 'private': False},  
            'aggTrades':        {'url': 'aggTrades', 'method': 'GET', 'private': False},
            'klines':           {'url': 'klines', 'method': 'GET', 'private': False},   
            'avgPrice':         {'url': 'avgPrice', 'method': 'GET', 'private': False}, 
            'ticker24hr':       {'url': 'ticker/24hr', 'method': 'GET', 'private': False},
            'tickerPrice':      {'url': 'ticker/price', 'method': 'GET', 'private': False},   
            'tickerBookTicker': {'url': 'ticker/bookTicker', 'method': 'GET', 'private': False}, 
            #  Private methods   
            'createOrder':      {'url': 'order', 'method': 'POST', 'private': True},                        
            'testOrder':        {'url': 'test', 'method': 'POST', 'private': True},              
            'orderInfo':        {'url': 'order', 'method': 'GET', 'private': True},
            'cancelOrder':      {'url': 'order', 'method': 'DELETE', 'private': True},
            'openOrders':       {'url': 'openOrders', 'method': 'GET', 'private': True}, 
            'allOrders':        {'url': 'allOrders', 'method': 'GET', 'private': True},     
            'account':          {'url': 'account', 'method': 'GET', 'private': True}, 
            'myTrades':         {'url': 'myTrades', 'method': 'GET', 'private': True}, 
   }
    
    def __init__(self, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = bytearray(API_SECRET, encoding='utf-8')
        self.shift_seconds = 0

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            kwargs.update(command=name)
            return self.call_api(**kwargs)
        return wrapper

    def set_shift_seconds(self, seconds):
        self.shift_seconds = seconds

    @staticmethod
    def interval(startTime: int, endTime: int):
        """
        binance intervals : 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M
        :param startTime: in ms
        :param endTime: in ms
        :return:
        """
        interval_mins = (endTime - startTime) / 60_000  # ms to minutes

        interval = '1M'
        if 0 < interval_mins / 1000 <= 1:
            interval = '1m'
        elif 1 < interval_mins / 1000 <= 3:
            interval = '3m'
        elif 3 < interval_mins / 1000 <= 5:
            interval = '5m'
        elif 5 < interval_mins / 1000 <= 15:
            interval = '15m'
        elif 15 < interval_mins / 1000 <= 30:
            interval = '30m'
        elif 30 < interval_mins / 1000 <= 60:
            interval = '1h'
        elif 60 < interval_mins / 1000 <= 60 * 2:
            interval = '2h'
        elif 60 * 2 < interval_mins / 1000 <= 60 * 4:
            interval = '4h'
        elif 60 * 4 < interval_mins / 1000 <= 60 * 6:
            interval = '6h'
        elif 60 * 6 < interval_mins / 1000 <= 60 * 8:
            interval = '8h'
        elif 60 * 8 < interval_mins / 1000 <= 60 * 12:
            interval = '12h'
        elif 60 * 12 < interval_mins / 1000 <= 60 * 24:
            interval = '1d'
        elif 60 * 24 < interval_mins / 1000 <= 60 * 24 * 3:
            interval = '3d'
        elif 60 * 24 * 3 < interval_mins / 1000 <= 60 * 24 * 7:
            interval = '1w'
        # otherwise the original '1M' setting
        return interval

    def call_api(self, **kwargs):

        command = kwargs.pop('command')
        api_url = 'https://api.binance.com/api/v3/' + self.methods[command]['url']

        payload = kwargs
        headers = {}
        
        payload_str = urllib.parse.urlencode(payload)
        if self.methods[command]['private']:
            payload.update({'timestamp': int(time.time() + self.shift_seconds - 1) * 1000})
            payload_str = urllib.parse.urlencode(payload).encode('utf-8')
            sign = hmac.new(
                key=self.API_SECRET,
                msg=payload_str,
                digestmod=hashlib.sha256
            ).hexdigest()

            payload_str = payload_str.decode("utf-8") + "&signature="+str(sign) 
            headers = {"X-MBX-APIKEY": self.API_KEY}

        if self.methods[command]['method'] == 'GET':
            api_url += '?' + payload_str

        # print(api_url, payload_str, self.methods[command])
        response = requests.request(
            method=self.methods[command]['method'], 
            url=api_url, 
            data="" if self.methods[command]['method'] == 'GET' else payload_str,
            headers=headers)
        
        if 'code' in response.text:
            print(response.text)
            response = response.json()
            return response['error']
        return response.json()

