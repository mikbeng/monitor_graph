from PyQt5.QtWidgets import *
from pyqtgraph import PlotWidget, plot, mkPen, setConfigOption

from PyQt5 import QtCore as qtc
from pyqtgraph.functions import mkColor

from .settings import *


class GraphPanel(QWidget):
    
    def __init__(self, framerate = None):
        super().__init__()

        self._signalines = []
        self._signaldatas = []

        if framerate is None:
            framerate = framerate

        # Setup this widget/layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setSpacing(0)
        
        # Setup automatic update/refresh
        self._timer = qtc.QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update)
        self._timer.start()

        # # # # # # # # # #
        # Graphs
        # # # # # # # # # #
        self.graphs = [] # TODO this should be created in the _create_graph() function if self.graphs is None


    def create_graph(self, name, last_graph = False):
        graph = PlotWidget()
        self.layout.addWidget(graph)
        graph.showGrid(x=True, y=True)
        graph.getAxis("left").setWidth(80)
        graph.getAxis("left").setLabel(name)
        graph.getAxis("bottom").setHeight(50)
        graph.getAxis("bottom").setLabel("Time [s]")
        graph.addLegend()

        self.graphs.append(graph)

        if last_graph==True:
            last_graph = self.graphs[-1] 
            last_graph.getAxis("bottom").setLabel("Time [s]")
            return len(self.graphs)-1
        else:
            return len(self.graphs)-1

    def freeze(self):
        self._timer.stop()

    def unfreeze(self):
        self._timer.start()

    def update(self):
        for i in range(len(self._signaldatas)):
            data = self._signaldatas[i].get_data()
            self._signalines[i].setData(data[0, :], data[1, :])

    def add_signal(self, graph_index, signaldata, style=mkPen({"color": "w", "width": 1})):
        self._signalines.append(self.graphs[graph_index].plot(name=signaldata.get_name(), pen=style))
        self._signaldatas.append(signaldata)
    
    def remove_all_signals(self):
        self._signalines.clear()
        self._signaldatas.clear()

        for graph in self.graphs:
            graph.clear()
