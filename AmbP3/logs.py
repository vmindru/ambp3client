import logging
from logging import handlers as logging_handlers


class Logg():
    LOGMAXSIZE = 50000000
    LOGBACKUPCOUT = 2
    LOGLEVEL = logging.ERROR

    def create_logger(name, logfile=None, logmaxsize=LOGMAXSIZE, loglevel=LOGLEVEL,
                      logbackupcount=LOGBACKUPCOUT):
        """ create and returns logger object that will log to file"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        format = '%(asctime)s : %(levelname)s : %(name)s : %(message)s'
        formatter = logging.Formatter(format)
        if logfile:
            RotatingFileHandler = logging_handlers.RotatingFileHandler
            file_handler = RotatingFileHandler(logfile, maxBytes=logmaxsize,
                                               backupCount=logbackupcount)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        logger.debug('DEBUG created logger: {}'.format(name))
        return logger
