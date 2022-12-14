from logger import getLogger
from client.binance import binanceClient
from client.mongo_db import mongoDBClient
from config import appConfig
from data_aggregator.historical_data_aggregator import collectHistoricalData, TIMEFRAME_TICK_MAP
from model.candle_info import CandleInfo
from training_models.base_model import BaseTrainingModel
from training_models.candle_type_prediction import CandleTypePrediction
from training_models.utils import getStartTime
from getopt import getopt
import sys


TRAINING_MODEL_MAP = {
    'candleTypePrediction': CandleTypePrediction
}

logger = getLogger()


def collectAllHistoricalData():
    try:
        logger.info('Beginning to collect historical data')
        trainingConfig = appConfig.trainingConfig
        for training in trainingConfig:
            serverTime = binanceClient.getServerTime()
            lastCandleRes = mongoDBClient.getLastCandle(training.symbol, training.trainingTimeframe)

            (startTime, buffer) = getStartTime(lastCandleRes[-1].closeTime, training.trainingTimeframe,
                                               training) if ((len(lastCandleRes) > 0 and isinstance(lastCandleRes[0], CandleInfo))) else (0, 0)
            newData = []
            if (len(lastCandleRes) == 0 or (lastCandleRes[0].closeTime + TIMEFRAME_TICK_MAP[training.trainingTimeframe] + 1) < serverTime):
                logger.info(f'Collecting historical data for {training.symbol} {training.trainingTimeframe}')
                newData = collectHistoricalData(training.symbol, training.trainingTimeframe, startTime)
                mongoDBClient.insertCandleInfo(newData[buffer:])

            for timeframe in training.predictionTimeframes:
                serverTime = binanceClient.getServerTime()
                lastCandleRes = mongoDBClient.getLastCandle(training.symbol, timeframe)
                (startTime, buffer) = getStartTime(lastCandleRes[-1].closeTime, timeframe,
                                                   training) if ((len(lastCandleRes) > 0 and isinstance(lastCandleRes[0], CandleInfo))) else (0, 0)
                if (len(lastCandleRes) == 0 or (lastCandleRes[0].closeTime + TIMEFRAME_TICK_MAP[timeframe] + 1) < serverTime):
                    logger.info(f'Collecting historical data for {training.symbol} {timeframe}')
                    newData = collectHistoricalData(training.symbol, timeframe, startTime)
                    mongoDBClient.insertCandleInfo(newData[buffer:])
        logger.info('Completed collecting historical data')
    except:
        logger.exception('An Error occured while collecting historical data')


def trainModels():
    try:
        trainingConfig = appConfig.trainingConfig
        for training in trainingConfig:
            TrainingModel = TRAINING_MODEL_MAP.get(training.study)
            trainingModel: BaseTrainingModel = TrainingModel(training)
            trainingModel.trainModel()
        logger.info('Completed training all models')
    except:
        logger.exception('An Error occured while training the model')


def runPredictions():
    try:
        trainingConfig = appConfig.trainingConfig
        for training in trainingConfig:
            TrainingModel = TRAINING_MODEL_MAP.get(training.study)
            trainingModel: BaseTrainingModel = TrainingModel(training)
            trainingModel.runPredictions()
        logger.info('Completed running predictions')
    except:
        logger.exception('An Error occured while running predictions')


def updatePreviousPredictionResult():
    try:
        trainingConfig = appConfig.trainingConfig
        for training in trainingConfig:
            TrainingModel = TRAINING_MODEL_MAP.get(training.study)
            trainingModel: BaseTrainingModel = TrainingModel(training)
            trainingModel.updatePreviousPredictionResult()
        logger.info('Completed updating previous prediction results')
    except:
        logger.exception('An Error occured while updating the previous results')


def calculatePredictionAccuracy():
    logger.info(f'Beginning to calculate prediction accuracy')
    try:
        for training in appConfig.trainingConfig:
            TrainingModel = TRAINING_MODEL_MAP.get(training.study)
            trainingModel: BaseTrainingModel = TrainingModel(training)
            trainingModel.calculatePredictionAccuracy()
        logger.info(f'Completed calculating prediction accuracy')
    except:
        logger.exception('An Error occured while calculating perdiction accuracy')


def recordUpdateLog():
    logger.info(f'Beginning to record update log')
    try:
        serverTime = binanceClient.getServerTime()
        mongoDBClient.recordUpdate(serverTime)
        logger.info('Completed recording update log')
    except:
        logger.exception('An Error occured while recording update log')


def upsertNewPredictions():
    collectAllHistoricalData()
    runPredictions()
    updatePreviousPredictionResult()
    recordUpdateLog()


ARG_HELP = f'{sys.argv[0]} -a <action> -s <study>'


def main():
    action = None
    study = None
    try:
        opts, args = getopt(sys.argv[1:], 'h:a', ['help', 'action='])
    except:
        print(ARG_HELP)
        sys.exit(0)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(ARG_HELP)
            sys.exit(2)
        elif opt in ('-a', '--action'):
            action = arg

    match action.lower():
        case 'collectallhistoricaldata':
            return collectAllHistoricalData()
        case 'trainmodels':
            return trainModels()
        case 'runpredictions':
            return runPredictions()
        case 'updatepreviouspredictionresult':
            return updatePreviousPredictionResult()
        case 'recordupdatelog':
            return recordUpdateLog()
        case 'upsertnewpredictions':
            return upsertNewPredictions()
        case 'calculatepredictionaccuracy':
            return calculatePredictionAccuracy()
        case _:
            print('Invalid arguments')
            print(ARG_HELP)
            sys.exit(1)


main()
