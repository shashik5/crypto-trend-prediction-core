import numpy as np


class CandleTypeAnalyticInfo:
    def __init__(self, symbol: str, interval: str, shadowTop: float, shadowBottom: float, body: float, prevCandleChanges: list[float], candleType: int, change: float, movingAverageDifference: list[float], openTime: int, closeTime: int, volumeChange: float):
        self.symbol = symbol
        self.interval = interval
        self.shadowTop = shadowTop
        self.shadowBottom = shadowBottom
        self.body = body
        self.prevCandleChanges = list(prevCandleChanges)
        self.change = change
        self.candleType = candleType
        self.movingAverageDifference = list(movingAverageDifference)
        self.openTime = openTime
        self.closeTime = closeTime
        self.volumeChange = volumeChange

    def getAnalyticsData(self):
        data = list()
        data.append(self.shadowTop)
        data.append(self.shadowBottom)
        data.append(self.body)
        data.append(self.volumeChange)
        data.extend(self.prevCandleChanges)
        data.extend(self.movingAverageDifference)
        while len(data) < 36:
            data.append(0)
        return np.array(data).reshape((6, 6))
