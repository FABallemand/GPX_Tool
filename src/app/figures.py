import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class MatplotlibFigure(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=16, height=9, dpi=100) -> None:
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MatplotlibFigure, self).__init__(fig)