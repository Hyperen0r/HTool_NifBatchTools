#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys
import time
import traceback

from PySide2.QtCore import QObject, Signal, QRunnable
# From : https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
from pyffi.formats.nif import NifFormat

log = logging.getLogger(__name__)


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(int, bool)
    progress = Signal(int)
    start = Signal(int)


class Worker(QRunnable):
    '''
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result, True)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class NifProcessWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, *args, **kwargs):
        super(NifProcessWorker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        result = False
        try:
            self.signals.start.emit(self.kwargs['index'])
            time.sleep(0.1)
            result = self.process_nif_files(self.kwargs['path'], self.kwargs['keywords'], self.kwargs['glossiness'], self.kwargs['specular_strength'])
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(self.kwargs['index'], result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
            time.sleep(0.1)

    @staticmethod
    def process_nif_files(path, keywords, glossiness, specular_strength):
        success = False
        data = NifFormat.Data()

        try:
            with open(path, 'rb') as stream:
                data.read(stream)
        except Exception:
            log.exception("Error while reading stream from file : " + path)
            return success

        # First, let's get relevant NiTriShape block
        block = None
        index = 0
        try:
            root = data.roots[0]
            while not block and index < len(keywords):
                block = root.find(keywords[index])
                index += 1

            # Second, if found, change its parameters
            if block is not None:
                for subblock in block.tree():
                    if subblock.__class__.__name__ == "BSLightingShaderProperty":
                        old_gloss = subblock.glossiness
                        subblock.glossiness = glossiness
                        old_spec_strength = subblock.specular_strength
                        subblock.specular_strength = specular_strength
                        log.info("[" + path + "] ------ Glossiness " + str(old_gloss) + " -> " + str(
                            glossiness) + " | Specular Strength " + str(old_spec_strength) + " -> " + str(
                            specular_strength))
                        success = True
        except IndexError:
            pass

        if success:
            try:
                with open(path, 'wb') as stream:
                    data.write(stream)
            except Exception:
                log.exception("Error while writing to file : " + path)

        return success
