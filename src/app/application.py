# System
import os
from pathlib import Path
from queue import Queue

# GUI
import logging
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Log and Thread
from .logger import *
from .workers import *

# GPX
from ..gpx.utils import *
from ..gpx.compress import *


class Application(QMainWindow):
    
    def __init__(self):
        """
        Initialise the application.
        """
        super(Application, self).__init__()

        # Multithreading attributes
        self.threadpool = QThreadPool.globalInstance()
        self.worker_queue = Queue()
        self.max_nb_threads = self.threadpool.maxThreadCount()
        self.nb_running_threads = 0

        # GUI attributes

        # File compression attributes
        self.selected_path = ""
        self.compression_method = ""
        self.remove_GPS_errors = False
        self.files_to_compress = []
        self.nb_files_to_compress = 0
        self.nb_compressed_files = 0
        self.start_compression_label = False

        # Create layout
        self.createLayout()

        # Create widgets
        self.createWidgets()

        # Set-up logger
        self.setUpLogger()

        # Show the app
        self.show()

        emitLog(Log.INFO, f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    #==== GUI ================================================================#

    def createLayout(self):
        """
        Create Application layout.
        """
        # Load the ui file
        uic.loadUi("src/app/application.ui", self)

        # Create layout
        self.splitter = self.findChild(QSplitter, "splitter")
        self.splitter.setStretchFactor(1, 10)

    def createWidgets(self):
        """
        Create widgets and assign a function to each widget.
        """
        # Model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.Dirs)

        # Proxy model to sort
        self.sort_proxy_model = QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.model)
        self.sort_proxy_model.setDynamicSortFilter(True)
        self.sort_proxy_model.sort(0, Qt.AscendingOrder)

        # Push button
        self.button_compress_files_state = 0
        self.button_compress_files.clicked.connect(self.onButtonClicked)

        # Tree view
        self.treeView.setModel(self.sort_proxy_model)
        self.treeView.setRootIndex(self.sort_proxy_model.mapFromSource(self.model.index(str(Path.home()))))
        for column in range(1, self.model.columnCount()):
            self.treeView.hideColumn(column)
        self.treeView.clicked.connect(self.onTreeViewClicked)

        # Radio buttons
        self.radio_button_remove_25.toggled.connect(self.onCompressMethodClicked)
        self.radio_button_remove_50.toggled.connect(self.onCompressMethodClicked)
        self.radio_button_remove_75.toggled.connect(self.onCompressMethodClicked)
        self.radio_button_RDP.toggled.connect(self.onCompressMethodClicked)
        self.radio_button_RDP.setChecked(True)

        # Check boxes
        self.checkbox_remove_GPS_errors.toggled.connect(self.onRemoveGPSErrorsChecked)

        # README
        text_read = self.textEdit
        text_read.setReadOnly(True)
        with open("README.md", encoding="utf8") as f:
            markdown = f.read()
            text_read.setMarkdown(markdown)

        # Progress bar
        self.last_nb_files_to_compress = self.nb_compressed_files
        self.las_nb_compressed_files = self.nb_files_to_compress
        self.progress_bar_label.setText(f"Parsed files: {self.nb_compressed_files}/{self.nb_files_to_compress}")

    def setUpLogger(self):
        """
        Set-up application logger.
        """
        # Log file
        self.log_file = "application.log"
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        logging.basicConfig(filename=self.log_file, encoding="utf-8", level=logging.DEBUG)

        # Log widget
        logTextBox = QPlainTextEditLogger()
        self.log.addWidget(logTextBox.widget)
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.INFO)
        logTextBox.setFormatter(CustomFormatter())

    def onButtonClicked(self):
        """
        Function executed when the "compress files" button is clicked.
        """
        if self.button_compress_files_state == 0:
            self.button_compress_files_state = 1
            self.button_compress_files.setText("Stop")
            self.startCompression()
        else:
            self.button_compress_files_state = 0
            self.button_compress_files.setText("...")
            self.stopCompression()
            self.updateProgressBar()

    def resetButton(self):
        """
        Reset button.
        """
        self.button_compress_files_state = 0
        self.button_compress_files.setText("Compress file(s)")
        self.button_compress_files.setEnabled(True)  

    def onTreeViewClicked(self, index):
        """
        Function to execute when the tree view is clicked.

        Args:
            index (...): ???
        """
        mapped_index = self.sort_proxy_model.mapToSource(index)
        self.selected_path = self.model.filePath(mapped_index)
        emitLog(Log.INFO, "Selected path: %s" % self.selected_path)

    def onCompressMethodClicked(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            self.compression_method = radio_button.text()
        emitLog(Log.INFO, f"Compression method: {self.compression_method}")

    def onRemoveGPSErrorsChecked(self):
        """
        Function executed when the "remove GPS errors" checkbox is clicked.
        """
        if self.checkbox_remove_GPS_errors.isChecked():
            self.remove_GPS_errors = True
            emitLog(Log.INFO, "Remove GPS errors: ON")
        else:
            self.remove_GPS_errors = False
            emitLog(Log.INFO, "Remove GPS errors: OFF")

    def updateProgressBar(self):
        """
        Update progress bar.
        """
        advance = self.nb_compressed_files - self.last_nb_files_to_compress
        max = self.nb_files_to_compress - self.las_nb_compressed_files

        if self.button_compress_files_state == 0:
            self.fileProgressBar.setValue(max)
            self.fileProgressBar.setMaximum(max)
            chaine = "Parsed files: " + str(max) + "/" + str(max)
            self.progress_bar_label.setText(chaine)
            self.las_nb_compressed_files = self.nb_files_to_compress
            self.last_nb_files_to_compress = self.nb_compressed_files
        else:
            self.fileProgressBar.setValue(advance)
            self.fileProgressBar.setMaximum(max)
            self.fileProgressBar.setFormat("%v / %m")
            chaine = "Parsed files: " + str(advance) + "/" + str(max)
            self.progress_bar_label.setText(chaine)
    
    def resetProgressbar(self):
        """
        Reset progress bar.
        """
        self.nb_files_to_compress = 0
        self.nb_compressed_files = 0
        self.last_nb_files_to_compress = 0
        self.las_nb_compressed_files = 0
        self.fileProgressBar.setValue(0)
        self.fileProgressBar.setMaximum(1)
        self.updateProgressBar()

    #==== Worker Handling ====================================================#

    def processWorkerQueue(self):
        """
        Handle worker queue, ie: attribute a worker to a thread when possible.
        """
        while not self.worker_queue.empty() and self.nb_running_threads < self.max_nb_threads - 1:
            worker = self.worker_queue.get()
            self.threadpool.start(worker)
            self.nb_running_threads += 1

    def addWorker(self, worker):
        """
        Add worker to the worker queue.

        Args:
            worker (Worker): Worker object used to download and parse files when attributed to a thread.
        """
        self.worker_queue.put(worker)
        self.processWorkerQueue()

    #==== Parsing ============================================================#

    def compressionWork(self, arg, worker=None):
        """
        Compress a single file.

        Args:
            arg (string): File path.
            worker (Worker, optional): Worker used to execute this function on a thread. Defaults to None.
        """
        file_path = arg
        emitLog(Log.INFO, f"Start compressing file: {file_path}", worker)

        # Open GPX file
        gpx = openGPX(file_path)

        # Remove GPS errors
        if self.remove_GPS_errors:
            gpx, _ = removeGPSErrors(gpx)

        # Compress GPX
        gpx = compressFile(gpx, self.compression_method)

        # Save result
        result_path = file_path[:-4] + "_compressed.gpx"
        saveGPX(gpx, result_path)
        emitLog(Log.INFO, f"Compressed file saved at: {result_path}")

    def workerComplete(self):
        """
        Handle worker (file compression) terminaison: start next worker, update progress bar, detect end of compression.
        """
        emitLog(Log.DEBUG, "Thread complete")
        self.nb_running_threads -= 1
        self.nb_compressed_files += 1
        self.processWorkerQueue()
        self.updateProgressBar()
        if self.worker_queue.empty() and self.nb_running_threads == 0:
            self.endOfCompression()

    def compression(self):
        """
        Handle compression of multiple files. For each file, create a Worker (that will compress a single file) and add it to the Worker queue.
        """
        if self.files_to_compress == []:
            emitLog(Log.WARNING, "No GPX file to compress...")
            self.endOfCompression()
            return
        
        emitLog(Log.DEBUG, "Starting workers to parse files...")
        self.nb_running_threads -=1
        self.start_compression_label = True
        
        t = 0
        self.nb_files_to_compress = len(self.files_to_compress)
        for file in self.files_to_compress:
            # Pass the function to execute
            # Any other args, kwargs are passed to the run function
            worker = Worker(self.compressionWork, arg=file)
            worker.signals.finished.connect(self.workerComplete)
            worker.signals.log.connect(emitLog)
            if not self.start_compression_label:
                return

            # Start the thread
            self.addWorker(worker)
            emitLog(Log.DEBUG, f"Starting thread {t}")
            t += 1
        self.start_compression_label = False

    def startCompression(self):
        """
        Start file(s) compression.
        """
        emitLog(Log.DEBUG, "Initialising compression")

        if self.selected_path == "" or not os.path.isdir(self.selected_path):
            emitLog(Log.ERROR, "Invalid path: " + self.selected_path)
            self.endOfCompression()
        # elif check self.remove_GPS_errors and self.compression_method
        else:
            if os.path.isfile(self.selected_path):
                self.files_to_compress = [self.selected_path]
            else:
                self.files_to_compress = [os.path.join(self.selected_path, file) for file in os.listdir(self.selected_path) if os.path.isfile(os.path.join(self.selected_path, file)) and file.endswith(".gpx")]
            self.resetProgressbar()
            self.compression()

    def stopCompression(self):
        """
        Stop file parsing.
        """
        self.button_compress_files.setEnabled(False)
        self.worker_queue = Queue()
        self.start_compression_label = False
        emitLog(Log.INFO, "Stop compression")

    def endOfCompression(self):
        """
        End of compression.
        """
        emitLog(Log.INFO, "Files successfully compressed!")
        self.resetButton()
        self.resetProgressbar()

    def signalHandler(self):
        """
        """
        emitLog(Log.DEBUG, "Received SIGINT")