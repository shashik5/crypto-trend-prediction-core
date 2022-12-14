class Prediction:
    def __init__(self, prediction, symbol: str, interval: str, study: str, openTime: int, closeTime: int, result = None):
        self.prediction = prediction
        self.study = study
        self.openTime = openTime
        self.closeTime = closeTime
        self.symbol = symbol
        self.interval = interval
        self.result = result

    def __getitem__(self, key: str):
        return getattr(self, key)

    def toRecord(self):
        obj = self.__dict__
        obj['_id'] = f'{self.study}_{self.symbol}_{self.interval}_{self.openTime}'
        return obj