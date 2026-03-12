"""
Application logger generation
"""

import os
import logging
import logging.handlers


class Logger(object):
    """
    Logger class
    """
    _instances = {}

    @classmethod
    def getInstance(cls, logFile=None):
        """
        Logger get instance
        """
        if not logFile:
            raise Exception("Require log file name.")
        if logFile not in Logger._instances:
                Logger._instances[logFile] = Logger(logFile)

        return Logger._instances[logFile].myLogger

    def __init__(self, logFile):
        """
        Logger initilization
        """
        conf = {"baseDir": "/var/log/cybercnslogs"}
        logBaseDir=conf.get("baseDir", 'logs')
        logMaxBytes=conf.get("maxBytes", 10000000)
        logBackUpCount=conf.get("maxCount", 5)
        if not os.path.exists(logBaseDir):
            os.makedirs(logBaseDir)

        logFilePath = os.path.join(logBaseDir, logFile + ".log")

        # Set up a specific logger with our desired output level
        self.myLogger = logging.getLogger(logFile)
        self.myLogger.setLevel(logging.DEBUG)

        # Add the log message handler to the logger
        handler = logging.handlers.RotatingFileHandler(logFilePath, maxBytes=logMaxBytes,
                                                       backupCount=logBackUpCount)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s %(funcName)s '
                                      '%(lineno)s %(message)s')
        handler.setFormatter(formatter)
        self.myLogger.addHandler(handler)

