class MovingAverageConfig:
    def __init__(self, property: str, noOfSamples: list[int]):
        self.property = property
        self.noOfSamples = noOfSamples


class TrainingConfig:
    def __init__(self, symbol: str, study: str, modelName: str, trainingTimeframe: str, predictionTimeframes: list[str], prevCandleDependants: int, movingAverage: MovingAverageConfig, epochs: int, batchSize: int):
        self.symbol = symbol
        self.study = study
        self.modelName = modelName
        self.trainingTimeframe = trainingTimeframe
        self.predictionTimeframes = predictionTimeframes
        self.prevCandleDependants = prevCandleDependants
        self.movingAverage = MovingAverageConfig(**movingAverage)
        self.epochs = epochs
        self.batchSize = batchSize


def toTrainingConfig(config: TrainingConfig):
    return TrainingConfig(**config)
