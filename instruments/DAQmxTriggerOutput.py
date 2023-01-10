import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxTriggerOutput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev, trigtime=0.001):
        super().__init__(dev)
        self.trigtime = trigtime

        self.create_task()

    def create_task(self):
        super().create_task()

        pydaqmx.DAQmxCreateCOPulseChanTime(self.th, self.dev, '', pydaqmx.DAQmx_Val_Seconds, pydaqmx.DAQmx_Val_Low, 10e-6, 10e-6, self.trigtime)

    def set_time(self,t):
        self.trigtime = t
        self.reset()