import numpy as np
import time, datetime
from PyQt5.QtCore import QThread, pyqtSignal

from . import ExpThread


class Spectrometer(ExpThread.ExpThread):
    signal_spectrometer_wait_for_mainexp = pyqtSignal()
    signal_spectrometer_grab_screenshots = pyqtSignal()
    signal_spectrometer_initplots = pyqtSignal()
    signal_spectrometer_updateplots = pyqtSignal()
    signal_spectrometer_log = pyqtSignal(str)

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)
        self.mainexp = mainexp

        # Calibration data taken from lightfield for the SiV0 exposure frame for both gratings.
        # Calibrated 03/13/19 - Peace
        self.lambdaCal_Center = [960.0, 960.0]  # grating setting for calibration
        self.lambdaCal_Left = [936.354, 822.456]  # left most pixel reading (full x-range)
        self.lambdaCal_Right = [982.401, 1095.500]  # right most pixel reading (full x-range)

        self.exptime = 0.4
        self.centerwavelength = 945
        self.grating = 0
        self.wavelengths = []
        # mainexp.binX = [0,0]
        self.binY = [30, 70]  # change to get from y-bin

        self.binxF = None
        self.binyF = None

        self.isESR = False  # Use for alternating ESR on-off. There should be a better place to put this though.

        # Signal Definitions
        self.signal_spectrometer_initplots.connect(mainexp.spectrometer_initplots)
        self.signal_spectrometer_updateplots.connect(mainexp.spectrometer_updateplots)
        self.signal_spectrometer_log.connect(mainexp.log)
        self.signal_spectrometer_wait_for_mainexp.connect(mainexp.wait_spectrometer.wakeAll)
        self.signal_spectrometer_grab_screenshots.connect(mainexp.spectrometer_grab_screenshots)

        try:
            self.specMono = mainexp.spectrometer
            self.specCam = mainexp.spectrometer.picam
        except AttributeError:
            print('Spectrometer initialization failed. Check drivers if spectrometer is connected.')

        self.cancel = False

    def pixel2wavelength(self, pixels):
        id = self.grating - 1
        self.wavelengths = (pixels - 1) * (self.lambdaCal_Right[id] - self.lambdaCal_Left[id]) / (
        1340 - 1) + self.lambdaCal_Left[id] + self.centerwavelength - self.lambdaCal_Center[id]

    def gotolambda(self, lam):
        if self.mainexp.spectrometer_initialized:
            self.specMono.goto_nm_max_speed(lam)

    def prep_mainexp(self):
        self.mainexp.datasaved = False
        self.mainexp.exp_spec_finished = False

        # enable and disable the right buttons here
        self.mainexp.set_gui_btn_enable('all', False)
        self.mainexp.set_gui_input_enable('confocal', False)
        self.mainexp.btn_spectrometer_stop.setEnabled(True)
        self.signal_spectrometer_initplots.emit()

    def update(self):
        self.binyF = self.mainexp.chkbx_spectrometer_ybin.isChecked()

        if self.binyF:
            self.binY = [self.mainexp.int_spectrometer_ybin_start.value(),
                         self.mainexp.int_spectrometer_ybin_stop.value()]
            self.specCam.setROI(0, 1340, 1, self.binY[0], self.binY[1] - self.binY[0],
                                self.binY[1] - self.binY[0])  # can change this to match center bin
        else:
            # todo handle 2D returns for full camera image
            self.specCam.setROI(0, 1340, 1, 30, 40, 40)  # can change this to match center bin

        self.centerwavelength = self.mainexp.dbl_spectrometer_centerwavelength.value()
        self.exptime = self.mainexp.dbl_spectrometer_exptime.value()
        # Set spectrometer settings based on GUI
        self.gotolambda(self.mainexp.dbl_spectrometer_centerwavelength.value())
        # Set camera settings based on GUI

        self.set_grating(self.mainexp.cbox_spectrometer_grating.currentIndex())
        self.pixel2wavelength(np.linspace(1, 1340, 1340))
        self.specCam.setParameter("ExposureTime", self.exptime * 1000)
        self.specCam.sendConfiguration()
        time.sleep(0.3)  # was 1

    def acquire(self):
        data = np.array(self.specCam.readNFrames(1, timeout=-1))  # N, timeout (ms)

        self.mainexp.trace_spectrometer = np.empty([np.size(data), 2])
        # self.curve_spec[:, 0] = np.linspace(1, 1340,np.size(specInt))
        self.mainexp.trace_spectrometer[:, 0] = self.wavelengths
        self.mainexp.trace_spectrometer[:, 1] = np.squeeze(data)
        self.signal_spectrometer_updateplots.emit()

    def set_grating(self, index):
        if index + 1 != self.grating:
            self.specMono.set_grating(index+1)
            self.grating = index + 1

    def run(self):
        self.cancel = False
        self.prep_mainexp()
        self.update()
        self.acquire()
        while self.mainexp.btn_spectrometer_live.isChecked():
            self.acquire()
        self.cleanup()

    def cleanup(self):
        self.signal_spectrometer_updateplots.emit()  # This is not even necessary since there is only one acquisition

        if self.isRunning():
            self.wait_for_mainexp()

        self.mainexp.log('%s finished at %s' % (self.mainexp.label_filename.text(),
                                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        if self.mainexp.chkbx_autosave.isChecked() and not self.mainexp.datasaved:
            self.save()

        self.mainexp.set_gui_btn_enable('all', True)
        self.mainexp.set_gui_input_enable('spectrometer', True)
        self.mainexp.btn_spectrometer_stop.setEnabled(False)

    def save(self, ext=False):
        if self.isRunning() and not ext:
            self.signal_spectrometer_grab_screenshots.emit()
            self.wait_for_mainexp()
            time.sleep(0.1)
        else:  # For use when save_exp is called from a button
            self.mainexp.spectrometer_grab_screenshots()

        graph = self.mainexp.pixmap_spectrometer_graph
        fig = self.mainexp.pixmap_spectrometer_fig

        data_dict = {'PL': self.mainexp.trace_spectrometer[:, 1], 'Wavelength': self.mainexp.trace_spectrometer[:, 0]}
        filename = self.mainexp.label_filename.text()

        self.save_data(filename, data_dict, graph=graph, fig=fig)


class SpecInitializer(QThread):
    def __init__(self, mainexp):
        QThread.__init__(self)
        self.mainexp = mainexp

    def run(self):
        try:
            specMono = self.mainexp.spectrometer
            specCam = self.mainexp.spectrometer.picam

            if specCam.lib is not None:
                if specCam.camIDs is None:
                    print('Library, loaded, but camera not found.')
                else:  # camera found and library loaded
                    specCam.connect()
                    # specCam.printAvailableParameters()
                    specCam.setParameter('SensorTemperatureSetPoint', -75)

                    while specCam.getParameter("SensorTemperatureStatus") is 1:
                        time.sleep(2)
                        temp = specCam.getParameter("SensorTemperatureReading")
                        self.mainexp.label_spectrometer_temp.setText('CCD Temperature: %.1f C' % temp)

                        # print("CCD Temperature = %.1f\n" % temp)
                    temp = specCam.getParameter("SensorTemperatureReading")
                    self.mainexp.label_spectrometer_temp.setText('CCD Temperature: %.1f C' % temp)

                    # print("CCD Temperature Lock status: %d" % specCam.getParameter("SensorTemperatureStatus"))

                    specCam.setParameter('ExposureTime', 0)
                    # specCam.setParameter("ReadoutControlMode", PicamReadoutControlMode["FullFrame"])
                    # custom chip settings
                    # specCam.setROI(0, 1339, 1, 1, 99, 99)  # can change this to match center bin
                    # self.binyF = self.mainexp.chkbx_spectrometer_ybin.isChecked()

                    # if self.binyF:
                    #     self.binY = [self.mainexp.int_spectrometer_ybin_start.value(),
                    #                  self.mainexp.int_spectrometer_ybin_stop.value()]
                    #     specCam.setROI(0, 1340, 1, self.binY[0], self.binY[1] - self.binY[0],
                    #                         self.binY[1] - self.binY[0])  # can change this to match center bin
                    # else:
                    specCam.setROI(0, 1340, 1, 30, 40, 40)  # can change this to match center bin

                    # specCam.setParameter("ActiveWidth", 1340)
                    # specCam.setParameter("ActiveHeight", 100)
                    # specCam.setParameter("ActiveLeftMargin", 0)
                    # specCam.setParameter("ActiveRightMargin", 0)
                    # specCam.setParameter("ActiveTopMargin", 8)
                    # specCam.setParameter("ActiveBottomMargin", 8)
                    # specCam.setParameter("VerticalShiftRate", 3.2)  # select fastest

                    # set logic out to not ready
                    # specCam.setParameter("OutputSignal", PicamOutputSignal["Busy"])

                    # shutter delays; open before trigger corresponds to shutter opening pre delay
                    # specCam.setParameter("ShutterTimingMode", PicamShutterTimingMode["Normal"])
                    # specCam.setParameter("ShutterClosingDelay", 0)

                    # sensor cleaning
                    # specCam.setParameter("CleanSectionFinalHeightCount", 1)
                    # specCam.setParameter("CleanSectionFinalHeight", 100)
                    # specCam.setParameter("CleanSerialRegister", False)
                    # specCam.setParameter("CleanCycleCount", 1)
                    # specCam.setParameter("CleanCycleHeight", 100)
                    # specCam.setParameter("CleanUntilTrigger", True)

                    # sensor gain settings
                    # according to manual, Pixis supports 100kHz and 2MHz; select fastest
                    # specCam.setParameter("AdcSpeed", 2.0)
                    # specCam.setParameter("AdcAnalogGain", PicamAdcAnalogGain["Low"])
                    # specCam.setParameter("AdcQuality", PicamAdcQuality["HighCapacity"])

                    # trigger and timing settings
                    # specCam.setParameter("TriggerDetermination", PicamTriggerDetermination["PositivePolarity"])
                    # specCam.setParameter("TriggerResponse", PicamTriggerResponse["ReadoutPerTrigger"])

                    # send settings to camera
                    specCam.sendConfiguration()

                    # connect monochrometer
                    if specMono.connected:
                        self.centerwavelength = self.mainexp.dbl_spectrometer_centerwavelength.value()
                        specMono.goto_nm_max_speed(self.centerwavelength)
                    else:
                        print('Cant connect to monochromator')

                self.mainexp.spectrometer_initialized = True
                self.mainexp.set_gui_defaults()

            else:
                print('Picam library not loaded.')

        except AttributeError:
            print('Spectrometer initialization failed. Check drivers if spectrometer is connected.')