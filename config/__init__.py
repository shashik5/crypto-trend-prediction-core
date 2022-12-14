import json
from config.app_config import AppConfig
from dotenv import load_dotenv

load_dotenv()

appConfig: AppConfig
with open('config.json', 'r') as jsonfile:
    appConfig = AppConfig(**json.load(jsonfile))
