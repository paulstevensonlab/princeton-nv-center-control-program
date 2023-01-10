import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxCounterOutput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev, freq=1000):
        super().__init__(dev)
        self.freq = freq

        self.create_task()

    def create_task(self):
        super().create_task()

        delay = 0
        duty = 0.5
        pydaqmx.DAQmxCreateCOPulseChanFreq(self.th, self.dev, '', pydaqmx.DAQmx_Val_Hz, pydaqmx.DAQmx_Val_Low, delay, self.freq, duty)
        pydaqmx.DAQmxCfgImplicitTiming(self.th,pydaqmx.DAQmx_Val_ContSamps,1000)

    def set_freq(self,freq):
        # (todo) warning if task is running
        self.clear_task()
        self.freq = freq
        self.create_task()
