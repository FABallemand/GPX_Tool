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
        self.start_parsing_label = False

        # Create layout
        self.createLayout()

        # Create widgets
        self.createWidgets()

        # Set-up logger
        self.setUpLogger()

        # Show the app
        self.show()

        emitLog(Log.INFO, "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

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
        self.button_compress_files.clicked.connect(self.onButtonClicked)
        self.button_compress_files_state = 0

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
        self.F_parsed_last = self.nb_compressed_files
        self.F_TOparsed_last = self.nb_files_to_compress
        chaine = "Parsed files: " + str(self.nb_compressed_files) + "/" + str(self.nb_files_to_compress)
        self.progress_bar_label.setText(chaine)

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
        logTextBox.setFormatter(CustomFormatter())

    def onButtonClicked(self):
        """
        Function executed when the "compress files" button is clicked.
        """
        if self.button_state == 0:
            self.button_state = 1
            self.button_compress_files.setText("Stop")
            self.startCompression()
        else:
            self.button_state = 0
            self.button_compress_files.setText("...")
            self.stopCompression()
            self.updateProgressBar()

    def resetButton(self):
        """
        Reset button.
        """
        self.button_state = 0
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
        emitLog(Log.DEBUG, "Compression method: " + str(self.compression_method))

    def onRemoveGPSErrorsChecked(self):
        """
        Function executed when the "remove GPS errors" checkbox is clicked.
        """
        if self.checkbox_remove_GPS_errors.isChecked():
            self.remove_GPS_errors = True
            emitLog(Log.DEBUG, "Rmove GPS errors: ON")
        else:
            self.remove_GPS_errors = False
            emitLog(Log.DEBUG, "Rmove GPS errors: OFF")

    def updateProgressBar(self):
        """
        Update progress bar.
        """
        advance = self.nb_compressed_files - self.F_parsed_last
        max = self.nb_files_to_compress - self.F_TOparsed_last

        if self.button_state == 0:
            self.fileProgressBar.setValue(max)
            self.fileProgressBar.setMaximum(max)
            chaine = "Parsed files: " + str(max) + "/" + str(max)
            self.progress_bar_label.setText(chaine)
            self.F_TOparsed_last = self.nb_files_to_compress
            self.F_parsed_last = self.nb_compressed_files
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
        self.F_parsed_last = 0
        self.F_TOparsed_last = 0
        self.fileProgressBar.setValue(0)
        self.fileProgressBar.setMaximum(1)

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

    def preWorkerWork(self, organisms, preworker=None):
        """
        For each organism, look for its files in the GenBank database and check if the organism needs to be parsed.
        An organism is parsed if GenBank files are newer than local files [or if there are less local files than GenBank files (organism partially parsed).](not yet implemented)
        Create a list (parsing_arguments) containing required informations for parsing (organism path, file id, organism name).

        Args:
            organisms (list): Tuples containing the name of the organism and the path to its folder.
            preworker (Preworker, optional): Preworker used to execute this function on a thread. Defaults to None.
        """
        # parsing_arguments = []

        # for organism, organism_path in organisms:
        #     emitLog(Log.INFO, "Start parsing organism: %s" % organism, preworker)
        #     ids = search.searchID(organism, worker=preworker)
        #     if ids == []:
        #         emitLog(Log.WARNING, "Did not find any NC corresponding to organism: %s" % organism, preworker)
        #         continue
        #     organism_files_to_parse = tree.needParsing(organism_path, ids, worker=preworker)
        #     emitLog(Log.INFO, "Organism %s has %d file(s) that need(s) to be parsed" % (organism, organism_files_to_parse), preworker)
        #     if organism_files_to_parse > 0:
        #         for id in ids:
        #             parsing_arguments.append((organism_path, id, organism))
        # preworker.signals.result.emit(parsing_arguments)
        pass

    def workerWork(self, parsing_argument, worker=None):
        """
        Parse a single file.

        Args:
            parsing_argument (tuple): Parsing informations (organism path, file id, organism name).
            worker (Preworker, optional): Worker used to execute this function on a thread. Defaults to None.
        """
        # organism_path, id, organism = parsing_argument
        # emitLog(Log.INFO, "Start parsing file: %s" % id, worker)
        # record = fetch.fetchFromID(id, worker=worker)
        # if record is not None:
        #     feature_parser.parseFeatures(self.region_type, organism_path, id, organism, record, worker=worker)
        pass

    def workerComplete(self):
        """
        Handle worker (file parsing) terminaison: start next worker, update progress bar, detect end of parsing.
        """
        emitLog(Log.INFO, "Thread complete")
        self.nb_running_threads -= 1
        self.nb_compressed_files += 1
        self.processWorkerQueue()
        self.updateProgressBar()
        if self.worker_queue.empty() and self.nb_running_threads == 0:
            self.endOfParsing()

    def Parsing(self, parsing_arguments):
        """
        Handle parsing of multiple files. For each file, create a Worker (that will parse a single file) and add it to the Worker queue.

        Args:
            parsing_arguments (list): List of tuples containing parsing informations (organism path, file id, organism name).
        """
        if parsing_arguments == []:
            self.endOfParsing()
            return
        
        emitLog(Log.INFO, "Starting workers to parse files...")
        self.nb_running_threads -=1
        self.start_parsing_label = True

        if not self.start_parsing_label or parsing_arguments == []:
            emitLog(Log.INFO, "End of parsing")
            self.resetButton()
            return
        
        t = 0
        self.nb_files_to_compress = len(parsing_arguments)
        for parsing_argument in parsing_arguments:
            # Pass the function to execute
            # Any other args, kwargs are passed to the run function
            worker = Worker(self.workerWork, parsing_argument=parsing_argument)
            worker.signals.finished.connect(self.workerComplete)
            worker.signals.log.connect(emitLog)
            if not self.start_parsing_label:
                return

            # Start the thread
            self.addWorker(worker)
            emitLog(Log.INFO, "Starting thread %d" % t)
            t += 1
        self.start_parsing_label = False        

    def preParsing(self, organisms):
        """
        Start a Preworker on a thread that will handle preparsing.
        Note: used to keep the GUI reponsive.

        Args:
            organisms (list): Tuples containing the name of the organism and the path to its folder.
        """
        emitLog(Log.INFO, "Start looking for files to parse...")
        pre_worker = Preworker(self.preWorkerWork, organisms=organisms)
        pre_worker.signals.result.connect(self.Parsing)
        pre_worker.signals.log.connect(emitLog)
        self.addWorker(pre_worker)

    def startCompression(self):
        """
        Start file parsing.
        """
        emitLog(Log.INFO, "Initialising parsing")

        if self.selected_path == "" or not os.path.isdir(self.selected_path):
            emitLog(Log.ERROR, "Invalid path: " + self.selected_path)
            self.resetButton()
        elif self.region_type == []:
            emitLog(Log.ERROR, "No DNA region selected")
            self.resetButton()
        else:
            self.resetProgressbar()
            emitLog(Log.INFO, "Stop parsing")
            # self.organisms_to_parse = tree.findOrganisms(self.selected_path)
            self.updateProgressBar()
            self.preParsing(self.organisms_to_parse)

    def stopCompression(self):
        """
        Stop file parsing.
        """
        self.button.setEnabled(False)
        self.worker_queue = Queue()
        self.start_parsing_label = False
        emitLog(Log.INFO, "Stop parsing")

    def signalHandler(self):
        """
        Delete all organisms files in the selected folder (self.selected_path).
        Note: Also remove files if they were created during a previous parsing. (For instance, files not needing update)
        """
        emitLog(Log.DEBUG, "Received SIGINT")
        if self.organisms_to_parse != [] and self.nb_files_to_compress - self.nb_compressed_files > 0:
            for organism, organism_path in self.organisms_to_parse:
                files = [file for file in os.listdir(organism_path) if os.path.isfile(file)]
                for file in files:
                    if os.path.exists(file):
                        os.remove(file)
                        emitLog(Log.INFO, "Successfully deleted: %s" % file)
    
    def endOfParsing(self):
        """
        End of parsing.
        """
        emitLog(Log.INFO, "End of parsing")
        self.resetButton()
        self.updateProgressBar()