import os


class MongoDbConfig:
    def __init__(self, conncetionString: str, database: str):
        self.conncetionString = os.getenv('MONGO_CONNECTION_STRING') or conncetionString
        self.database = os.getenv('MONGO_DATABASE_NAME') or database
