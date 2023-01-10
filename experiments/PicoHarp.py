import numpy as np
import time
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import ctypes as ct
from ctypes import byref

from . import ExpThread

# From phdefin.h
LIB_VERSION = "3.0"
HISTCHAN = 65536
MAXDEVNUM = 1
MODE_HIST = 0
FLAG_OVERFLOW = 0x0040

# binning = 5 # you can change this - timing resolution = 4 * 2^binning
# offset = 0
# tacq = 1000 # Measurement time in millisec, you can change this
syncDivider = 1 # you can change this
# CFDZeroCross0 = 10 # you can change this (in mV)
# CFDLevel0 = 50 # you can change this (in mV)
# CFDZeroCross1 = 10 # you can change this (in mV)
# CFDLevel1 = 50 # you can change this (in mV)

libVersion = ct.create_string_buffer(b"", 8)

try:
    phlib = ct.CDLL("phlib64.dll")  # hard-coded for 64-bit DLL
    phlib.PH_GetLibraryVersion(libVersion)
    print("PicoHarp Library version is %s" % libVersion.value.decode("utf-8"))
    if libVersion.value.decode("utf-8") != LIB_VERSION:
        raise Warning("Warning: The application was built for version %s" % LIB_VERSION)
except:
    print('Warning: phlib64.dll not found')
    phlib = None

# Define PicoHarp Sampling Selections
# Acquisition binning i
# Acquisition time = 4 ps * 2^i
DICT_RES_ACQ = {}
for i in np.arange(1, 9):
    DICT_RES_ACQ[str(pow(2, i+1))] = i

# Subsampling time (ps) - used for displaying only
DICT_RES_DISP = {}
for i in np.arange(2, 22):
    val = pow(2, i)
    if val < 1e3:
        DICT_RES_DISP['%d ps' % val] = val
    elif val < 1e6:
        DICT_RES_DISP['%d ns' % (val / 1e3)] = val
    elif val < 1e9:
        DICT_RES_DISP['%d us' % (val / 1e6)] = val


