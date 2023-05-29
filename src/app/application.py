# System
import os
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

        # Create layout
        self.createLayout()

        # Create widgets
        self.createWidgets()

        # Set-up logger
        self.setUpLogger()

        # Show the app
        self.show()

        # emitLog(Log.INFO, "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

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
        self.button = self.findChild(QPushButton, "pushButton")
        self.button.clicked.connect(self.onButtonClicked)
        self.button_state = 0

        # Tree view
        self.treeView.setModel(self.sort_proxy_model)
        self.treeView.setRootIndex(self.sort_proxy_model.mapFromSource(
            self.model.index(os.path.join(QDir.currentPath(), "Results"))))
        for column in range(1, self.model.columnCount()):
            self.treeView.hideColumn(column)
        self.treeView.clicked.connect(self.onTreeViewClicked)

        # Check boxes
        self.checkboxes = [self.CDS, self.CENTRO, self.INTRON, self.MOBILE, self.NC_RNA, self.R_RNA, self.TELOMETRE, self.T_RNA, self.UTR_3, self.UTR_5, self.ALL, self.NONE]
        self.all_checked = False
        self.none_checked = False
        for checkbox in self.checkboxes:
            checkbox.toggled.connect(self.onChecked)
        self.NONE.toggled.connect(self.onChecked_NONE)
        self.ALL.toggled.connect(self.onChecked_ALL)

        # README
        text_read = self.textEdit
        text_read.setReadOnly(True)
        with open("README.md", encoding="utf8") as f:
            markdown = f.read()
            text_read.setMarkdown(markdown)

        # Progress bar
        self.F_parsed_last = self.nb_parsed_files
        self.F_TOparsed_last = self.nb_files_to_parse
        chaine = "Parsed files: " + str(self.nb_parsed_files) + "/" + str(self.nb_files_to_parse)
        self.progress_bar_label.setText(chaine)

    def setUpLogger(self):
        """
        Set-up application logger.
        """
        # Log file
        self.log_file = "application.log"
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        logging.basicConfig(filename=self.log_file, encoding="utf-8", level=logging.INFO)

        # Log widget
        self.logger_box = self.findChild(QFormLayout, "formLayout_6")
        logTextBox = QPlainTextEditLogger()
        self.logger_box.addWidget(logTextBox.widget)
        logging.getLogger().addHandler(logTextBox)
        logTextBox.setFormatter(CustomFormatter())

    def onTreeViewClicked(self, index):
        """
        Function to execute when the tree view is clicked.

        Args:
            index (...): ???
        """
        mapped_index = self.sort_proxy_model.mapToSource(index)
        self.selected_path = self.model.filePath(mapped_index)
        emitLog(Log.INFO, "Selected path: %s" % self.selected_path)

    def updateProgressBar(self):
        """
        Update progress bar.
        """
        advance = self.nb_parsed_files - self.F_parsed_last
        max = self.nb_files_to_parse - self.F_TOparsed_last

        if self.button_state == 0:
            self.fileProgressBar.setValue(max)
            self.fileProgressBar.setMaximum(max)
            chaine = "Parsed files: " + str(max) + "/" + str(max)
            self.progress_bar_label.setText(chaine)
            self.F_TOparsed_last = self.nb_files_to_parse
            self.F_parsed_last = self.nb_parsed_files
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
        self.nb_files_to_parse = 0
        self.nb_parsed_files = 0
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
        parsing_arguments = []

        for organism, organism_path in organisms:
            emitLog(Log.INFO, "Start parsing organism: %s" % organism, preworker)
            ids = search.searchID(organism, worker=preworker)
            if ids == []:
                emitLog(Log.WARNING, "Did not find any NC corresponding to organism: %s" % organism, preworker)
                continue
            organism_files_to_parse = tree.needParsing(organism_path, ids, worker=preworker)
            emitLog(Log.INFO, "Organism %s has %d file(s) that need(s) to be parsed" % (organism, organism_files_to_parse), preworker)
            if organism_files_to_parse > 0:
                for id in ids:
                    parsing_arguments.append((organism_path, id, organism))
        preworker.signals.result.emit(parsing_arguments)

    def workerWork(self, parsing_argument, worker=None):
        """
        Parse a single file.

        Args:
            parsing_argument (tuple): Parsing informations (organism path, file id, organism name).
            worker (Preworker, optional): Worker used to execute this function on a thread. Defaults to None.
        """
        organism_path, id, organism = parsing_argument
        emitLog(Log.INFO, "Start parsing file: %s" % id, worker)
        record = fetch.fetchFromID(id, worker=worker)
        if record is not None:
            feature_parser.parseFeatures(self.region_type, organism_path, id, organism, record, worker=worker)

    def workerComplete(self):
        """
        Handle worker (file parsing) terminaison: start next worker, update progress bar, detect end of parsing.
        """
        emitLog(Log.INFO, "Thread complete")
        self.nb_running_threads -= 1
        self.nb_parsed_files += 1
        self.processWorkerQueue()
        self.updateProgressBar()
        if self.worker_queue.empty() and self.nb_running_threads == 0:
            self.endOfParsing()

    def signalHandler(self):
        """
        Delete all organisms files in the selected folder (self.selected_path).
        Note: Also remove files if they were created during a previous parsing. (For instance, files not needing update)
        """
        emitLog(Log.DEBUG, "Received SIGINT")
        if self.organisms_to_parse != [] and self.nb_files_to_parse - self.nb_parsed_files > 0:
            for organism, organism_path in self.organisms_to_parse:
                files = [file for file in os.listdir(organism_path) if os.path.isfile(file)]
                for file in files:
                    if os.path.exists(file):
                        os.remove(file)
                        emitLog(Log.INFO, "Successfully deleted: %s" % file)