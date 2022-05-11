# -*- coding: utf-8 -*-

import logging
import logging.handlers
from datetime import datetime
'''
logging elements
    namespace
    pod name
    state(running)
    kill policy
    kill reason

* DEBUG level
    all pod information
* INFO level
    pod killing information
* WARMING level
    pod killing
    
* ERROR level


# Two log handler
1. DEBUG level
2. INFO level
'''

LOGFILE = './logging.log'
now_time = datetime.now().strftime('%Y-%m-%d_%H')

logger = logging.getLogger('Kube_pod_manager')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_handler(
        filename,
        formatter,
        level,
        maxBytes=10*1000*1024,
        backupCount=10,
    ):
    _logger = logging.handlers.RotatingFileHandler(
        filename=f'{filename}',
        mode='a',
        maxBytes=maxBytes,
        backupCount=backupCount,
    )
    _logger.setFormatter(formatter)
    _logger.setLevel(level)
    return _logger


def close_handler(logger):
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()
    

debug_logger = create_handler(
        filename=f'{now_time}_logging_debug.log',
        formatter=formatter,
        level = logging.DEBUG,
        maxBytes=50*1000*1024,
    )
info_logger = create_handler(
        filename=f'{now_time}_logging_info.log',
        formatter=formatter,
        level = logging.INFO,
    )
    
logger.addHandler(debug_logger)
logger.addHandler(info_logger)


if __name__ == '__main__':
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
    close_handler(logger)

