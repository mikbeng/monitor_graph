from PyQt5 import QtWidgets as qtw
import sys
import time
import numpy as np
from pyqtgraph.functions import mkPen

from .MainView import MainView
from .signals import SignalHandle
from .settings import *


class Panel():  
    def __init__(self, name, live_index, rec_index):
        self.live_index = live_index
        self.record_index = rec_index
        self.name = name

class Variable():

    width_default = 1

    colours = {
        "white": mkPen({"color": "w", "width": width_default}),
        "cyan": mkPen({"color": (20,174,242), "width": width_default}),
        "cyan_dotted": mkPen({"color": (20,174,242), "width": 5, "style": 3}),
        "grass": mkPen({"color": (23,187,119), "width": width_default}),
        "moss": mkPen({"color": (54, 139, 133), "width": width_default}),
        "pink": mkPen({"color": (245,108,142), "width": width_default}),
        "pink_thick": mkPen({"color": (245,108,142), "width": width_default}),
        "sun": mkPen({"color": (255, 228, 89), "width": width_default}),
    }

    def __init__(self,signal_handle, name, graph_panel : Panel, style):

        self.signal_handle : SignalHandle = signal_handle
        self.name = name
        self.graph_panel = graph_panel
        self.value = 0
        self.timestamp = time.time()
        self.style = style

        self.getter_func = None

    def assign_getter_func(self, getter_func):
        self.getter_func = getter_func

    def update_value_func(self):
        if self.getter_func() != None:
            self.value, self.timestamp = self.getter_func()
            return self.value, self.timestamp
        else:
            print("No getter_func assigned")



class Monitor():
    def __init__(self,Ts_plot):

        self._buffer_size = buffer_size

        self.var_dict = {}

        self.time_start = time.time()

        self.app = qtw.QApplication(sys.argv)
        self.screen = self.app.primaryScreen()
        self.size = self.screen.size()
        self.width = self.size.width()
        self.height = self.size.height()
        self.view = MainView(Ts = Ts_plot)
        self.app_width = 1300
        self.app_height = self.height - 200
        self.pos_x = self.width - self.app_width
        self.view.setGeometry(self.pos_x, 100, self.app_width, self.app_height)

        #self.add_button_with_cb("start", "stop", monitor_button_cb, None)

    def add_button_with_cb(self, checked_str, unchecked_str, cb, *args):
        self.view.add_user_button(checked_str, unchecked_str, cb, *args)

    def add_user_save_file_on_save(self, io_file_handle):
        self.view.pass_additional_save_data_handle(io_file_handle)

    def start_recording(self):
        if(self.view.record_start_button.isChecked()):
            print("recording already started!")
        else:
            self.view.record_start_button.click()

    def stop_recording(self):
        if(self.view.record_start_button.isChecked()):
            self.view.record_start_button.click()
        else:
            print("recording already started!")
            

    def show(self):
        # self.view.live_sampler.clear() # If true (recording just started, clear any old data)
        # self.view.live_sampler.set_enabled(True)
        self.view.show()
        

    def create_graph_panel(self, name):
        index_live = self.view.live_panel.create_graph(name)
        index_record = self.view.record_panel.create_graph(name)

        panel = Panel(name,index_live,index_record)
        return panel


    def add_variable(self, name, style, graph_panel: Panel) -> Variable:

        signal_handle = SignalHandle()

        var = Variable(signal_handle, name, graph_panel, style)

        self.view.register_signal(self.view.live_sampler, var.signal_handle, var.graph_panel.live_index, var.name, var.style)

        self.var_dict[var.name] = var 
        #self.var_dict[name] = var
        return var

    def update_plot(self):
        for key, var in self.var_dict.items():
            if var.getter_func != None:
                var.update_value_func()

            var.signal_handle.commit_data(np.vstack((var.timestamp - self.time_start, var.value)))
        
        
        # for i in range(N):
        #     if self.var_list[i].getter_func != None:
        #         self.var_list[i].update_value_func()

        #     if self.var_list[i].get_timestamp_func != None:
        #         self.var_list[i].update_timestamp_func()

        #     self.var_list[i].signal_handle.commit_data(np.vstack((self.var_list[i].timestamp - self.time_start, self.var_list[i].value)))
        #     #self._signal_handles[i].commit_data( np.vstack((time_vector, self._analog_converters[i](data))) )

