from logger import getLogger
import numpy as np
from client.mongo_db import mongoDBClient
from config.training_config import TrainingConfig
from model.candle_info import CandleInfo
from model.candle_type_analytic_info import CandleTypeAnalyticInfo
from model.prediction import Prediction
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Flatten, Conv2D, MaxPooling2D
from datetime import datetime
import random

from training_models.base_model import BaseTrainingModel

SEED = 1234
random.seed(SEED)
np.random.seed(SEED)

CLASS_COUNT = 2
BATCH_SIZE = 100
logger = getLogger()


def getMovingAverage(data: list[CandleInfo], property: str, maSamples: int, index: int):
    if (index == 0):
        return 0.
    targetedItems = data[max(index-maSamples, 0):index]
    item: CandleInfo = data[index]
    ma = sum(list(map(lambda i, multiplier: i[property] * multiplier, targetedItems, range(maSamples, 1, -1))))/(maSamples * (maSamples + 1) / 2)
    return (item.close - ma)/ma


def getVolumeChange(data: list[CandleInfo], index: int):
    if (index == 0):
        return 1
    return (data[index].volume - data[index - 1].volume)/data[index - 1].volume if data[index - 1].volume > 0 else 1


def getChange(currentCandleClose: float, prevCandleClose: float):
    return (currentCandleClose - prevCandleClose)/prevCandleClose


def getCandleType(item: CandleInfo):
    return 1 if item.close > item.open else 0


def getPrevCandleResults(data: list[CandleInfo], noOfDependants: int, prevIndex: int) -> list[float]:
    prevCandleTypes = list()
    for i in range(noOfDependants):
        currentIndex = prevIndex - i
        prevCandleTypes.append(getChange(data[currentIndex].close, data[currentIndex-1].close) if (currentIndex - 1) > -1 else 0)
    return prevCandleTypes


class CandleTypePrediction(BaseTrainingModel):
    def __init__(self, trainingConfig: TrainingConfig):
        BaseTrainingModel.__init__(self, trainingConfig)

    def generateModel(self):
        model = Sequential()
        model.add(Conv2D(144, (3, 3), input_shape=(6, 6, 1)))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Conv2D(288, (2, 2)))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(1, 1)))

        model.add(Flatten())
        model.add(Dense(2))
        model.add(Activation("softmax"))

        model.summary()
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    def testTrainedModel(self, data: list[CandleInfo]):
        analyticsInfo = self.generateAnalyticsInfo(data)
        (xTest, yTest) = self.prepareDataForTraining(analyticsInfo)
        logger.info(f'Begining to test the model with {len(xTest)} samples...')
        startTime = datetime.now()
        totalPredictedSamples = 0
        correctClassifications = 0
        confusionMatrix = np.zeros((CLASS_COUNT, CLASS_COUNT), dtype=np.int16)

        for x, y in zip(xTest, yTest):
            totalPredictedSamples += 1
            predictedValue = self.predict(x)
            if (predictedValue == y):
                correctClassifications += 1
            confusionMatrix[predictedValue, int(y)] += 1

        accuracy = correctClassifications / totalPredictedSamples
        logger.info(f'Testing time: {(datetime.now()-startTime).total_seconds()} seconds')
        logger.info(f'Testing Accuracy: {accuracy}')
        logger.info(f'Confusion Matrix: {confusionMatrix}')
        logger.info('Classification Accuracy:')
        row_sum = np.sum(confusionMatrix, axis=1)
        for cls in range(CLASS_COUNT):
            accuracy = confusionMatrix[cls][cls]/row_sum[cls]
            logger.info(f'Accuracy of class {cls} is {accuracy}')

    def predict(self, input):
        predictions = self.model.predict(input.reshape((1, 6, 6, 1)))
        return int(np.argmax(predictions))

    def generateAnalyticsInfo(self, data: list[CandleInfo]) -> list[CandleTypeAnalyticInfo]:
        analyticsInfo: list[CandleTypeAnalyticInfo] = list()
        for index in range(len(data)):
            maDiff = list()
            item: CandleInfo = data[index]
            for maSamples in self.trainingConfig.movingAverage.noOfSamples:
                maDiff.append(getMovingAverage(data, self.trainingConfig.movingAverage.property, maSamples, index))
            change = getChange(item.close, data[index-1].close) if (index-1) > -1 else 0
            candleType = getCandleType(item)
            isGreenCandle = candleType == 1
            totalLength = item.high-item.low
            shadowTop = (abs(item.high - (item.close if isGreenCandle else item.open))/totalLength) if totalLength > 0 else 0
            shadowBottom = (abs(item.low - (item.open if isGreenCandle else item.close))/totalLength) if totalLength > 0 else 0
            body = ((item.close - item.open)/totalLength) if totalLength > 0 else 100
            prevCandleChanges = getPrevCandleResults(data, self.trainingConfig.prevCandleDependants, index-1)
            analyticsInfo.append(CandleTypeAnalyticInfo(
                symbol=item.symbol,
                interval=item.interval,
                prevCandleChanges=prevCandleChanges,
                body=body,
                change=change,
                candleType=candleType,
                openTime=item.openTime,
                closeTime=item.closeTime,
                movingAverageDifference=maDiff,
                shadowBottom=shadowBottom,
                shadowTop=shadowTop,
                volumeChange=getVolumeChange(data, index)
            ))
        analyticsInfo.sort(key=lambda i: i.closeTime)
        return analyticsInfo

    def prepareDataForTraining(self, analyticsInfo: list[CandleTypeAnalyticInfo]):
        input = np.array(list(map(lambda a: a.getAnalyticsData(), analyticsInfo[:len(analyticsInfo)-1])))
        output = np.array(list(map(lambda a: a.candleType, analyticsInfo[1:])))
        return (input.reshape((-1, 6, 6, 1)), output)

    def prepareDataForPrediction(self, analyticsInfo: list[CandleTypeAnalyticInfo]):
        input = np.array(list(map(lambda a: a.getAnalyticsData(), analyticsInfo)))
        return input.reshape((-1, 6, 6, 1))

    def getPredictionResult(self, prediction: Prediction):
        candleInfo = mongoDBClient.getCandleByOpenTime(prediction.symbol, prediction.interval, prediction.openTime)
        if len(candleInfo) == 0:
            return None
        return 1 if (candleInfo[0].close > candleInfo[0].open) else 0

    def calculatePredictionAccuracy(self):
        for timeframe in self.trainingConfig.predictionTimeframes:
            predictions = mongoDBClient.getCompletedPredictionsByStudyAndTimeframe(self.trainingConfig.study, timeframe)
            totalCount = len(predictions)
            trueCount = 0
            falseCount = 0

            for p in predictions:
                if p.result == p.prediction:
                    trueCount += 1
                else:
                    falseCount += 1

            info = f'PredictionAccuracy for {self.trainingConfig.study} {timeframe} timeframe -> totalPredictions: {totalCount}, accuracy: {trueCount/totalCount}, failedPredictions: {falseCount}'
            logger.info(info)
            print(info)
