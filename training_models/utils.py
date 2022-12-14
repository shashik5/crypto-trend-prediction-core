import math
import numpy as np

from config.training_config import TrainingConfig
from data_aggregator.historical_data_aggregator import TIMEFRAME_TICK_MAP


def splitDataset(x: np.ndarray, y: np.ndarray):
    sampleCount = x.shape[0]
    trainCount = math.floor(sampleCount * 0.85)
    trainEnd = trainCount
    return x[:trainEnd], y[:trainEnd], x[trainEnd:], y[trainEnd:]


def getStartTime(prevCloseTime: int, timeframe: str, training: TrainingConfig):
    buffer = max(max(training.movingAverage.noOfSamples), training.prevCandleDependants)
    return (int(prevCloseTime - (TIMEFRAME_TICK_MAP[timeframe] * buffer)), buffer)
