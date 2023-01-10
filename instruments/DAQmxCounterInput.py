import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxCounterInput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev):
        super().__init__(dev)

        self.ext_src = ''
        self.create_task()

    def create_task(self):
        super().create_task()

        init_count = 0
        pydaqmx.DAQmxCreateCICountEdgesChan(self.th, self.dev, '', pydaqmx.DAQmx_Val_Rising, init_count, pydaqmx.DAQmx_Val_CountUp)

    def route_external_signal(self, src, dest):
        pydaqmx.DAQmxConnectTerms(src, dest, 0)

    def get_count(self):
        # numsamp=-1 for read all available, timeout=-1 for infinite wait

        val = ctypes.c_uint32()

        pydaqmx.DAQmxReadCounterScalarU32(self.th, -1, val, None)

        return val.value

    def get_counts(self, n, timeout=-1):
        n = np.uint32(n)

        if self.clock_src == '':
            print('sample clock has not been set')
            return []
        else:
            readarray = np.zeros(n, dtype=np.uint32)
            readval = ctypes.c_int32()

            if not self.read_all_samples:
                pydaqmx.DAQmxReadCounterU32(self.th, n, timeout, readarray, n, readval, None)
                if readval.value != n:
                    print('could not read all the values')
            else:
                # Read all possible samples up to n samples
                pydaqmx.DAQmxReadCounterU32(self.th, -1, timeout, readarray, n, readval, None)
                if readval.value != n:
                    # this is okay for the case of forced readout, just trim the readarray accordingly
                    readarray = readarray[:readval.value]

            return readarray

    def set_pause_trigger(self, src):
        pydaqmx.DAQmxSetDigLvlPauseTrigSrc(self.th, src)
        pydaqmx.DAQmxSetPauseTrigType(self.th, pydaqmx.DAQmx_Val_DigLvl)
        pydaqmx.DAQmxSetDigLvlPauseTrigWhen(self.th, pydaqmx.DAQmx_Val_Low)

    def set_source(self, src):
        pydaqmx.DAQmxSetCICountEdgesTerm(self.th, self.dev, src)
