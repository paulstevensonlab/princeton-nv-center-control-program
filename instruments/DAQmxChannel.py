import PyDAQmx as pydaqmx
import numpy as np
import ctypes
import time


class DAQmxChannel:

    def __init__(self, dev, test=0):

        self.dev = dev
        self.th = pydaqmx.TaskHandle()
        if test:  # For testing, create the task. Otherwise create_task should be called in the subclass.
            self.create_task()
        self.clock_src = ''
        self.clock_edge = pydaqmx.DAQmx_Val_Rising
        self.trig_src = ''
        self.trig_edge = pydaqmx.DAQmx_Val_Rising
        self.cont_buffer_size = 100000000

        self.isTimed = False
        self.read_all_samples = False

    def create_task(self):

        self.th = pydaqmx.TaskHandle()
        pydaqmx.DAQmxCreateTask('', ctypes.byref(self.th))

    def set_sample_clock(self, src, edge, n):
        self.clock_src = src
        self.clock_edge = edge

        if n < self.cont_buffer_size:
            pydaqmx.DAQmxCfgSampClkTiming(self.th, src, 1000, edge, pydaqmx.DAQmx_Val_FiniteSamps, n)
        else:  # Use continuous sampling
            pydaqmx.DAQmxCfgSampClkTiming(self.th, src, 1000000, edge, pydaqmx.DAQmx_Val_ContSamps, self.cont_buffer_size)

        self.isTimed = True

    def set_n_sample(self, n):
        if self.clock_src == '':
            print('No Clock Src Assigned')
        else:
            self.setSampleClock(self.clock_src, self.clock_edge, n)

    def set_read_all_samples(self, b):
        pydaqmx.DAQmxSetReadReadAllAvailSamp(self.th, b)
        self.read_all_samples = b

    def set_start_trigger(self, src, edge):
        pydaqmx.DAQmxCfgDigEdgeStartTrig(self.th, src, edge)

    def set_arm_start_trigger(self, src, edge):
        # maybe we do not need this?
        pydaqmx.DAQmxSetArmStartTrigType(self.th,pydaqmx.DAQmx_Val_DigEdge)
        pydaqmx.DAQmxSetDigEdgeArmStartTrigSrc(self.th,src)
        pydaqmx.DAQmxSetDigEdgeArmStartTrigEdge(self.th,edge)

    def set_finite_samples(self, n):
        pydaqmx.DAQmxCfgImplicitTiming(self.th, pydaqmx.DAQmx_Val_FiniteSamps, n)

    def set_retriggerable(self, b):
        pydaqmx.DAQmxSetStartTrigRetriggerable(self.th, b)

    def start(self):
        pydaqmx.DAQmxStartTask(self.th)

    def stop(self):
        pydaqmx.DAQmxStopTask(self.th)
        pydaqmx.DAQmxTaskControl(self.th,pydaqmx.DAQmx_Val_Task_Unreserve)

    def wait_until_done(self):
        pydaqmx.DAQmxWaitUntilTaskDone(self.th, -1)

    def wait_until_done_thd(self, thd):
        daqmx_running = 1
        while daqmx_running != 0 and not thd.cancel:
            try:
                daqmx_running = pydaqmx.DAQmxWaitUntilTaskDone(self.th, 0)
            except:
                time.sleep(0.01)

        if thd.cancel:
            return 1
        else:
            return 0

    # def is_task_done(self):
        # int32 DAQmxIsTaskDone (TaskHandle taskHandle, bool32 *isTaskDone);

    def clear_task(self):
        pydaqmx.DAQmxClearTask(self.th)

    def reset(self):
        self.clear_task()
        self.create_task()

        self.isTimed = False

    # def __del__(self):
        # pydaqmx.DAQmxClearTask(self.th)
