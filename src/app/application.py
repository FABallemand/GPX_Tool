# System
import os
import logging
from pathlib import Path
from queue import Queue

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# GUI
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import matplotlib
from .figures import MatplotlibFigure

# Log and Thread
from .logger import *
from .workers import *

# GPX
from ezgpx import GPX


class Application(QMainWindow):
    
    def __init__(self):
        """
        Initialise the application.
        """
        super(Application, self).__init__()

        # Multithreading attributes
        self.threadpool = QThreadPool.globalInstance()
        self.worker_queue = Queue()
        self.max_nb_threads: int = self.threadpool.maxThreadCount()
        self.nb_running_threads: int = 0

        # File modification attributes
        self.selected_path: str = ""
        self.files_to_compress: list[str] = []
        self.nb_files_to_compress: int = 0
        self.nb_compressed_files: int = 0

        self.compression_algorithm: str = ""
        self.remove_gps_errors: bool = False
        self.remove_metadata: bool = False
        self.remove_time: bool = False
        self.remove_elevation: bool = False

        # File plot attributes
        self.color: str = ""
        self.start_stop_colors: tuple[str, str] = None
        self.way_points_color: str = None
        self.title: bool = False
        self.colorbar: bool = False
        
        self.start_modification_label: bool = False

        # Create GUI
        self.createGUI()

        # Show the app
        self.show()

        emitLog(Log.INFO, f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    #==== GUI ================================================================#

    # Left vertical layout (files tree)

    def onTreeViewClicked(self, index):
        """
        Function to execute when the tree view is clicked.

        Args:
            index (...): ???
        """
        mapped_index = self.sort_proxy_model.mapToSource(index)
        self.selected_path = self.model.filePath(mapped_index)
        emitLog(Log.INFO, "Selected path: %s" % self.selected_path)
        if os.path.isfile(self.selected_path):
            self.button_plot_file.setEnabled(True)
        else:
            self.button_plot_file.setEnabled(False)

    def createFilesTree(self):
        """
        Create the GUI files tree.
        """
        # Model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        # self.model.setFilter(QDir.NoDotAndDotDot | QDir.Dirs)
        self.model.setFilter(QDir.AllDirs | QDir.AllEntries | QDir.NoDotAndDotDot)

        # Proxy model to sort
        self.sort_proxy_model = QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.model)
        self.sort_proxy_model.setDynamicSortFilter(True)
        self.sort_proxy_model.sort(0, Qt.AscendingOrder)
        self.sort_proxy_model.setFilterRegularExpression(r'^(.*\.gpx|[^.]+)$')

        # Tree view
        self.treeView.setModel(self.sort_proxy_model)
        self.treeView.setRootIndex(self.sort_proxy_model.mapFromSource(self.model.index(str(Path.home()))))
        for column in range(1, self.model.columnCount()):
            self.treeView.hideColumn(column)
        self.treeView.clicked.connect(self.onTreeViewClicked)

    def onFilesCheckboxClicked(self):
        """
        Function executed when files checkboxes are clicked.
        """
        if self.checkbox_show_gpx.isChecked():
            self.sort_proxy_model.setFilterRegularExpression(r'^(.*\.gpx|[^.]+)$')
        else:
            self.sort_proxy_model.setFilterRegularExpression(r'.*$')

    def createLeftGUI(self):
        """
        Create the left part of the GUI (files tree).
        """
        # Files tree
        self.createFilesTree()        

        # Filter checkbox
        self.checkbox_show_gpx.toggled.connect(self.onFilesCheckboxClicked)
        self.checkbox_show_gpx.setChecked(True)

    # Center vertical layout (settings and plot)

    def onCompressionRadioButtonClicked(self):
        """
        Function to execute when compression radio buttons are clicked.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            if radio_button.text() == "None":
                self.compression_algorithm = ""
            elif radio_button.text() == "Ramer-Douglas-Peucker algorithm":
                self.compression_algorithm = "RDP"
            elif radio_button.text() == "Remove close points":
                self.compression_algorithm = "remove_close_points"
            else:
                emitLog(Log.ERROR, f"Invalid compression method: {radio_button.text()}")
        emitLog(Log.INFO, f"Compression algorithm: {self.compression_algorithm}")

    def onDataCheckboxClicked(self):
        """
        Function executed when data checkboxes are clicked.
        """
        # Remove GPS errors
        if self.checkbox_remove_GPS_errors.isChecked():
            self.remove_gps_errors = True
            emitLog(Log.INFO, "Remove GPS errors: ON")
        else:
            self.remove_gps_errors = False
            emitLog(Log.INFO, "Remove GPS errors: OFF")

        # Remove metadata
        if self.checkbox_remove_metadata.isChecked():
            self.remove_metadata = True
            emitLog(Log.INFO, "Remove metadata: ON")
        else:
            self.remove_metadata = False
            emitLog(Log.INFO, "Remove metadata: OFF")

        # Remove time
        if self.checkbox_remove_time.isChecked():
            self.remove_time = True
            emitLog(Log.INFO, "Remove time: ON")
        else:
            self.remove_time = False
            emitLog(Log.INFO, "Remove time: OFF")

        # Remove elevation
        if self.checkbox_remove_elevation.isChecked():
            self.remove_elevation = True
            emitLog(Log.INFO, "Remove elevation: ON")
        else:
            self.remove_elevation = False
            emitLog(Log.INFO, "Remove elevation: OFF")

    def onPlotRadioButtonClicked(self):
        """
        Function to execute when plot radio buttons are clicked.
        """
        radio_button = self.sender()
        if radio_button.isChecked():
            if radio_button.text() == "None":
                self.color = "#0F0F0F"
            elif radio_button.text() == "Plot elevation":
                self.color = "elevation"
            elif radio_button.text() == "Plot speed":
                self.color = "speed"
            elif radio_button.text() == "Plot pace":
                self.color = "pace"
            elif radio_button.text() == "Plot ascent rate":
                self.color = "ascent_rate"
            elif radio_button.text() == "Plot ascent speed":
                self.color = "ascent_speed"
            else:
                emitLog(Log.ERROR, f"Invalid plot method: {radio_button.text()}")

    def onPlotCheckboxClicked(self):
        """
        Function executed when plot checkboxes are clicked.
        """
        # Plot start/stop points
        if self.checkbox_plot_start_stop_points.isChecked():
            self.start_stop_colors = ("#00FF00", "#FF0000")
            emitLog(Log.INFO, "Plot start/stop points: ON")
        else:
            self.start_stop_colors = None
            emitLog(Log.INFO, "Plot start/stop points: OFF")

        # Plot way points
        if self.checkbox_plot_way_points.isChecked():
            self.way_points_color = "#0000FF"
            emitLog(Log.INFO, "Plot way points: ON")
        else:
            self.way_points_color = None
            emitLog(Log.INFO, "Plot way points: OFF")

        # Plot title
        if self.checkbox_plot_title.isChecked():
            self.title = True
            emitLog(Log.INFO, "Plot title: ON")
        else:
            self.title = False
            emitLog(Log.INFO, "Plot title: OFF")

        # Remove elevation
        if self.checkbox_plot_colorbar.isChecked():
            self.colorbar = True
            emitLog(Log.INFO, "Plot colorbar: ON")
        else:
            self.colorbar = False
            emitLog(Log.INFO, "Plot colorbar: OFF")

    def createCenterGUI(self):
        """
        Create the center part of the GUI (settings and plot).
        """
        # Compression settings
        self.radio_button_none_compress.toggled.connect(self.onCompressionRadioButtonClicked)
        self.radio_button_remove_close.toggled.connect(self.onCompressionRadioButtonClicked)
        self.radio_button_RDP.toggled.connect(self.onCompressionRadioButtonClicked)
        self.radio_button_none_compress.setChecked(True)

        # Data settings
        self.checkbox_remove_GPS_errors.toggled.connect(self.onDataCheckboxClicked)
        self.checkbox_remove_metadata.toggled.connect(self.onDataCheckboxClicked)
        self.checkbox_remove_time.toggled.connect(self.onDataCheckboxClicked)
        self.checkbox_remove_elevation.toggled.connect(self.onDataCheckboxClicked)

        # Plot settings
        self.radio_button_none_plot.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_elevation.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_speed.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_pace.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_ascent_rate.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_ascent_speed.toggled.connect(self.onPlotRadioButtonClicked)
        self.radio_button_none_plot.setChecked(True)
        self.checkbox_plot_start_stop_points.toggled.connect(self.onPlotCheckboxClicked)
        self.checkbox_plot_way_points.toggled.connect(self.onPlotCheckboxClicked)
        self.checkbox_plot_title.toggled.connect(self.onPlotCheckboxClicked)
        self.checkbox_plot_colorbar.toggled.connect(self.onPlotCheckboxClicked)

        # Map
        self.map = MatplotlibFigure(self, width=5, height=4, dpi=100)
        self.horizontalLayout_2.addWidget(self.map)
        logo = np.asarray(Image.open("img/logo.png"))
        self.map.axes.imshow(logo)
        self.map.axes.get_xaxis().set_visible(False)
        self.map.axes.get_yaxis().set_visible(False)

    # Right vertical layout (progress bar, buttons and log)

    def updateProgressBar(self):
        """
        Update progress bar.
        """
        advance = self.nb_compressed_files - self.last_nb_files_to_compress
        max = self.nb_files_to_compress - self.las_nb_compressed_files

        if self.button_modify_files_state == 0:
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

    def onModifyButtonClicked(self):
        """
        Function executed when the "Modify files" button is clicked.
        """
        if self.button_modify_files_state == 0:
            self.button_modify_files_state = 1
            self.button_modify_files.setText("Stop")
            self.startModification()
        else:
            self.button_modify_files_state = 0
            self.button_modify_files.setText("...")
            self.stopGpxModification()
            self.updateProgressBar()

    def resetModifyButton(self):
        """
        Reset modify button.
        """
        self.button_modify_files_state = 0
        self.button_modify_files.setText("Modify file(s)")
        self.button_modify_files.setEnabled(True)

    def onPlotButtonClicked(self):
        """
        Function executed when the "Plot file" button is clicked.
        """
        # Remove the previous Matplotlib figure and create a new one
        self.horizontalLayout_2.removeWidget(self.map)
        self.map = MatplotlibFigure(self, width=5, height=4, dpi=100)
        self.horizontalLayout_2.addWidget(self.map)

        gpx = GPX(self.selected_path)
        gpx.matplotlib_axes_plot(self.map.axes,
                                 color=self.color,
                                 colorbar=self.colorbar,
                                 start_stop_colors=self.start_stop_colors,
                                 way_points_color=self.way_points_color,
                                 title=gpx.name() if self.title else None)
        # self.map.hide()
        # self.map.show()

    def createLogger(self):
        """
        Create application logger.
        """
        # Log file
        self.log_file = "application.log"
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        logging.basicConfig(filename=self.log_file,
                            encoding="utf-8",
                            level=logging.DEBUG)

        # Log widget
        logTextBox = QPlainTextEditLogger()
        self.log.addWidget(logTextBox.widget)
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.INFO)
        logTextBox.setFormatter(CustomFormatter())

    def createRightGUI(self):
        """
        Create the right part of the GUI (progress bar, buttons and log).
        """
        # Progress bar
        self.last_nb_files_to_compress = self.nb_compressed_files
        self.las_nb_compressed_files = self.nb_files_to_compress
        self.progress_bar_label.setText(f"Parsed files: {self.nb_compressed_files}/{self.nb_files_to_compress}")

        # Modify button
        self.button_modify_files_state = 0
        self.button_modify_files.clicked.connect(self.onModifyButtonClicked)

        # Plot button
        self.button_plot_state = 0
        self.button_plot_file.clicked.connect(self.onPlotButtonClicked)
        self.button_plot_file.setEnabled(False)

        # Log
        self.createLogger()

    # Tabs

    def createMainTab(self):
        """
        Create main tab.
        """
        self.createLeftGUI()
        self.createCenterGUI()
        self.createRightGUI()

    def createReadmeTab(self):
        """
        Create README tab.
        """
        # README
        text_read = self.textEdit
        text_read.setReadOnly(True)
        with open("README.md", encoding="utf8") as f:
            markdown = f.read()
            text_read.setMarkdown(markdown)

    # GUI

    def createGUI(self):
        """
        Create application Graphic User Interface (GUI).
        """
        # Load the ui file
        uic.loadUi("src/app/application.ui", self)

        # Create tabs
        self.createMainTab()
        self.createReadmeTab()        

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
            worker (Worker): Worker object used to download and parse files
                             when attributed to a thread.
        """
        self.worker_queue.put(worker)
        self.processWorkerQueue()

    #==== Parsing ============================================================#

    def GpxModificationWork(self, arg, worker=None):
        """
        Modify a single file.

        Args:
            arg (string): File path.
            worker (Worker, optional): Worker used to execute this function on
                                       a thread. Defaults to None.
        """
        file_path = arg
        emitLog(Log.INFO, f"Start modifying file: {file_path}", worker)

        # Open GPX file
        emitLog(Log.INFO, f"Reading GPX file: {file_path}", worker)
        gpx = GPX(file_path)
        
        # Remove GPS errors
        if self.remove_gps_errors:
            emitLog(Log.INFO, f"Removing GPS errors in file: {file_path}", worker)
            gpx.remove_gps_errors()

        # Remove metadata
        if self.remove_metadata:
            emitLog(Log.INFO, f"Removing metadata in file: {file_path}", worker)
            gpx.remove_metadata()

        # Remove time data
        if self.remove_time:
            emitLog(Log.INFO, f"Removing time data in file: {file_path}", worker)
            gpx.remove_time()

        # Remove elevation data
        if self.remove_elevation:
            emitLog(Log.INFO, f"Removing elevation data in file: {file_path}", worker)
            gpx.remove_elevation()

        # Compress GPX
        if self.compression_algorithm == "RDP":
            emitLog(Log.INFO, f"Simplifying file: {file_path}", worker)
            gpx.simplify()
        elif self.compression_algorithm == "remove_close_points":
            emitLog(Log.INFO, f"Removing points in file: {file_path}", worker)
            gpx.remove_close_points()

        # Save result
        result_path = file_path[:-4] + "_modified.gpx"
        gpx.to_gpx(result_path)
        emitLog(Log.INFO, f"Modified file saved at: {result_path}", worker)

    def GpxModificationWorkComplete(self):
        """
        Handle worker (GPX file modification) terminaison: start next worker,
        update progress bar, detect end of compression.
        """
        emitLog(Log.DEBUG, "Thread complete")
        self.nb_running_threads -= 1
        self.nb_compressed_files += 1
        self.processWorkerQueue()
        self.updateProgressBar()
        if self.worker_queue.empty() and self.nb_running_threads == 0:
            self.GpxModificationWorkEnd()

    def GpxModification(self):
        """
        Handle modification of multiple files. For each file, create a Worker
        (that will modify a single file) and add it to the Worker queue.
        """
        if self.files_to_compress == []:
            emitLog(Log.WARNING, "No GPX file to modify...")
            self.GpxModificationWorkEnd()
            return
        
        emitLog(Log.DEBUG, "Starting workers to modify files...")
        self.nb_running_threads = 0
        self.start_modification_label = True
        
        self.nb_files_to_compress = len(self.files_to_compress)
        for file in self.files_to_compress:
            # Pass the function to execute
            # Any other args, kwargs are passed to the run function
            worker = Worker(self.GpxModificationWork, arg=file)
            worker.signals.finished.connect(self.GpxModificationWorkComplete)
            worker.signals.log.connect(emitLog)
            if not self.start_modification_label:
                return

            # Start the thread
            self.addWorker(worker)
            emitLog(Log.DEBUG, f"Starting thread {self.nb_running_threads}")
        self.start_modification_label = False

    def startModification(self):
        """
        Start file(s) modification.
        """
        emitLog(Log.DEBUG, "Initialising modification")

        if not os.path.exists(self.selected_path):
            emitLog(Log.ERROR, "Invalid path: " + self.selected_path)
            self.GpxModificationWorkEnd()
        else:
            if os.path.isfile(self.selected_path):
                self.files_to_compress = [self.selected_path]
            else:
                self.files_to_compress = [os.path.join(self.selected_path, file) for file in os.listdir(self.selected_path) if os.path.isfile(os.path.join(self.selected_path, file)) and file.endswith(".gpx")]
            self.resetProgressbar()
            self.GpxModification()

    def stopGpxModification(self):
        """
        Stop GPX files modification.
        """
        self.button_modify_files.setEnabled(False)
        self.worker_queue = Queue()
        self.start_modification_label = False
        emitLog(Log.INFO, "Stop modification")

    def GpxModificationWorkEnd(self):
        """
        End of GPX files modification.
        """
        emitLog(Log.INFO, "Files successfully modified!")
        self.resetModifyButton()
        self.resetProgressbar()

    def signalHandler(self):
        """
        Handle signals.
        """
        emitLog(Log.DEBUG, "Received SIGINT")