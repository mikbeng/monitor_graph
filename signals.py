import numpy as np
from numpy_ringbuffer import RingBuffer

class SlightlyBetterRingBuffer(RingBuffer):

    def clear(self):
        for _ in range(len(self)):
            self.pop()
    
    def extend(self, data):
        super().extend(data.T)
    
    def get_data(self):
        return np.array(self).T

class SignalHandle():
    def __init__(self):
        self.callback_methods = []
        self.clear_methods = []

    def add_listener(self, callback_method, clear_method = None):
        self.callback_methods.append(callback_method)
        self.clear_methods.append(clear_method)

    def commit_data(self, data):
        for callback_method in self.callback_methods:
            callback_method(data)
    
    def clear_data(self):
        for clear_method in self.clear_methods:
            if (clear_method is not None): clear_method()

class DerivativeSignalHandle(SignalHandle):
    def __init__(self, signal_handle):
        super().__init__()
        self._previous_value = None

        # Register to "primitive signal handle"
        signal_handle.add_listener(self.commit_data, self.clear_data)

    def commit_data(self, data):
        if (self._previous_value is None):
            self._previous_value = np.full((data.shape[0], 1), np.nan)

        derivative_data = np.diff(data[1:, :], prepend = self._previous_value[1:, :]) / np.diff(data[0, :], prepend = self._previous_value[0, :])
        super().commit_data(np.vstack( (data[0, :], derivative_data) ))
            
        self._previous_value = np.array([ data[:, -1] ]).T
    
    def clear_data(self):
        super().clear_data()
        self._previous_value = None

class SignalData():
    
    def __init__(self, size, signal_handle, name = "", allow_overwrite = False, enabled = True):
        self._name = name

        # Create ringbuffer for storing the signal data
        self._enabled = enabled
        self._data = SlightlyBetterRingBuffer(round(size), dtype = (np.double, 2), allow_overwrite = allow_overwrite)
        
        # Register callback to signal handle
        signal_handle.add_listener(self._data_callback, self._clear)

    def _data_callback(self, data):
        if (self._enabled):
            self._data.extend(data)

    def set_enabled(self, enabled):
        self._enabled = enabled
    
    def get_data(self):
        return self._data.get_data()
    
    def clear(self):
        self._data.clear()

    def _clear(self):
        if (self._enabled):
            self.clear()
    
    def get_name(self):
        return self._name

class Sampler():

    def __init__(self, size, continous = False, enabled = False):
        self.size = size
        self.continous = continous
        self.signaldatas = []

        self.enabled = enabled

    def clear(self):
        for signaldata in self.signaldatas:
            signaldata.clear()

    def set_enabled(self, enabled):
        self.enabled = enabled

        for signaldata in self.signaldatas:
            signaldata.set_enabled(enabled)

    def add_signal(self, signal_handle, name):
        signaldata = SignalData(self.size, signal_handle, name = name, allow_overwrite = self.continous, enabled = self.enabled)
        self.signaldatas.append(signaldata)

        return signaldata

    def _combine_data(self):
        N = len(self.signaldatas)
        nr_var_total = N
        nr_samp_total = 0

        for i in range(N):
            temp = self.signaldatas[i].get_data()
            nr_samp_total += temp.shape[1]
            #nr_samp_total += self.signaldatas[i].get_data()
        
        #print("Variables: ", nr_var_total, "\t Samples: ", nr_samp_total)
        datamatrix = np.full((nr_var_total+1,nr_samp_total), np.nan) # +1 is time

        r = 1
        c = 0
        for i in range(N):
            vec = self.signaldatas[i].get_data()
            nr_samples = vec.shape[1]
            nr_variables = 1

            time = vec[0, :]
            data = vec[1, :]

            datamatrix[0, c:(c+nr_samples)] = time
            datamatrix[r:(r+nr_variables), c:(c+nr_samples)] = data

            c += nr_samples
            r += nr_variables

        # TODO change orientation of matrix from start....
        datamatrix = datamatrix[:,:].transpose()
        return datamatrix

    def export_to_csv(self, filename):
        matrix = self._combine_data()

        # Save to csv file
        delimiter = ","
        header = ["Time"] + [signaldata.get_name() for signaldata in self.signaldatas]
        np.savetxt(filename, matrix, delimiter=delimiter, header=delimiter.join(header), comments="")