#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import logging

from PySide2.QtWidgets import QApplication

from src.pyqt.NifBatchTools.NifBatchTools import NifBatchTools
from src.utils.config import get_config

if __name__ == '__main__':
    try:
        logging.basicConfig(filemode="w",
                            filename="htool.log",
                            level=logging.getLevelName(get_config().get("LOG", "level")),
                            format='%(asctime)s - [%(levelname)s] - %(name)s : %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

        if not get_config().get("LOG", "enabled"):
            logger = logging.getLogger()
            logger.disabled = True

        logging.info(" =============== STARTING LOGGING ===============")
        logging.info("Log Level : " + get_config().get("LOG", "level"))
        app = QApplication(sys.argv)
        tool = NifBatchTools()
        tool.setAppStyle(app)
        tool.open()
        sys.exit(app.exec_())
    except SystemExit:
        logging.info("Closing application")
    except:
        logging.exception("Fatal error :")
        raise
