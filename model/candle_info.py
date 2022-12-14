class CandleInfo:
    def __init__(self, symbol: str, interval: str, openTime: int, open: float, high: float, low: float, close: float, volume: float, closeTime: int, quoteAssetVolume: float, numberOfTrades: int, takerBuyBaseAssetVolume: float, takerBuyQuoteAssestVolume: float):
        self.symbol = symbol
        self.interval = interval
        self.openTime = int(openTime)
        self.open = float(open)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = float(volume)
        self.closeTime = int(closeTime)
        self.quoteAssetVolume = float(quoteAssetVolume)
        self.numberOfTrades = int(numberOfTrades)
        self.takerBuyBaseAssetVolume = float(takerBuyBaseAssetVolume)
        self.takerBuyQuoteAssestVolume = float(takerBuyQuoteAssestVolume)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def toRecord(self):
        obj = self.__dict__
        obj['_id'] = f'{self.symbol}_{self.interval}_{self.openTime}'
        return obj


def getCandleInfoFromList(klineData: list, symbol: str, interval: str,):
    (openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssestVolume, ignoredValue) = klineData
    return CandleInfo(symbol, interval, openTime, open, high, low, close, volume, closeTime, quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssestVolume)
