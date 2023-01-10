from PyQt5 import QtGui, QtCore, QtWidgets

# system imports
import weakref, datetime, pytz
import pyqtgraph as pg
import numpy as np
import functools

# import UI files
import widget_tracker
import widget_liveapd
import widget_seqapd
import widget_satcurve
import widget_histogram
import widget_picoharp
import widget_calculator
import widget_batch
import widget_terminal
import widget_shortcuts


class TrackerControl(QtGui.QWidget, widget_tracker.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_tracker.setChecked(False)


class LiveAPD(QtGui.QWidget, widget_liveapd.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        if self.btn_liveapd_stop.isEnabled():
            self.mainexp.liveapd_stop()
        self.mainexp.btn_widget_liveapd.setChecked(False)


class SeqAPD(QtGui.QWidget, widget_seqapd.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_seqapd.setChecked(False)


class SatCurve(QtGui.QWidget, widget_satcurve.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_satcurve.setChecked(False)


class Histogram(QtGui.QWidget, widget_histogram.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_histogram.setChecked(False)


class Picoharp(QtGui.QWidget, widget_picoharp.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_picoharp.setChecked(False)

'''NV PARAMETERS'''
ZFS = 2870.0  # Zero-Field Splitting
gamma_e = 2.802  # MHz/G
gamma_p = 4.256  # kHz/G
'''PHOTON PARAMETERS'''
c = 299792458
h = 6.62607004e-4  # zJ / GHz
kB = 1.38064852e-2  # zJ / K
e = 1.60217662e-1  # zJ / mV


class Calculator(QtGui.QWidget, widget_calculator.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.btn_nvfreq.clicked.connect(self.get_nvfreq)
        self.btn_deerfreq.clicked.connect(self.get_deerfreq)
        self.btn_nvfreq_2.clicked.connect(self.get_nvfreq_2)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

        self.dbl_calc_Bz.valueChanged.connect(self.calc_Bz)
        self.dbl_calc_nvfreq.valueChanged.connect(self.calc_nvfreq)
        self.dbl_calc_deerfreq.valueChanged.connect(self.calc_deerfreq)
        self.dbl_calc_protonfreq.valueChanged.connect(self.calc_protonfreq)
        self.dbl_calc_protontau.valueChanged.connect(self.calc_protontau)
        self.dbl_calc_nvfreq_2.valueChanged.connect(self.calc_nvfreq_2)

        self.dbl_calc_freq_abs.valueChanged[float].connect(self.calc_photon_freq_abs)
        self.dbl_calc_wavelength_abs.valueChanged[float].connect(self.calc_photon_wavelength_abs)
        self.dbl_calc_energy_abs.valueChanged[float].connect(self.calc_photon_energy_abs)
        self.dbl_calc_temp_abs.valueChanged[float].connect(self.calc_photon_temp_abs)
        self.dbl_calc_freq_delta.valueChanged[float].connect(self.calc_photon_freq_delta)
        self.dbl_calc_wavelength_delta.valueChanged[float].connect(self.calc_photon_wavelength_delta)
        self.dbl_calc_energy_delta.valueChanged[float].connect(self.calc_photon_energy_delta)
        self.dbl_calc_temp_delta.valueChanged[float].connect(self.calc_photon_temp_delta)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_calculator.setChecked(False)

    '''NV Calculations'''

    def calc_Bz(self, excl=''):
        Bz = self.dbl_calc_Bz.value()

        if excl != 'nvfreq':
            self.dbl_calc_nvfreq.setValue(ZFS-gamma_e*Bz)
        if excl != 'deerfreq':
            self.dbl_calc_deerfreq.setValue(gamma_e*Bz)
        if excl != 'protonfreq':
            self.dbl_calc_protonfreq.setValue(gamma_p*Bz)
        if excl != 'protontau':
            self.dbl_calc_protontau.setValue(1e6/gamma_p/Bz/2.0)
        if excl != 'nvfreq_2':
            self.dbl_calc_nvfreq_2.setValue(ZFS+gamma_e*Bz)

    def calc_nvfreq(self):
        nvfreq = self.dbl_calc_nvfreq.value()
        self.dbl_calc_Bz.setValue((ZFS-nvfreq)/gamma_e)
        self.calc_Bz('nvfreq')

    def calc_deerfreq(self):
        deerfreq = self.dbl_calc_deerfreq.value()
        self.dbl_calc_Bz.setValue(deerfreq/gamma_e)
        self.calc_Bz('deerfreq')

    def calc_protonfreq(self):
        protonfreq = self.dbl_calc_protonfreq.value()
        self.dbl_calc_Bz.setValue(protonfreq/gamma_p)
        self.calc_Bz('protonfreq')

    def calc_protontau(self):
        protontau = self.dbl_calc_protontau.value()
        self.dbl_calc_Bz.setValue(1e6/gamma_p/protontau/2.0)
        self.calc_Bz('protontau')

    def calc_nvfreq_2(self):
        nvfreq_2 = self.dbl_calc_nvfreq_2.value()
        self.dbl_calc_Bz.setValue((nvfreq_2-ZFS)/gamma_e)
        self.calc_Bz('nvfreq_2')

    def get_nvfreq(self):
        self.dbl_calc_nvfreq.setValue(float(self.mainexp.exp_params['Instrument']['mw1freq'])*1e-6)

    def get_deerfreq(self):
        self.dbl_calc_deerfreq.setValue(float(self.mainexp.exp_params['Instrument']['mw2freq'])*1e-6)

    def get_nvfreq_2(self):
        self.dbl_calc_nvfreq_2.setValue(float(self.mainexp.exp_params['Instrument']['mw1freq'])*1e-6)

    '''Photon Unit Conversions'''

    def calc_photon_freq_abs(self, freq, excl=''):
        try:
            if excl != 'wavelength':
                self.dbl_calc_wavelength_abs.blockSignals(True)
                self.dbl_calc_wavelength_abs.setValue(c / freq)
                self.dbl_calc_wavelength_abs.blockSignals(False)
            if excl != 'energy':
                self.dbl_calc_energy_abs.blockSignals(True)
                self.dbl_calc_energy_abs.setValue(h * freq / e)
                self.dbl_calc_energy_abs.blockSignals(False)
            if excl != 'temp':
                self.dbl_calc_temp_abs.blockSignals(True)
                self.dbl_calc_temp_abs.setValue(h * freq / kB)
                self.dbl_calc_temp_abs.blockSignals(False)
        except ZeroDivisionError:
            pass

    def calc_photon_wavelength_abs(self, wavelength):
        try:
            self.dbl_calc_freq_abs.blockSignals(True)
            self.dbl_calc_freq_abs.setValue(c / wavelength)
            self.dbl_calc_freq_abs.blockSignals(False)
            self.calc_photon_freq_abs(c / wavelength, excl='wavelength')
        except ZeroDivisionError:
            pass

    def calc_photon_energy_abs(self, energy):
        try:
            self.dbl_calc_freq_abs.blockSignals(True)
            self.dbl_calc_freq_abs.setValue(e * energy / h)
            self.dbl_calc_freq_abs.blockSignals(False)
            self.calc_photon_freq_abs(e * energy / h, excl='energy')
        except ZeroDivisionError:
            pass

    def calc_photon_temp_abs(self, temp):
        try:
            self.dbl_calc_freq_abs.blockSignals(True)
            self.dbl_calc_freq_abs.setValue(temp * kB / h)
            self.dbl_calc_freq_abs.blockSignals(False)
            self.calc_photon_freq_abs(temp * kB / h, excl='temp')
        except ZeroDivisionError:
            pass

    def calc_photon_freq_delta(self, freq_delta, excl=''):
        try:
            if excl != 'wavelength':
                freq = self.dbl_calc_freq_abs.value()
                wavelength_delta = c / (freq + freq_delta) - c / freq
                self.dbl_calc_wavelength_delta.blockSignals(True)
                self.dbl_calc_wavelength_delta.setValue(wavelength_delta)
                self.dbl_calc_wavelength_delta.blockSignals(False)
            if excl != 'energy':
                self.dbl_calc_energy_delta.blockSignals(True)
                self.dbl_calc_energy_delta.setValue(h * freq_delta / e)
                self.dbl_calc_energy_delta.blockSignals(False)
            if excl != 'temp':
                self.dbl_calc_temp_delta.blockSignals(True)
                self.dbl_calc_temp_delta.setValue(h * freq_delta / kB)
                self.dbl_calc_temp_delta.blockSignals(False)
        except ZeroDivisionError:
            pass

    def calc_photon_wavelength_delta(self, wavelength_delta):
        try:
            wavelength = self.dbl_calc_wavelength_abs.value()
            freq_delta = c / (wavelength + wavelength_delta) - c / wavelength
            self.dbl_calc_freq_delta.blockSignals(True)
            self.dbl_calc_freq_delta.setValue(freq_delta)
            self.dbl_calc_freq_delta.blockSignals(False)
            self.calc_photon_freq_delta(freq_delta, excl='wavelength')
        except ZeroDivisionError:
            pass

    def calc_photon_energy_delta(self, energy_delta):
        try:
            self.dbl_calc_freq_delta.blockSignals(True)
            self.dbl_calc_freq_delta.setValue(e * energy_delta / h)
            self.dbl_calc_freq_delta.blockSignals(False)
            self.calc_photon_freq_delta(e * energy_delta / h, excl='energy')
        except ZeroDivisionError:
            pass

    def calc_photon_temp_delta(self, temp_delta):
        try:
            self.dbl_calc_freq_delta.blockSignals(True)
            self.dbl_calc_freq_delta.setValue(temp_delta * kB / h)
            self.dbl_calc_freq_delta.blockSignals(False)
            self.calc_photon_freq_delta(temp_delta * kB / h, excl='temp')
        except ZeroDivisionError:
            pass


class Batch(QtGui.QWidget, widget_batch.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_batch.setChecked(False)


class Terminal(QtGui.QWidget, widget_terminal.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)

        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

        self.shortcut_focus = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+J'), self)
        self.shortcut_focus.activated.connect(self.setFocus)

        self.linein_terminal_cmd.setFocus()

    def display(self, disp):
        if disp:
            self.show()
            self.raise_()
        else:
            self.hide()

    def bringToFront(self):
        self.show()
        self.raise_()
        self.setFocus()
        self.linein_terminal_cmd.setFocus()
        self.mainexp.btn_widget_terminal.setChecked(True)

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_terminal.setChecked(False)


class Shortcuts(QtGui.QWidget, widget_shortcuts.Ui_Form):
    def __init__(self, mainexp):
        super().__init__()
        self.setupUi(self)
        self.mainexp = mainexp

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.shortcut_close = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+W'), self)
        self.shortcut_close.activated.connect(self.close)

    def display(self, disp):
        if disp:
            self.show()
        else:
            self.hide()

    def closeEvent(self, *args, **kwargs):
        self.mainexp.btn_widget_shortcuts.setChecked(False)


class CustomLUTWidget(pg.GraphicsView):

    def __init__(self, parent=None, *args, **kargs):
        background = kargs.get('background', 'default')
        pg.GraphicsView.__init__(self, parent, useOpenGL=False, background=background)
        self.item = CustomLUTItem(*args, **kargs)
        self.setCentralItem(self.item)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(56)

        self.gradient.rectSize = 7  # width of color bar
        self.gradient.tickSize = 5

    def sizeHint(self):
        return QtCore.QSize(50, 200)

    def setLabel(self, text=None, units=None, unitPrefix=None, **args):
        self.item.axis.setLabel(text=text, units=units, unitPrefix=unitPrefix, **args)
        self.setMinimumWidth(60)
        # self.axis.setWidth(15)

    def __getattr__(self, attr):
        return getattr(self.item, attr)


class CustomLUTItem(pg.HistogramLUTItem):
    def __init__(self, image=None, fillHistogram=True):
        self.autoLevel = True
        super().__init__(image=image, fillHistogram=fillHistogram)
        self.vb.setMinimumWidth(10)  # width of the actual histogram
        self.vb.setMaximumWidth(15)  # width of the actual histogram
        self.vb.setContentsMargins(0.01, 0.01, 0.01, 0.01)

    def setImageItem(self, img_list):
        # Clear old signals:
        if type(self.imageItem) is not list:
            if callable(self.imageItem):
                if self.imageItem() is not None:
                    self.imageItem().sigImageChanged.disconnect()
            elif self.imageItem is not None:
                self.imageItem.sigImageChanged.disconnect()
        else:
            for img in self.imageItem:
                img().sigImageChanged.disconnect()

        # allow setting array of images
        if type(img_list) is not list:
            self.imageItem = weakref.ref(img_list)
            img_list.sigImageChanged.connect(functools.partial(self.imageChanged, autoLevel=True))
            img_list.setLookupTable(self.getLookupTable)  ## send function pointer, not the result
            # self.gradientChanged()
            self.regionChanged()
        else:
            self.imageItem = []
            for img in img_list:
                self.imageItem.append(weakref.ref(img))
                img.sigImageChanged.connect(functools.partial(self.imageChanged, autoLevel=True))
                img.setLookupTable(self.getLookupTable)

            self.regionChanged()
        self.imageChanged(autoLevel=self.autoLevel)

    def gradientChanged(self):
        if self.imageItem is not None:
            if self.gradient.isLookupTrivial():
                lut = None  # lambda x: x.astype(np.uint8))
            else:
                lut = self.getLookupTable  ## send function pointer, not the result

            if type(self.imageItem) is not list:
                if self.imageItem() is not None:
                    self.imageItem().setLookupTable(lut)
            else:
                for img in self.imageItem:
                    img().setLookupTable(lut)

        self.lut = None
        # if self.imageItem is not None:
        # self.imageItem.setLookupTable(self.gradient.getLookupTable(512))
        self.sigLookupTableChanged.emit(self)

    def updateImageRegion(self):
        if self.imageItem is not None:
            if type(self.imageItem) is not list:
                if self.imageItem() is not None:
                    self.imageItem().setLevels(self.region.getRegion())
            else:
                for img in self.imageItem:
                    img().setLevels(self.region.getRegion())

    def regionChanged(self):
        self.updateImageRegion()
        self.sigLevelChangeFinished.emit(self)

    def regionChanging(self):
        self.updateImageRegion()
        self.sigLevelsChanged.emit(self)
        self.update()

    def imageChanged(self, autoLevel=False, autoRange=False):
        targetHistogramSize = 100
        if type(self.imageItem) is not list:
            h = self.imageItem().getHistogram(targetHistogramSize=targetHistogramSize)
        else:
            mns = []
            mxs = []

            for img in self.imageItem:
                if img().image is not None:
                    mns.append(np.nanmin(img().image))
                    mxs.append(np.nanmax(img().image))

            if mns and mxs:
                mn = np.nanmin(mns)
                mx = np.nanmax(mxs)
            else:
                mn = 0.0
                mx = 1.0

            if all(img().image is not None for img in self.imageItem):
                bins = np.linspace(mn, mx, targetHistogramSize)
                hist_total = np.linspace(0, 0, targetHistogramSize)

                for img in self.imageItem:
                    image_array = img().image
                    hist = np.histogram(image_array[~np.isnan(image_array)], bins=np.linspace(mn, mx, targetHistogramSize+1))
                    hist_total += hist[0]

                h = [bins, hist_total]
            else:
                h = [None, None]

        if h[0] is None:
            return
        self.plot.setData(*h)

        if autoLevel and self.autoLevel:
            mn = h[0][0]
            mx = h[0][-1]
            self.region.setRegion([mn, mx])
        self.updateImageRegion()


UNIX_EPOCH_naive = datetime.datetime(1970, 1, 1, 0, 0)  # offset-naive datetime
UNIX_EPOCH_offset_aware = datetime.datetime(1970, 1, 1, 0, 0, tzinfo = pytz.utc)  # offset-aware datetime
UNIX_EPOCH = UNIX_EPOCH_naive

TS_MULT_us = 1e6


def now_timestamp(ts_mult=TS_MULT_us, epoch=UNIX_EPOCH):
    return int((datetime.datetime.now() - epoch).total_seconds()*ts_mult)


def int2dt(ts, ts_mult=TS_MULT_us):
    return datetime.datetime.utcfromtimestamp(float(ts)/ts_mult)


def dt2int(dt, ts_mult=TS_MULT_us, epoch=UNIX_EPOCH):
    delta = dt - epoch
    return int(delta.total_seconds()*ts_mult)


def td2int(td, ts_mult=TS_MULT_us):
    return int(td.total_seconds()*ts_mult)


def int2td(ts, ts_mult=TS_MULT_us):
    return datetime.timedelta(seconds=float(ts)/ts_mult)


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        #return [QTime().addMSecs(value).toString('mm:ss') for value in values]
        return [int2dt(value).strftime("%H:%M") for value in values]
        # return [int2dt(value).strftime("%x %X") for value in values]  # return the date