class PicoHarp(ExpThread.ExpThread):

    signal_picoharp_initplots = pyqtSignal()
    signal_picoharp_update_rate = pyqtSignal(float, float)
    signal_picoharp_update_status = pyqtSignal(str)
    signal_picoharp_update_plot = pyqtSignal(float)
    signal_picoharp_grab_screenshots = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        self.connected = False
        self.mode = 0
        self.t_remain = 0

        # Connect the signals here instead of in mainexp since it uses the dictionary defined in this class
        self.mainexp.cbox_picoharp_res_acq.addItems(sorted(DICT_RES_ACQ, key=DICT_RES_ACQ.get))
        self.mainexp.cbox_picoharp_res_disp.addItems(sorted(DICT_RES_DISP, key=DICT_RES_DISP.get))
        self.mainexp.cbox_picoharp_res_disp.currentIndexChanged.connect(self.update_res_disp)
        self.res_acq = 4
        self.res_disp = 4

        # Variables to store information read from DLLs
        self.counts = (ct.c_uint * HISTCHAN)()
        self.dev = []
        self.hwSerial = ct.create_string_buffer(b"", 8)
        self.hwPartno = ct.create_string_buffer(b"", 8)
        self.hwVersion = ct.create_string_buffer(b"", 8)
        self.hwModel = ct.create_string_buffer(b"", 16)
        self.errorString = ct.create_string_buffer(b"", 40)
        self.resolution = ct.c_double()
        self.countRate0 = ct.c_int()
        self.countRate1 = ct.c_int()
        self.flags = ct.c_int()

        # Timer for polling count rates on both channels
        self.timer_interval = 200  # ms
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_rate)

        # Tracking Conditions
        self.lasttracktime = -1.0

        # Connect the signals
        self.signal_picoharp_initplots.connect(mainexp.picoharp_initplots)
        self.signal_picoharp_update_rate.connect(mainexp.picoharp_update_rate)
        self.signal_picoharp_update_status.connect(mainexp.picoharp_update_status)
        self.signal_picoharp_update_plot.connect(mainexp.picoharp_update_plot)
        self.signal_picoharp_grab_screenshots.connect(mainexp.picoharp_grab_screenshots)

    def dev_connect(self, b):
        if b:
            dev = []

            for i in range(0, MAXDEVNUM):
                retcode = phlib.PH_OpenDevice(ct.c_int(i), self.hwSerial)
                if retcode == 0:
                    self.log("Dev%1d        S/N %s" % (i, self.hwSerial.value.decode("utf-8")))
                    dev.append(i)
                else:
                    if retcode == -1:  # ERROR_DEVICE_OPEN_FAIL
                        self.log("Dev%1d        no device" % i)
                    else:
                        phlib.PH_GetErrorString(self.errorString, ct.c_int(retcode))
                        self.log("Dev%1d        %s" % (i, self.errorString.value.decode("utf8")))

            if len(dev) < 1:
                # print("No device available.")
                self.dev_disconnect()

            else:
                try:
                    # Use the first PicoHarp device we find, i.e. dev[0].
                    # You can also use multiple devices in parallel.
                    # You can also check for specific serial numbers, so that you always know
                    # which physical device you are talking to.
                    self.dev = dev

                    # print("Using device #%1d" % dev[0])
                    # print("\nInitializing the device...")

                    self.tryfunc(phlib.PH_Initialize(ct.c_int(dev[0]), ct.c_int(MODE_HIST)), "Initialize")

                    # Only for information
                    self.tryfunc(phlib.PH_GetHardwareInfo(dev[0], self.hwModel, self.hwPartno, self.hwVersion), \
                            "GetHardwareInfo")
                    # print("Found Model %s Part no %s Version %s" % (self.hwModel.value.decode("utf-8"), \
                    #                                                 self.hwPartno.value.decode("utf-8"),
                    #                                                 self.hwVersion.value.decode("utf-8")))

                    # print("\nCalibrating...")
                    self.tryfunc(phlib.PH_Calibrate(ct.c_int(dev[0])), "Calibrate")

                    # # Note: after Init or SetSyncDiv you must allow 100 ms for valid count rate readings
                    # time.sleep(0.2)
                    #
                    # self.tryfunc(phlib.PH_GetCountRate(ct.c_int(dev[0]), ct.c_int(0), byref(self.countRate0)), "GetCountRate")
                    # self.tryfunc(phlib.PH_GetCountRate(ct.c_int(dev[0]), ct.c_int(1), byref(self.countRate1)), "GetCountRate")
                    # print("Countrate0=%d/s Countrate1=%d/s" % (self.countRate0.value, self.countRate1.value))

                    self.tryfunc(phlib.PH_SetStopOverflow(ct.c_int(dev[0]), ct.c_int(1), ct.c_int(65535)), \
                            "SetStopOverflow")
                    self.connected = True
                    self.signal_picoharp_update_status.emit('Picoharp Connected')

                    # hard-coded SyncDiv for now
                    self.tryfunc(phlib.PH_SetSyncDiv(ct.c_int(dev[0]), ct.c_int(syncDivider)), "SetSyncDiv")

                    self.update_settings()
                    if self.connected:
                        self.timer.start(self.timer_interval)
                except RuntimeError as error:
                    self.log(error.args[0])
                    self.mainexp.btn_picoharp_connect.setChecked(False)
        else:
            if self.connected:
                self.dev_disconnect()
            else:
                self.signal_picoharp_update_status.emit('Picoharp Disconnected')

    def dev_disconnect(self):
        self.connected = False
        self.signal_picoharp_update_status.emit('Picoharp Disconnected')

        self.timer.stop()

        self.mainexp.btn_picoharp_connect.setChecked(False)
        for i in range(0, MAXDEVNUM):
            phlib.PH_CloseDevice(ct.c_int(i))

    def setup(self):
        dev = self.dev
        self.tryfunc(phlib.PH_ClearHistMem(ct.c_int(dev[0]), ct.c_int(0)), "ClearHistMeM")

        self.update_settings()

        binning = DICT_RES_ACQ[self.mainexp.cbox_picoharp_res_acq.currentText()]
        self.res_acq = 2 * pow(2, binning)
        offset = self.mainexp.int_picoharp_offset.value() * 1000
        self.mode = self.mainexp.cbox_picoharp_mode.currentIndex()

        self.tryfunc(phlib.PH_SetBinning(ct.c_int(dev[0]), ct.c_int(binning)), "SetBinning")
        self.tryfunc(phlib.PH_SetOffset(ct.c_int(dev[0]), ct.c_int(offset)), "SetOffset")
        self.tryfunc(phlib.PH_GetResolution(ct.c_int(dev[0]), byref(self.resolution)), "GetResolution")

    def tryfunc(self, retcode, funcName):
        if retcode < 0:
            phlib.PH_GetErrorString(self.errorString, ct.c_int(retcode))
            self.dev_disconnect()
            raise RuntimeError("PH_%s error %d (%s). Aborted." %
                               (funcName, retcode, self.errorString.value.decode("utf-8")))

    def pb_setup(self):
        if self.mode == 1:  # pb_esr mode
            self.mainexp.pb.set_program(autostart=True, infinite=True)
        elif self.mode == 2:  # pb_custom mode
            self.mainexp.pbcustom_run()
        if self.mode:
            if self.mainexp.inst_chkbx_mw1_enable.isChecked():
                self.mainexp.mw1.set_output(1)
            if self.mainexp.inst_chkbx_mw2_enable.isChecked():
                self.mainexp.mw2.set_output(1)

    def run(self):
        self.cancel = False
        if not self.connected:
            self.log('PicoHarp not connected. Trying to connect...')
            self.dev_connect(True)
            if self.connected:
                self.mainexp.btn_picoharp_connect.blockSignals(True)
                self.mainexp.btn_picoharp_connect.setChecked(True)
                self.mainexp.btn_picoharp_connect.blockSignals(False)
            else:
                self.log('Cannot connect to Picoharp!')
                self.cancel = True

        if not self.cancel:
            self.timer.stop()

            self.mainexp.set_gui_btn_enable('picoharp', False)
            self.mainexp.btn_picoharp_start.setEnabled(False)
            self.mainexp.btn_picoharp_stop.setEnabled(True)

            self.setup()

            self.signal_picoharp_initplots.emit()
            self.wait_for_mainexp()

            self.lasttracktime = -1.0
            self.track_if_needed()
            self.pb_setup()

            dev = self.dev

            tacq_s = self.mainexp.int_picoharp_acqtime.value()
            tacq = tacq_s*1000  # Acquisition time in ms

            start_time = time.time()
            self.tryfunc(phlib.PH_StartMeas(ct.c_int(dev[0]), ct.c_int(tacq)), "StartMeas")

            ctcstatus = ct.c_int(0)
            while ctcstatus.value == 0 and not self.cancel:
                self.track_if_needed()

                if self.mode:
                    # Restart the PicoHarp if it has been stopped
                    if self.mainexp.pb.pb_read_status() != 4:
                        self.pb_setup()

                time.sleep(self.timer_interval/1000)
                self.t_remain = tacq_s - (time.time() - start_time)

                self.tryfunc(phlib.PH_CTCStatus(ct.c_int(dev[0]), byref(ctcstatus)), "CTCStatus")

                self.tryfunc(phlib.PH_GetHistogram(ct.c_int(dev[0]), byref(self.counts), ct.c_int(0)), "GetHistogram")

                self.update_rate()
                self.updata_data()

            self.t_remain = 0

            self.tryfunc(phlib.PH_StopMeas(ct.c_int(dev[0])), "StopMeas")
            self.tryfunc(phlib.PH_GetHistogram(ct.c_int(dev[0]), byref(self.counts), ct.c_int(0)), "GetHistogram")
            self.tryfunc(phlib.PH_GetFlags(ct.c_int(dev[0]), byref(self.flags)), "GetFlags")

            # integralCount = 0
            # for i in range(0, HISTCHAN):
            #     integralCount += self.counts[i]

            if self.flags.value & FLAG_OVERFLOW > 0:
                print("  Overflow.")

            self.updata_data()

            if self.mode:
                if self.mainexp.inst_chkbx_mw1_enable.isChecked():
                    self.mainexp.mw1.set_output(0)
                if self.mainexp.inst_chkbx_mw2_enable.isChecked():
                    self.mainexp.mw2.set_output(0)
                self.mainexp.pb.set_cw()

            if self.mainexp.chkbx_picoharp_autosave.isChecked():
                self.save()

            if self.connected:
                self.timer.start(self.timer_interval)

    def update_settings(self):
        dev = self.dev
        CFDZeroCross0 = self.mainexp.int_picoharp_ZeroCr0.value()
        CFDLevel0 = self.mainexp.int_picoharp_Discr0.value()
        CFDZeroCross1 = self.mainexp.int_picoharp_ZeroCr1.value()
        CFDLevel1 = self.mainexp.int_picoharp_Discr1.value()

        self.tryfunc(phlib.PH_SetInputCFD(ct.c_int(dev[0]),
                                          ct.c_int(0),
                                          ct.c_int(CFDLevel0),
                                          ct.c_int(CFDZeroCross0)),
                     "SetInputCFD")

        self.tryfunc(phlib.PH_SetInputCFD(ct.c_int(dev[0]),
                                          ct.c_int(1),
                                          ct.c_int(CFDLevel1),
                                          ct.c_int(CFDZeroCross1)),
                     "SetInputCFD")

        time.sleep(0.2)

    def updata_data(self):
        n_raw = len(self.counts)
        xvals = int(self.resolution.value)*1e-12*np.arange(n_raw)
        counts = np.asarray(self.counts)
        self.mainexp.picoharp_xvals = xvals
        self.mainexp.picoharp_yvals = counts
        # Re-sample the data
        n_sampling = self.res_disp / self.res_acq
        if n_sampling > 1:
            self.mainexp.picoharp_xvals_disp = int(self.resolution.value)*1e-12*np.arange(n_raw/n_sampling)*n_sampling
            self.mainexp.picoharp_yvals_disp = np.nansum(counts.reshape(int(n_raw/n_sampling), -1), 1)
        else:
            self.mainexp.picoharp_xvals_disp = self.mainexp.picoharp_xvals
            self.mainexp.picoharp_yvals_disp = self.mainexp.picoharp_yvals

        self.signal_picoharp_update_plot.emit(self.t_remain)

    def update_rate(self):
        dev = self.dev
        self.tryfunc(phlib.PH_GetCountRate(ct.c_int(dev[0]), ct.c_int(0), byref(self.countRate0)), "GetCountRate")
        self.tryfunc(phlib.PH_GetCountRate(ct.c_int(dev[0]), ct.c_int(1), byref(self.countRate1)), "GetCountRate")

        self.signal_picoharp_update_rate.emit(self.countRate0.value, self.countRate1.value)

    def update_res_disp(self):
        self.res_disp = DICT_RES_DISP[self.mainexp.cbox_picoharp_res_disp.currentText()]
        if not self.isRunning():
            self.mainexp.picoharp_update_plot(0.0)

    def track_if_needed(self):
        # Update the track_period and bool_period - this allows changing parameters while scan is running
        track_period = self.mainexp.dbl_tracker_period.value() * 60
        bool_period = self.mainexp.chkbx_picoharp_autotrack.isChecked()

        if (time.time() - self.lasttracktime > track_period) and bool_period:
            self.mainexp.pb.set_cw()
            self.track()

            # backup experiment, except at the beginning when it is empty
            if self.mainexp.chkbx_autosave.isChecked() and self.lasttracktime > -1.0:
                self.save()

            self.lasttracktime = time.time()

    def track(self, numtrack=1):
        self.mainexp.thread_tracker.numtrack = numtrack
        self.mainexp.thread_tracker.start()
        self.mainexp.thread_tracker.wait()

        self.mainexp.set_gui_btn_enable('picoharp', False)
        self.mainexp.btn_picoharp_stop.setEnabled(True)

        self.pb_setup()

    def save(self, ext=False):
        if self.isRunning() and not ext:
            self.signal_picoharp_grab_screenshots.emit()
            self.wait_for_mainexp()
            time.sleep(0.1)
        else:  # For use when save_exp is called from a button
            self.mainexp.picoharp_grab_screenshots()

        graph = self.mainexp.pixmap_picoharp_graph

        self.mainexp.pb.set_cw()
        time.sleep(1)

        filename = self.mainexp.label_picoharp_filename.text()
        data_dict = {'pl': self.mainexp.picoharp_yvals, 'xvals': self.mainexp.picoharp_xvals}

        self.save_data(filename, data_dict, graph=graph, fig=graph)

    def __del__(self):
        self.wait()
