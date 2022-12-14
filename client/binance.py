from math import floor
from urllib.parse import urljoin, urlencode
from config import appConfig
from config.binance_config import BinanceApiUrls
from model.candle_info import getCandleInfoFromList
from datetime import datetime
import requests


class BinanceClient:
    def __init__(self, key: str, baseUrls: BinanceApiUrls):
        self.__key = key
        self.__baseUrls = baseUrls

    def __get(self, endpoint: str, params: object = {}):

        params['timestamp'] = floor(datetime.now().timestamp() * 1e3)
        params = urlencode(params)
        url = urljoin(self.__baseUrls.fapi, endpoint) + '?' + params
        return requests.get(url, headers=self.__getHeaders())

    def __getHeaders(self):
        return {
            'Content-Type': 'application/json',
            'X-MBX-APIKEY': self.__key
        }

    def getKlines(self, symbol: str, interval: str, startTime: int, endTime: int, limit=1500):
        response = self.__get('klines', {'symbol': symbol, 'interval': interval, 'startTime': startTime, 'endTime': endTime, 'limit': limit})
        response = response.json()
        return list(map(lambda r: getCandleInfoFromList(r, symbol, interval), response))

    def getServerTime(self) -> int:
        response = self.__get('time')
        response = response.json()
        return response['serverTime']


binanceClient = BinanceClient(appConfig.binance.apiKey, appConfig.binance.urls)
