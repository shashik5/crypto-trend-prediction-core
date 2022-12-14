from config.mongo_config import MongoDbConfig
from config.training_config import toTrainingConfig, TrainingConfig
from config.binance_config import BinanceConfig


class AppConfig:
    def __init__(self, basePath: str, modelDirectory:str, binance: BinanceConfig, mongoDB: MongoDbConfig, trainingConfig: list[TrainingConfig]):
        self.basePath = basePath
        self.modelDirectory = modelDirectory
        self.binance = BinanceConfig(**binance)
        self.trainingConfig = list(map(toTrainingConfig, trainingConfig))
        self.mongoDB = MongoDbConfig(**mongoDB)
