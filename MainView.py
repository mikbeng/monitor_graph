import time
from datetime import datetime
from PyQt5.QtWidgets import *
from pyqtgraph.functions import mkPen

from .settings import *
from .GraphPanel import GraphPanel

from .signals import Sampler
from .helpers import available_ports

import os

class UserButton:
    def __init__(self, checked_str, unchecked_str, qboxLayout_obj, user_cb_pressed, *args):
        self.name_str = unchecked_str
        self.qbutton_obj = QPushButton(unchecked_str)
        self.user_cb_pressed = user_cb_pressed
        self.user_cb_pressed_args = args

        self.checked_str = checked_str
        self.unchecked_str = unchecked_str

        qboxLayout_obj.addWidget(self.qbutton_obj)
        self.qbutton_obj.setCheckable(True)
        self.qbutton_obj.clicked.connect(self.on_pressed)  

    def on_pressed(self, checked):

        self.qbutton_obj.setDisabled(False)

        self.user_cb_pressed(checked, *self.user_cb_pressed_args)

        if (checked):
            self.qbutton_obj.setText(self.checked_str)
        else:
            self.qbutton_obj.setText(self.unchecked_str)

class MainView(QWidget):

    def __init__(self, Ts=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.additional_save_data = None

        sampling_frequency = 1/Ts
        self.live_max_size = sampling_frequency * live_max_time

        # # # # # # # # # #
        # Setup UI
        # # # # # # # # # #
        root_layout = QHBoxLayout()
        self.setLayout(root_layout)

        # # # # # # # # # #
        # Graph Column
        # # # # # # # # # #
        live_panel = GraphPanel(framerate = framerate)
        root_layout.addWidget(live_panel)
        live_panel.hide()

        record_panel = GraphPanel(framerate = framerate)
        root_layout.addWidget(record_panel)
        record_panel.hide()

        # # # # # # # # # #
        # Control Column
        # # # # # # # # # #
        control_column = QVBoxLayout()
        root_layout.addLayout(control_column)

        # User control buttons
        self.user_controls_group = QGroupBox('Controls')
        control_column.addWidget(self.user_controls_group)

        self.buttons_layout = QVBoxLayout() # TODO change to gridlayout
        self.user_controls_group.setLayout(self.buttons_layout)


        # Graph View
        graphview_group = QGroupBox('Graph View')
        control_column.addWidget(graphview_group)
        
        graphview_vlayout = QVBoxLayout()
        graphview_group.setLayout(graphview_vlayout)
        
        graphview_hlayout = QHBoxLayout()
        graphview_vlayout.addLayout(graphview_hlayout)
        
        graphview_live_button = QPushButton("Live")
        graphview_hlayout.addWidget(graphview_live_button)
        graphview_live_button.setCheckable(True)
        graphview_live_button.clicked.connect(self.show_live_panel)
        
        graphview_record_button = QPushButton("Recorded")
        graphview_hlayout.addWidget(graphview_record_button)
        graphview_record_button.setCheckable(True)
        graphview_record_button.clicked.connect(self.show_record_panel)
        
        graphview_freeze_button = QPushButton("Freeze")
        graphview_vlayout.addWidget(graphview_freeze_button)
        graphview_freeze_button.setCheckable(True)
        graphview_freeze_button.clicked.connect(self.freeze_graphs)

        # Recording
        recording_group = QGroupBox('Recording')
        control_column.addWidget(recording_group)
        
        recording_layout = QVBoxLayout()
        recording_group.setLayout(recording_layout)

        control_seq_checkbox = QCheckBox("Enable control sig. seq.")
        recording_layout.addWidget(control_seq_checkbox)
        
        record_start_button = QPushButton("Start Recording")
        recording_layout.addWidget(record_start_button)
        record_start_button.setCheckable(True)
        record_start_button.clicked.connect(self.record)
        
        record_save_button = QPushButton("Save Recording")
        recording_layout.addWidget(record_save_button)
        record_save_button.clicked.connect(self.save)
        self.previous_filename = None

        # # # # # # # # # #
        # Misc
        # # # # # # # # # #

        # Store important UI things
        self.graphs = live_panel
        self.live_panel = live_panel
        self.record_panel = record_panel
        self.graphview_live_button = graphview_live_button
        self.graphview_record_button = graphview_record_button
        self.graphview_freeze_button = graphview_freeze_button
        self.control_seq_checkbox = control_seq_checkbox
        self.record_start_button = record_start_button
        self.record_save_button = record_save_button

        self.user_buttons = []

        # Finally, initialise ui elements
        self.graphview_live_button.click()

        self.setup_data_acquisition()


    def add_user_button(self, checked_str, unchecked_str, cb, *args):

        button = UserButton(checked_str, unchecked_str, self.buttons_layout, cb, *args)
        
        self.user_buttons.append(button)
   

    def closeEvent(self, event):
        # Close resources

        # Forward event to super class
        super().closeEvent(event)


    def setup_data_acquisition(self):

        # Clear graphs
        self.live_panel.remove_all_signals()
        self.record_panel.remove_all_signals()
        
        # Clear any record state (UI)
        self.record_start_button.setText("Start Recording")
        self.record_start_button.setChecked(False)
        self.record_save_button.setDisabled(True)
        
        # Create new Samplers (old is automatically removed by garbage collector)
        self.live_sampler = Sampler(self.live_max_size, continous = True, enabled = True)
        self.record_sampler = Sampler(record_max_size)


    def register_signal(self, sampler : Sampler, signal_handle, graph_index, name, style = mkPen({"color": "w", "width": 1})):
        self.live_panel.add_signal(graph_index, sampler.add_signal(signal_handle, name), style)
        self.record_panel.add_signal(graph_index, self.record_sampler.add_signal(signal_handle, name), style)



    def show_live_panel(self, checked):
        if (not checked):
            self.graphview_live_button.setChecked(True)
            return
        
        self.graphview_record_button.setChecked(False)
        self.live_panel.show()
        self.record_panel.hide()

    def show_record_panel(self, checked):
        if (not checked):
            self.graphview_record_button.setChecked(True)
            return
        
        self.graphview_live_button.setChecked(False)
        self.live_panel.hide()
        self.record_panel.show()
        
    def freeze_graphs(self, checked):
        if (checked):
            self.graphview_freeze_button.setText("Unfreeze")
            self.live_panel.freeze()
            self.record_panel.freeze()
        else:
            self.graphview_freeze_button.setText("Freeze")
            self.live_panel.unfreeze()
            self.record_panel.unfreeze()

    def record(self, checked):
        self.record_save_button.setDisabled(False)

        if (checked):
            self.record_sampler.clear() # If true (recording just started, clear any old data)
            self.record_start_button.setText("Stop Recording")
            if (self.control_seq_checkbox.isChecked()):
                pass   #Do some automated thing here
        else:
            self.record_start_button.setText("Start Recording")
        
        # Set enabled/disabled
        self.record_sampler.set_enabled(checked)

    def pass_additional_save_data_handle(self, io_file_handle):

        self.additional_save_data = io_file_handle

    def save_noprompt(self, folder, filename):
        #save via function call

        # If this function is called and recording is still running
        # Simulate stop recording by pressing stop record button
        if (self.record_start_button.isChecked()):
            self.record_start_button.click()
        #sleep some here in order for the previous click to take effect    
        time.sleep(1)

        if not os.path.exists(folder):
            os.makedirs(folder)

        #Save file to folder
        file_out = os.path.join(folder, (filename + ".csv"))
        
        self.record_sampler.export_to_csv(file_out)

        #Check if there is additional data to be saved
        if(self.additional_save_data != None):
            # Move to the start of the StringIO object
            self.additional_save_data.seek(0)
            
            out_file, _ = os.path.splitext(file_out)
            # Open a real file and write the contents of the StringIO object to it
            with open(out_file+'_loaddata.txt', 'w') as file:
                file.write(self.additional_save_data.getvalue())

    def save(self):
        # If save is clicked and recording is still running
        # Simulate stop recording by pressing stop record button
        if (self.record_start_button.isChecked()):
            self.record_start_button.click()

        suggested_filename = self.previous_filename
        if (suggested_filename == None): 
            suggested_filename = "sample" + datetime.now().strftime("_%Y%m%d_%H%M%S") + ".csv"


        # Prompt save dialog
        filename, _ = QFileDialog.getSaveFileName(self,
                                                  directory = suggested_filename,
                                                  filter = "CSV (*.csv);;TXT (*.txt);;Any Files (*)",
                                                  caption = "Save Sample"
        )

        # filename will be empty if dialog was cancelled
        if (filename):
            self.previous_filename = filename # Save filename for next (will also remember the right directory)
            self.record_sampler.export_to_csv(filename)

            #Check if there is additional data to be saved
            if(self.additional_save_data != None):
                # Move to the start of the StringIO object
                self.additional_save_data.seek(0)
                
                import os
                out_file, _ = os.path.splitext(filename)
                # Open a real file and write the contents of the StringIO object to it
                with open(out_file+'_loaddata.txt', 'w') as file:
                    file.write(self.additional_save_data.getvalue())



