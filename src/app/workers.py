import sys, traceback
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from .logger import Log

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    progress = pyqtSignal(int)
    log = pyqtSignal(Log, str)


class Worker(QRunnable):
    """
    Worker thread, inherits from QRunnable (to handle worker thread setup), signals and wrap-up.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs["parsing_argument"] = kwargs["parsing_argument"]
        self.kwargs["worker"] = self

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        # Retrieve args/kwargs and start working
        try:
            self.fn(*self.args, **self.kwargs)
        except:
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()


class Preworker(QRunnable):
    """
    Preworker thread, inherits from QRunnable (to handle worker thread setup), signals and wrap-up.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Preworker, self).__init__()
        
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs["organisms"] = kwargs["organisms"]
        self.kwargs["preworker"] = self

    @pyqtSlot()
    def run(self):
        """
        Handle preparsing.
        """
        try:
            self.fn(*self.args, **self.kwargs)
        except:
            exctype, value = sys.exc_info()[:2]
            print(exctype, value, traceback.format_exc())
            self.signals.error.emit((exctype, value, traceback.format_exc()))            