from datetime import datetime
import logging
import os

def getLogger():
    if os.path.isdir('logs') != True:
        os.mkdir('logs')
    date = datetime.today()
    logging.basicConfig(filename=f'logs/log_{date.day}_{date.month}_{date.year}.log', format='%(asctime)s - %(levelname)s: %(message)s', encoding='utf-8', level=logging.INFO)
    return logging.getLogger('logger')
    