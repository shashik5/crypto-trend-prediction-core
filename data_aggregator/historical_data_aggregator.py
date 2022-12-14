from client.binance import binanceClient
from model.candle_info import CandleInfo


def getTicks(hours: int):
    return hours * 3600000


TIMEFRAME_TICK_MAP = {
    '15m': getTicks(0.25),
    '30m': getTicks(0.5),
    '1h': getTicks(1),
    '4h': getTicks(4),
    '8h': getTicks(8),
    '1d': getTicks(24),
    '1w': getTicks(168)
}


def collectHistoricalData(symbol: str, timeframe: str, startTimestamp=0):
    serverTime = binanceClient.getServerTime()
    result: list[CandleInfo] = list()
    endTime = serverTime - TIMEFRAME_TICK_MAP[timeframe]

    while (startTimestamp < endTime):
        newResult = binanceClient.getKlines(symbol, timeframe, startTimestamp, endTime)
        result.extend(newResult)
        startTimestamp = newResult[-1].closeTime

    result.sort(key=lambda i: i.closeTime)
    return result
