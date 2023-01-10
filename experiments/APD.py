from PyQt5.QtCore import pyqtSignal
import time
import numpy as np
import PyDAQmx
import warnings

from . import ExpThread


class LiveAPD(ExpThread.ExpThread):

    signal_liveapd_updateplots = pyqtSignal(float, float)
    signal_liveapd_grab_screenshots = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        self.signal_liveapd_updateplots.connect(mainexp.liveapd_updateplots)
        self.signal_liveapd_grab_screenshots.connect(mainexp.liveapd_grab_screenshots)

    def update(self):
        acqtime = self.mainexp.dbl_liveapd_acqtime.value()
        pl = self.get_countrate(acqtime)

        self.signal_liveapd_updateplots.emit(acqtime, pl)

    def get_countrate(self, acqtime):
        self.mainexp.ctrapd.start()
        self.mainexp.ctrtrig.set_time(acqtime)
        self.mainexp.ctrtrig.start()
        self.mainexp.ctrtrig.wait_until_done()
        self.mainexp.ctrtrig.stop()
        val = self.mainexp.ctrapd.get_count() / acqtime
        self.mainexp.ctrapd.stop()

        return val

    def run(self):
        self.mainexp.set_gui_btn_enable('all', False)
        self.mainexp.set_gui_btn_enable('tracker', True)
        self.mainexp.set_gui_input_enable('tracker', True)
        self.mainexp.btn_liveapd_stop.setEnabled(True)
        self.mainexp.btn_liveapd_clear.setEnabled(True)
        self.mainexp.btn_nvlist_add.setEnabled(True)
        self.mainexp.btn_seqapd_start.setEnabled(False)

        self.mainexp.ctrapd.reset()
        self.mainexp.ctrtrig.reset()
        self.mainexp.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.mainexp.ctrapd.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'])


        self.cancel = False
        while not self.cancel:
            self.update()

        self.mainexp.galpie.reset()
        self.mainexp.ctrapd.reset()
        self.mainexp.ctrclk.reset()
        self.mainexp.ctrtrig.reset()


    def save(self):
        if self.isRunning():
            self.signal_liveapd_grab_screenshots.emit()
            self.wait_for_mainexp()
        else:
            self.mainexp.liveapd_grab_screenshots()

        time.sleep(0.1)

        graph = self.mainexp.pixmap_liveapd_graph
        filename = 'PLtime_%d' % self.mainexp.wavenum
        data_dict = {'pl': self.mainexp.liveapd_pl, 'xvals': self.mainexp.liveapd_t}

        self.save_data(filename, data_dict, graph=graph, fig=graph)


class SeqAPD(ExpThread.ExpThread):

    signal_seqapd_updateplots = pyqtSignal()
    signal_seqapd_grab_screenshots = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)
        self.mainexp = mainexp

        self.signal_seqapd_updateplots.connect(mainexp.seqapd_updateplots)
        self.signal_seqapd_grab_screenshots.connect(mainexp.seqapd_grab_screenshots)

    def run(self):
        self.cancel = False
        self.mainexp.set_gui_btn_enable('all', False)
        self.mainexp.btn_seqapd_start.setEnabled(False)
        self.mainexp.btn_seqapd_stop.setEnabled(True)

        self.mainexp.label_seqapd_filename.setText('SeqPLtime_%d' % self.mainexp.wavenum)

        seqapd_acqtime = self.mainexp.dbl_seqapd_acqtime.value() * 0.001
        numpnts = int(self.mainexp.dbl_seqapd_int_time.value() / seqapd_acqtime)

        # set up counter
        self.mainexp.ctrapd.reset()
        self.mainexp.ctrclk.reset()
        self.mainexp.ctrtrig.set_time(0.001)
        self.mainexp.ctrtrig.reset()
        # create a ctrapd running on clock from ctrclk and wait for trigger from ctrtrig
        self.mainexp.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.mainexp.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                             PyDAQmx.DAQmx_Val_Rising, numpnts + 1)
        self.mainexp.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                                  PyDAQmx.DAQmx_Val_Rising)
        self.mainexp.ctrapd.set_read_all_samples(True)
        # creates a clock using pulses on self.mainexp.ctrclk (output to PFI7)
        self.mainexp.ctrclk.set_freq(1 / seqapd_acqtime)
        self.mainexp.ctrclk.start()
        time.sleep(.5)

        # start acquiring data
        self.mainexp.ctrapd.start()
        self.mainexp.ctrtrig.start()
        self.mainexp.ctrtrig.wait_until_done()
        self.mainexp.ctrtrig.stop()

        n_read = 0
        t_update = 0.1

        self.mainexp.seqapd_pl = np.array([])

        last_counter = 0  # Actual counter value, which monotonically counts up and need to be diff to get count rate

        while not self.cancel and n_read < numpnts+1:
            time.sleep(t_update)
            # try to read twice as many samples as python time will always be slower
            # (assume it doesn't take more than 2*t_update)
            ctr_raw = self.mainexp.ctrapd.get_counts(int(t_update / seqapd_acqtime * 2))
            if n_read != 0:
                ctr_diff = np.diff(np.append([last_counter], ctr_raw))
            else:
                ctr_diff = np.diff(ctr_raw)
            if len(ctr_raw):
                n_read += len(ctr_raw)
                last_counter = ctr_raw[-1]
                self.mainexp.seqapd_pl = np.append(self.mainexp.seqapd_pl, ctr_diff)
                self.mainexp.seqapd_t = np.arange(len(self.mainexp.seqapd_pl)) * seqapd_acqtime
                self.signal_seqapd_updateplots.emit()

        if hasattr(PyDAQmx.DAQmxFunctions, 'DAQWarning'):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',
                                      PyDAQmx.DAQmxFunctions.DAQWarning)  # for ignoring warnings when plotting NaNs

                self.mainexp.ctrclk.stop()
                self.mainexp.ctrclk.reset()
                try:
                    self.mainexp.ctrapd.stop()
                except PyDAQmx.DAQmxFunctions.DAQError:
                    # It is normal for the PyDAQmx to throw an error when stopped prematurely
                    pass
                self.mainexp.ctrapd.reset()

        if self.mainexp.thread_terminal.isRunning() or self.mainexp.thread_batch.isRunning():
            self.save()

    def save(self):
        if self.isRunning():
            self.signal_seqapd_grab_screenshots.emit()
            self.wait_for_mainexp()
        else:
            self.mainexp.seqapd_grab_screenshots()

        time.sleep(0.1)

        graph = self.mainexp.pixmap_seqapd_graph
        filename = self.mainexp.label_seqapd_filename.text()
        data_dict = {'pl': self.mainexp.seqapd_pl, 'xvals': self.mainexp.seqapd_t}

        self.save_data(filename, data_dict, graph=graph, fig=graph)
