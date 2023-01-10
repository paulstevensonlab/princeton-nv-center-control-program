import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxDigitalOutput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev):
        super().__init__(dev)
        self.create_task()
        self.write(0) #initialize to 0 on startup , later initialize to track_state?
        self.value = 0
        self.track_state = 0 #gets rewritten immediately in the instrument initialization by calling setTrackState
    def create_task(self):
        super().create_task()
        pydaqmx.DAQmxCreateDOChan(self.th, self.dev, "",pydaqmx.DAQmx_Val_ChanForAllLines) #"" = name to assign channels

    def write(self, val=0):
        pydaqmx.DAQmxStartTask(self.th)
        timeout = 10.
        autoStart = 1
        pydaqmx.DAQmxWriteDigitalLines(self.th, 1, autoStart, timeout,pydaqmx.DAQmx_Val_GroupByChannel,np.array([val], dtype='uint8'),None,None)
        pydaqmx.DAQmxStopTask(self.th)
        self.value = val
    def writeFromField(self, val=0): #ensures input is a positive integer
        if val<0:
            print('Error negative value!  Setting output to 0.')
            val = 0
        if not type(val)==int:
            print('Error not an integer!  Setting output to 0.')
            val = 0

        pydaqmx.DAQmxStartTask(self.th)
        timeout = 10.
        autoStart = 1
        pydaqmx.DAQmxWriteDigitalLines(self.th, 1, autoStart, timeout,pydaqmx.DAQmx_Val_GroupByChannel,np.array([val], dtype='uint8'),None,None)
        pydaqmx.DAQmxStopTask(self.th)
        self.value = val
    def read(self):
        return self.value

    def setTrackState(self, val):
        self.track_state = val
