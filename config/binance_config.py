import os


class BinanceApiUrls:
    def __init__(self, fapi):
        self.fapi = os.getenv('BINANCE_FAPI') or fapi


class BinanceConfig:
    def __init__(self, urls: BinanceApiUrls, apiKey: str):
        self.urls = BinanceApiUrls(**urls)
        self.apiKey = os.getenv('BINANCE_API_KEY') or apiKey
