from pymongo import MongoClient, database, cursor
from model.candle_info import CandleInfo
from config import appConfig
from model.prediction import Prediction


COLLECTION_NAMES = {
    'candleInfo': 'candle_info',
    'prediction': 'prediction',
    'updateLog': 'update_log'
}


def toCandleInfoList(queryResult: cursor.Cursor) -> list[CandleInfo]:
    candles = []
    for r in queryResult:
        candles.append(CandleInfo(**r))
    return candles


def toPredictionList(queryResult: cursor.Cursor) -> list[Prediction]:
    predictions = []
    for r in queryResult:
        predictions.append(Prediction(**r))
    return predictions


class MongoDBClient:
    def __init__(self, conncetionString: str, database: str):
        self.conncetionString = conncetionString
        self.database = database

    def __getDB(self) -> database.Database:
        client = MongoClient(self.conncetionString, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        return client.get_database(self.database)

    def __getCollection(self, collectionName):
        return self.__getDB().get_collection(collectionName)

    def __getCandleInfoCollection(self):
        return self.__getCollection(COLLECTION_NAMES.get('candleInfo'))

    def __getPredictionCollection(self):
        return self.__getCollection(COLLECTION_NAMES.get('prediction'))

    def __getUpdateLogCollection(self):
        return self.__getCollection(COLLECTION_NAMES.get('updateLog'))

    def insertCandleInfo(self, candleData: list[CandleInfo]):
        col = self.__getCandleInfoCollection()
        return col.insert_many(map(lambda c: c.toRecord(), candleData))

    def getCandleInfo(self, symbol: str, interval: str, startTime=0):
        col = self.__getCandleInfoCollection()
        res = col.find({
            'symbol': symbol,
            'interval': interval,
            'openTime': {'$gt': startTime}
        }, {
            '_id': 0
        }).sort('openTime', 1)
        return toCandleInfoList(res)

    def getCandleInfoInRange(self, symbol: str, interval: str, startTime: int, closeTime: int):
        col = self.__getCandleInfoCollection()
        res = col.find({
            'symbol': symbol,
            'interval': interval,
            'openTime': {'$gt': startTime},
            'closeTime': {
                '$lte': closeTime
            }
        }, {
            '_id': 0
        }).sort('openTime', 1)
        return toCandleInfoList(res)

    def getLastCandle(self, symbol: str, interval: str):
        col = self.__getCandleInfoCollection()
        res = col.find({
            'symbol': symbol,
            'interval': interval
        }, {
            '_id': 0
        }).sort('openTime', -1).limit(1)
        return toCandleInfoList(res)

    def getCandleByOpenTime(self, symbol: str, interval: str, openTime: int):
        col = self.__getCandleInfoCollection()
        res = col.find_one({
            'symbol': symbol,
            'interval': interval,
            'openTime': openTime
        }, {
            '_id': 0
        })
        return toCandleInfoList([res] if res != None else [])

    def insertPredictions(self, predictions: list[Prediction]):
        col = self.__getPredictionCollection()
        return col.insert_many(map(lambda p: p.toRecord(), predictions))

    def recordUpdate(self, timestamp: int):
        col = self.__getUpdateLogCollection()
        return col.insert_one({'lastUpdateAt': timestamp})

    def getLastPrediction(self, study: str, symbol: str, interval: str):
        col = self.__getPredictionCollection()
        res = col.find({
            'study': study,
            'symbol': symbol,
            'interval': interval
        }, {
            '_id': 0
        }).sort('openTime', -1).limit(1)
        return toPredictionList(res)

    def updatePredictionResult(self, prediction: Prediction):
        col = self.__getPredictionCollection()
        col.update_one({
            '_id': prediction.toRecord()['_id']
        }, {
            '$set': {
                'result': prediction.result
            }
        })

    def getPredictionsToUpdate(self, study: str, symbol: str, interval: str, serverTime: int):
        col = self.__getPredictionCollection()
        res = col.find({
            'study': study,
            'symbol': symbol,
            'interval': interval,
            'result': None,
            'closeTime': {
                '$lte': serverTime
            }
        }, {
            '_id': 0
        }).sort('openTime', 1)
        return toPredictionList(res)

    def getAllPredictions(self):
        col = self.__getPredictionCollection()
        res = col.find({}, {
            '_id': 0
        }).sort('openTime', 1)
        return toPredictionList(res)

    def getCompletedPredictionsByStudyAndTimeframe(self, study: str, timeframe: str):
        col = self.__getPredictionCollection()
        res = col.find({
            'study': study,
            'interval': timeframe,
            'result': {'$ne': None}
        }, {
            '_id': 0
        }).sort('openTime', 1)
        return toPredictionList(res)


mongoDBClient = MongoDBClient(appConfig.mongoDB.conncetionString, appConfig.mongoDB.database)
