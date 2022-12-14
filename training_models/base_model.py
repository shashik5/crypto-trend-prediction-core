from logger import getLogger
from datetime import datetime
import os
from client.binance import binanceClient
from config.training_config import TrainingConfig
from client.mongo_db import mongoDBClient
from data_aggregator.historical_data_aggregator import TIMEFRAME_TICK_MAP
from model.candle_info import CandleInfo
from model.prediction import Prediction
from tensorflow.keras.models import load_model
from config import appConfig
from training_models.utils import getStartTime


logger = getLogger()


class BaseTrainingModel:
    def __init__(self, trainingConfig: TrainingConfig):
        self.trainingConfig = trainingConfig
        self.model = self.getModel()

    def saveModel(self):
        self.model.save(os.path.join(appConfig.basePath, appConfig.modelDirectory, self.trainingConfig.modelName), save_format='tf')

    def trainModel(self):
        trainingData = mongoDBClient.getCandleInfo(self.trainingConfig.symbol, self.trainingConfig.trainingTimeframe)
        analyticsInfo = self.generateAnalyticsInfo(trainingData)
        (xTrain, yTrain) = self.prepareDataForTraining(analyticsInfo)
        logger.info(f'Beginning to train the model: {self.trainingConfig.study} {self.trainingConfig.symbol} {self.trainingConfig.trainingTimeframe} with {len(xTrain)} samples')
        startTime = datetime.now()
        epochs = self.trainingConfig.epochs
        batchSize = self.trainingConfig.batchSize
        self.model.fit(xTrain, yTrain, epochs=epochs, validation_split=0.2, shuffle=True, batch_size=batchSize)
        logger.info(f'Training time: {(datetime.now()-startTime).total_seconds()} seconds')
        self.saveModel()
        for timeframe in self.trainingConfig.predictionTimeframes:
            logger.info(f'Testing {self.trainingConfig.symbol}_{timeframe} using {self.trainingConfig.modelName} model')
            testData = mongoDBClient.getCandleInfo(self.trainingConfig.symbol, timeframe)
            self.testTrainedModel(testData)

    def getModel(self):
        path = os.path.join(appConfig.basePath, appConfig.modelDirectory, self.trainingConfig.modelName)
        if os.path.exists(path):
            return load_model(path)
        return self.generateModel()

    def runPredictions(self):
        serverTime = binanceClient.getServerTime()
        for timeframe in self.trainingConfig.predictionTimeframes:
            logger.info(f'Running predictions: {self.trainingConfig.study} {self.trainingConfig.symbol} {timeframe}')
            lastPredictionRes = mongoDBClient.getLastPrediction(self.trainingConfig.study, self.trainingConfig.symbol, timeframe)
            (startTime, buffer) = getStartTime(lastPredictionRes[-1].openTime - 1, timeframe,
                                               self.trainingConfig) if ((len(lastPredictionRes) > 0 and isinstance(lastPredictionRes[0], Prediction))) else (0, 0)
            newData = mongoDBClient.getCandleInfoInRange(self.trainingConfig.symbol, timeframe, startTime, serverTime)
            analyticsInfo = self.generateAnalyticsInfo(newData)
            predictionData = self.prepareDataForPrediction(analyticsInfo[buffer:])
            predictions: list[Prediction] = []
            for (data, info) in zip(predictionData, analyticsInfo[buffer:]):
                result = self.predict(data)
                prediction = Prediction(result, self.trainingConfig.symbol, timeframe, self.trainingConfig.study,
                                        info.closeTime + 1, info.closeTime + TIMEFRAME_TICK_MAP[timeframe])
                predictions.append(prediction)
            if len(predictions) > 0:
                mongoDBClient.insertPredictions(predictions)
                logger.info(f'{len(predictions)} new predictions: {self.trainingConfig.study} {self.trainingConfig.symbol} {timeframe}')
            else:
                logger.info(f'There are no new predictions: {self.trainingConfig.study} {self.trainingConfig.symbol} {timeframe}')

    def updatePreviousPredictionResult(self):
        training = self.trainingConfig
        serverTime = binanceClient.getServerTime()
        for timeframe in training.predictionTimeframes:
            logger.info(f'Updating previous prediction results: {self.trainingConfig.study} {self.trainingConfig.symbol} {timeframe}')
            predictionsToUpdate = mongoDBClient.getPredictionsToUpdate(training.study, training.symbol, timeframe, serverTime)
            if (len(predictionsToUpdate) == 0 or (predictionsToUpdate[0].openTime + TIMEFRAME_TICK_MAP[timeframe] + 1) > serverTime):
                logger.info(f'There are no predictions to update yet: {self.trainingConfig.study} {self.trainingConfig.symbol} {timeframe}')
                continue

            for prediction in predictionsToUpdate:
                prediction.result = self.getPredictionResult(prediction)
                mongoDBClient.updatePredictionResult(prediction)

    def generateModel(self):
        raise Exception('Not Implemented')

    def testTrainedModel(self, data: list[CandleInfo]):
        pass

    def predict(self, input) -> list[Prediction]:
        raise Exception('Not Implemented')

    def generateAnalyticsInfo(self, data: list[CandleInfo]):
        return []

    def prepareDataForTraining(self, analyticsInfo: list):
        return ([], [])

    def prepareDataForPrediction(self, analyticsInfo: list):
        return []

    def getPredictionResult(self, prediction: Prediction):
        return None

    def calculatePredictionAccuracy(self):
        return {'totalPredictions': 0, 'accuracy': 0, 'failedPredictions': 0}
