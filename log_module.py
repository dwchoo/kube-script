# -*- coding: utf-8 -*-

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
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


def close_handler(logger):
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()

class log_module:
    def __init__(self,file_path='./log'):

        Path(file_path).mkdir(parents=True,exist_ok=True)
        now_time = datetime.now().strftime('%Y-%m-%d_%H')

        self.logger = logging.getLogger('Kube_pod_manager')
        self.logger.setLevel(logging.DEBUG)

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



        debug_logger = create_handler(
                filename=f'{file_path}/{now_time}_logging_debug.log',
                formatter=formatter,
                level = logging.DEBUG,
                maxBytes=50*1000*1024,
            )
        info_logger = create_handler(
                filename=f'{file_path}/{now_time}_logging_info.log',
                formatter=formatter,
                level = logging.INFO,
            )
            
        self.logger.addHandler(debug_logger)
        self.logger.addHandler(info_logger)


if __name__ == '__main__':
    logger_module = log_module(file_path='./log')
    logger = logger_module.logger
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
    close_handler(logger)

