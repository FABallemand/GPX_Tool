# System
import os
import logging
from pathlib import Path
from queue import Queue

# GUI
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# from PyQt5.QtCore import QThreadPool, QDir, QSortFilterProxyModel
# from PyQt5.QtWidgets import QMainWindow, QFileSystemModel

# Images
import numpy as np
from PIL import Image
import matplotlib
from mpl_toolkits.basemap import Basemap
from .figures import MatplotlibFigure

# GPX
from ezgpx import GPX

# Log and Thread
from .logger import *
from .workers import *


class Application(QMainWindow):
    
    def __init__(self):
        """
        Initialise the application
        """
        super(Application, self).__init__()
        # self.setWindowTitle("GPX Tool")

        # Multithreading attributes
        self.threadpool = QThreadPool.globalInstance()
        self.worker_queue = Queue()
        self.max_nb_threads: int = self.threadpool.maxThreadCount()
        self.nb_running_threads: int = 0

        # GPX Variables
        self.selected_path: str = ""
        self.gpx: GPX = None

        # Export Pre-processing Settings
        self.remove_gps_errors = False
        self.remove_metadata = False
        self.remove_time = False
        self.remove_elevation = False
        self.compress_data = False

        # Create GUI
        self.createGUI()

        # Show the app
        self.show()

        emitLog(Log.DEBUG, f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    ###########################################################################
    #### Signals ##############################################################
    ###########################################################################

    def signalHandler(self):
        """
        Handle signals
        """
        emitLog(Log.DEBUG, "Received SIGINT")

    ###########################################################################
    #### Worker Management ####################################################
    ###########################################################################

    def processWorkerQueue(self):
        """
        Handle worker queue, ie: attribute a worker to a thread when possible
        """
        while not self.worker_queue.empty() and self.nb_running_threads < self.max_nb_threads - 1:
            worker = self.worker_queue.get()
            self.threadpool.start(worker)
            self.nb_running_threads += 1

    def addWorker(self, worker):
        """
        Add worker to the worker queue

        Args:
            worker (Worker): Worker object used to download and parse files
                             when attributed to a thread
        """
        self.worker_queue.put(worker)
        self.processWorkerQueue()

    def workerLoadGPX(self, arg, worker=None):
        """
        Load GPX file with worker

        Parameters
        ----------
        arg : tuple
            Arguments to pass to the worker
        worker : Worker, optional
            Wroker to execute work, by default None
        """
        emitLog(Log.INFO, f"Loading GPX file: {arg}", worker)
        
        # Load GPX file
        selected_path = arg
        self.gpx = GPX(selected_path)

    def workerLoadGPXComplete(self):
        """
        Load GPX file with worker (complete)
        """
        emitLog(Log.DEBUG, "Successfully loaded GPX file")
        
        # Process worker queue
        self.processWorkerQueue()

        # Update buttons state
        self.button_export_gpx.setEnabled(True)
        self.button_export_kml.setEnabled(True)
        self.button_export_csv.setEnabled(True)

        # Update map plot
        self.createMap()

    def workerPreProcessGPX(self, arg, worker=None):
        """
        Pre-process GPX file with worker

        Parameters
        ----------
        arg : tuple
            Arguments to pass to the worker
        worker : Worker, optional
            Wroker to execute work, by default None
        """
        emitLog(Log.DEBUG, f"Pre-processing GPX file: {self.selected_path}", worker)
        
        # Pre-process GPX file
        # gpx, remove_gps_errors, remove_metadata, remove_time, remove_elevation, compress_data = arg
        if self.remove_gps_errors:
            self.gpx.remove_gps_errors()
        if self.remove_metadata:
            self.gpx.remove_metadata()
        if self.remove_time:
            self.gpx.remove_time()
        if self.remove_elevation:
            self.gpx.remove_elevation()
        if self.compress_data:
            self.gpx.simplify()

    def workerPreProcessGPXComplete(self):
        """
        Pre-process GPX file with worker (complete)
        """
        emitLog(Log.DEBUG, "Successfully pre-processed GPX file")
        
        # Process worker queue
        self.processWorkerQueue()

    def workerExportGPX(self, arg, worker=None):
        """
        Export GPX file to GPX with worker

        Parameters
        ----------
        arg : tuple
            Arguments to pass to the worker
        worker : Worker, optional
            Wroker to execute work, by default None
        """
        emitLog(Log.DEBUG, f"Export GPX file to GPX: {self.selected_path}", worker)
        
        # Export to GPX
        new_path = self.selected_path[:-4] + "_modified.gpx" # Multiple points in path? Use remove suffix instead...
        self.gpx.to_gpx(new_path)

    def workerExportGPXComplete(self):
        """
        Export GPX file to GPX with worker (complete)
        """
        emitLog(Log.DEBUG, "Successfully exported GPX file to GPX")
        
        # Process worker queue
        self.processWorkerQueue()

    def workerExportKML(self, arg, worker=None):
        """
        Export GPX file to KML with worker

        Parameters
        ----------
        arg : tuple
            Arguments to pass to the worker
        worker : Worker, optional
            Wroker to execute work, by default None
        """
        emitLog(Log.DEBUG, f"Export GPX file to KML: {self.selected_path}", worker)
        
        # Export to GPX
        new_path = self.selected_path[:-4] + ".kml" # Multiple points in path? Use remove suffix instead...
        self.gpx.to_kml(new_path)

    def workerExportKMLComplete(self):
        """
        Export GPX file to KML with worker (complete)
        """
        emitLog(Log.DEBUG, "Successfully exported GPX file to KML")
        
        # Process worker queue
        self.processWorkerQueue()

    def workerExportCSV(self, arg, worker=None):
        """
        Export GPX file to CSV with worker

        Parameters
        ----------
        arg : tuple
            Arguments to pass to the worker
        worker : Worker, optional
            Wroker to execute work, by default None
        """
        emitLog(Log.DEBUG, f"Export GPX file to CSV: {self.selected_path}", worker)
        
        # Export to GPX
        new_path = self.selected_path[:-4] + ".csv" # Multiple points in path? Use remove suffix instead...
        self.gpx.to_csv(new_path)

    def workerExportCSVComplete(self):
        """
        Export GPX file to CSV with worker (complete)
        """
        emitLog(Log.DEBUG, "Successfully exported GPX file to CSV")
        
        # Process worker queue
        self.processWorkerQueue()  

    ###########################################################################
    #### GUI ##################################################################
    ###########################################################################

    #==== Main Tab ===========================================================#

    #==== Left Part: Files Tree

    def onFilesTreeCheckboxClicked(self):
        """
        Function executed when files checkboxes are clicked
        """
        if self.checkbox_show_gpx.isChecked():
            self.sort_proxy_model.setFilterRegularExpression(r'^(.*\.gpx|[^.]+)$')
        else:
            self.sort_proxy_model.setFilterRegularExpression(r'.*$')

    def onFilesTreeClicked(self, index):
        """
        Function to execute when the tree view is clicked

        Args:
            index (...): ???
        """
        # Select file
        mapped_index = self.sort_proxy_model.mapToSource(index)
        self.selected_path = self.model.filePath(mapped_index)
        if os.path.isfile(self.selected_path):
            emitLog(Log.INFO, f"Selected file: {self.selected_path}")

            # Reset map plot
            self.resetMap()

            # Load and plot GPX
            worker = Worker(self.workerLoadGPX, arg=self.selected_path)
            worker.signals.finished.connect(self.workerLoadGPXComplete)
            worker.signals.log.connect(emitLog)
            self.addWorker(worker)

    def createFilesTree(self):
        """
        Create the GUI files tree
        """
        # Model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.model.setFilter(QDir.AllDirs | QDir.AllEntries | QDir.NoDotAndDotDot)

        # Proxy model to sort
        self.sort_proxy_model = QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.model)
        self.sort_proxy_model.setDynamicSortFilter(True)
        self.sort_proxy_model.sort(0, Qt.AscendingOrder)
        self.sort_proxy_model.setFilterRegularExpression(r'^(.*\.gpx|[^.]+)$')

        # Tree view
        self.filesTree.setModel(self.sort_proxy_model)
        self.filesTree.setRootIndex(self.sort_proxy_model.mapFromSource(self.model.index(str(Path.home()))))
        for column in range(1, self.model.columnCount()):
            self.filesTree.hideColumn(column)
        self.filesTree.clicked.connect(self.onFilesTreeClicked)

    def createLeftGUI(self):
        """
        Create the left part of the GUI (files tree)
        """
        # Files tree
        self.createFilesTree()

        # Filter checkbox
        self.checkbox_show_gpx.toggled.connect(self.onFilesTreeCheckboxClicked)
        self.checkbox_show_gpx.setChecked(True)

    #==== Center Part: Map

    def createDefaultMap(self):
        """
        Create default map (plot logo)
        """
        self.map = MatplotlibFigure(self, width=5, height=4, dpi=100)
        self.horizontalLayout_2.addWidget(self.map)
        logo = np.asarray(Image.open("img/logo.png"))
        self.map.axes.imshow(logo)
        self.map.axes.get_xaxis().set_visible(False)
        self.map.axes.get_yaxis().set_visible(False)

    def resetMap(self):
        """
        Remove the previous map and create a new default map
        """
        self.horizontalLayout_2.removeWidget(self.map)
        self.createDefaultMap()

    def createMap(self):
        """
        Remove the previous map and create a new map
        """
        # Remove the previous figure and create a new one
        self.horizontalLayout_2.removeWidget(self.map)
        self.map = MatplotlibFigure(self)
        self.horizontalLayout_2.addWidget(self.map)

        # Create dataframe containing data from the GPX file
        dataframe = self.gpx.to_dataframe(elevation=True,
                                          time=True,
                                          speed=True,
                                          pace=True,
                                          ascent_rate=True,
                                          ascent_speed=True,
                                          distance_from_start=True)
        
        # Compute track boundaries and default offset
        min_lat, min_lon, max_lat, max_lon = self.gpx.bounds()
        delta_max = max(max_lat - min_lat, max_lon - min_lon)
        offset = delta_max * 0.04
        min_lat, min_lon = max(0, min_lat - offset), max(0, min_lon - offset)
        max_lat, max_lon = min(max_lat + offset, 90),  min(max_lon + offset, 180)

        # Create map
        map = Basemap(projection="cyl",
                      llcrnrlon=min_lon,
                      llcrnrlat=min_lat,
                      urcrnrlon=max_lon,
                      urcrnrlat=max_lat,
                      ax=self.map.axes)
        # map.arcgisimage("World_Imagery")

        # Scatter track points
        color = "#FFA800"
        size = 10
        cmap = matplotlib.cm.get_cmap("viridis", 12)
        if color in ["ele", "speed", "pace", "vertical_drop", "ascent_rate", "ascent_speed"]:
            im = map.scatter(dataframe["lon"],
                             dataframe["lat"],
                             s=size,
                             c=dataframe[color],
                             cmap=cmap)
        else:
            im = map.scatter(dataframe["lon"],
                             dataframe["lat"],
                             s=size,
                             color=color)
            
        # Scatter start point with different color
        # if self.start_point_color:
        #     map.scatter(dataframe["lon"][0], dataframe["lat"][0], marker="^",
        #                 color=self.start_point_color)

        # Scatter stop point with different color
        # if self.stop_point_color:
        #     map.scatter(dataframe["lon"][-1], dataframe["lat"][-1], marker="h",
        #                 color=self.stop_point_color)

        # Scatter way points with different color
        # if self.way_points_color:
        #     for way_point in gpx.gpx.wpt:
        #         x, y = map(way_point.lon, way_point.lat) # Project way point
        #         map.scatter(x, y, marker="D",
        #                     color=self.way_points_color)      # Scatter way point

    def createCenterGUI(self):
        """
        Create the center part of the GUI (map plot)
        """
        self.createDefaultMap()

    #==== Right Part: ...

    def onRemoveGPSErrorsClicked(self):
        """
        Function executed when the "Remove GPS errors" checkbox is clicked
        """
        if self.checkbox_remove_GPS_errors.isChecked():
            self.remove_gps_errors = True
            emitLog(Log.INFO, "Remove GPS errors: ON")
        else:
            self.remove_gps_errors = False
            emitLog(Log.INFO, "Remove GPS errors: OFF")

    def onRemoveMetadataClicked(self):
        """
        Function executed when the "Remove metadata" checkbox is clicked
        """
        if self.checkbox_remove_metadata.isChecked():
            self.remove_metadata = True
            emitLog(Log.INFO, "Remove metadata: ON")
        else:
            self.remove_metadata = False
            emitLog(Log.INFO, "Remove metadata: OFF")

    def onRemoveTimeClicked(self):
        """
        Function executed when the "Remove time data" checkbox is clicked
        """
        if self.checkbox_remove_time.isChecked():
            self.remove_time = True
            emitLog(Log.INFO, "Remove time: ON")
        else:
            self.remove_time = False
            emitLog(Log.INFO, "Remove time: OFF")

    def onRemoveElevationClicked(self):
        """
        Function executed when the "Remove elevation data" checkbox is clicked
        """
        if self.checkbox_remove_elevation.isChecked():
            self.remove_elevation = True
            emitLog(Log.INFO, "Remove elevation: ON")
        else:
            self.remove_elevation = False
            emitLog(Log.INFO, "Remove elevation: OFF")

    def onCompressDataClicked(self):
        """
        Function executed when the "Compress data" checkbox is clicked
        """
        if self.checkbox_compress_data.isChecked():
            self.compress_data = True
            emitLog(Log.INFO, "Compress data: ON")
        else:
            self.compress_data = False
            emitLog(Log.INFO, "Compress data: OFF")

    def onExportGPXClicked(self):
        """
        Function executed when the "Export to GPX" button is clicked
        """
        self.button_export_gpx.setEnabled(False)
        self.button_export_kml.setEnabled(False)
        self.button_export_csv.setEnabled(False)

        # Pre-process GPX
        worker = Worker(self.workerPreProcessGPX, arg=None)
        worker.signals.finished.connect(self.workerPreProcessGPXComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        # Export to GPX
        worker = Worker(self.workerExportGPX, arg=None)
        worker.signals.finished.connect(self.workerExportGPXComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        self.button_export_gpx.setEnabled(True)
        self.button_export_kml.setEnabled(True)
        self.button_export_csv.setEnabled(True)

    def onExportKMLClicked(self):
        """
        Function executed when the "Export to KML" button is clicked
        """
        self.button_export_gpx.setEnabled(False)
        self.button_export_kml.setEnabled(False)
        self.button_export_csv.setEnabled(False)

        # Pre-process GPX
        worker = Worker(self.workerPreProcessGPX, arg=None)
        worker.signals.finished.connect(self.workerPreProcessGPXComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        # Export to KML
        worker = Worker(self.workerExportKML, arg=None)
        worker.signals.finished.connect(self.workerExportKMLComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        self.button_export_gpx.setEnabled(True)
        self.button_export_kml.setEnabled(True)
        self.button_export_csv.setEnabled(True)

    def onExportCSVClicked(self):
        """
        Function executed when the "Export to CSV" button is clicked
        """
        self.button_export_gpx.setEnabled(False)
        self.button_export_kml.setEnabled(False)
        self.button_export_csv.setEnabled(False)

        # Pre-process GPX
        worker = Worker(self.workerPreProcessGPX, arg=None)
        worker.signals.finished.connect(self.workerPreProcessGPXComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        # Export to CSV
        worker = Worker(self.workerExportCSV, arg=None)
        worker.signals.finished.connect(self.workerExportCSVComplete)
        worker.signals.log.connect(emitLog)
        self.addWorker(worker)

        self.button_export_gpx.setEnabled(True)
        self.button_export_kml.setEnabled(True)
        self.button_export_csv.setEnabled(True)

    def createRightGUI(self):
        """
        Create the right part of the GUI (progress bar, buttons and log)
        """
        # Export settings
        self.checkbox_remove_GPS_errors.toggled.connect(self.onRemoveGPSErrorsClicked)
        self.checkbox_remove_metadata.toggled.connect(self.onRemoveMetadataClicked)
        self.checkbox_remove_time.toggled.connect(self.onRemoveTimeClicked)
        self.checkbox_remove_elevation.toggled.connect(self.onRemoveElevationClicked)
        self.checkbox_compress_data.toggled.connect(self.onCompressDataClicked)

        # Export buttons
        self.button_export_gpx.clicked.connect(self.onExportGPXClicked)
        self.button_export_kml.clicked.connect(self.onExportKMLClicked)
        self.button_export_csv.clicked.connect(self.onExportCSVClicked)
        self.button_export_gpx.setEnabled(False)
        self.button_export_kml.setEnabled(False)
        self.button_export_csv.setEnabled(False)

    def createMainTab(self):
        """
        Create main tab
        """
        self.createLeftGUI()
        self.createCenterGUI()
        self.createRightGUI()

    #==== Logging Tab ====================================================#

    def createLogger(self):
        """
        Create application logger
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

    def createLogTab(self):
        """
        Create logging tab
        """
        # Log
        self.createLogger()

    #==== Read Me Tab ====================================================#

    def createReadmeTab(self):
        """
        Create README tab
        """
        # README
        text_read = self.textEdit
        text_read.setReadOnly(True)
        with open("README.md", encoding="utf8") as f:
            markdown = f.read()
            text_read.setMarkdown(markdown)

    #==== GUI ============================================================#

    def createGUI(self):
        """
        Create application Graphic User Interface (GUI)
        """
        # Load the ui file
        uic.loadUi("src/app/application.ui", self)

        # Create tabs
        self.createMainTab()
        self.createLogTab()
        self.createReadmeTab()