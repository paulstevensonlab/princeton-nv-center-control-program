import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time

from instruments import DAQmxChannel


class DAQmxAnalogInput(DAQmxChannel.DAQmxChannel):

    def __init__(self, dev, minval=-10.0, maxval=+10.0):
        super().__init__(dev)

        self.numchan = len(dev.split(','))

        self.create_task(minval=minval, maxval=maxval)

    def create_task(self, minval=-10.0, maxval=+10.0):
        super().create_task()
        pydaqmx.DAQmxCreateAIVoltageChan(self.th, self.dev, '', pydaqmx.DAQmx_Val_Diff, minval, maxval, pydaqmx.DAQmx_Val_Volts, '')

    def get_voltages(self, n):
        read = ctypes.c_int32()
        readarray = np.zeros((self.numchan*n,), dtype=np.float64)
        pydaqmx.DAQmxReadAnalogF64(self.th, n, -1, pydaqmx.DAQmx_Val_GroupByChannel, readarray, self.numchan*n, read, None)

        return readarray

if __name__ == '__main__':
    # this works in the mainexp
    import PyDAQmx as pydaqmx

    ai = instr.DAQmxAnalogInput.DAQmxAnalogInput('PXIe-6363/ai0')
    ai.set_sample_clock('PFI12', pydaqmx.DAQmx_Val_Rising, 10)
    ai.set_start_trigger('PFI13', pydaqmx.DAQmx_Val_Rising)

    ao = instr.DAQmxAnalogOutput.DAQmxAnalogOutput('PXIe-6363/ao0')
    ao.set_sample_clock('PFI12', pydaqmx.DAQmx_Val_Rising, 10)
    ao.set_start_trigger('PFI13', pydaqmx.DAQmx_Val_Rising)
    #
    ai.start()

    ao.set_voltages(np.linspace(0.5,5,10))
    ao.start()

    # time.sleep(20)

    print(ai.get_voltages(10))