from PyQt5.QtCore import QThread, pyqtSignal
import time
import numpy as np

import fitters
from . import ExpThread


class SatCurve(ExpThread.ExpThread):

    signal_satcurve_updateplots = pyqtSignal()
    signal_satcurve_updatefits = pyqtSignal()
    signal_satcurve_grab_screenshots = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        self.fitter = fitters.fit_satcurve()
        self.signal_satcurve_updateplots.connect(mainexp.satcurve_updateplots)
        self.signal_satcurve_updatefits.connect(mainexp.satcurve_updatefits)
        self.signal_satcurve_grab_screenshots.connect(mainexp.satcurve_grab_screenshots)

    def meas(self):

        pm = getattr(self.mainexp, self.mainexp.cbox_satcurve_pm.currentText())
        acqtime = self.mainexp.dbl_satcurve_acqtime.value()
        val = self.get_countrate(acqtime)

        self.mainexp.satcurve_pl = np.append(self.mainexp.satcurve_pl, val)
        self.mainexp.satcurve_p = np.append(self.mainexp.satcurve_p, pm.get_pow()*1000)

        self.mainexp.satcurve_pl = [x for (y, x) in sorted(zip(self.mainexp.satcurve_p, self.mainexp.satcurve_pl))]
        self.mainexp.satcurve_p = sorted(self.mainexp.satcurve_p)

        self.signal_satcurve_updateplots.emit()

    def get_countrate(self, acqtime):
        self.mainexp.ctrapd.start()
        self.mainexp.ctrtrig.set_time(acqtime)
        self.mainexp.ctrtrig.start()
        self.mainexp.ctrtrig.wait_until_done()
        self.mainexp.ctrtrig.stop()
        val = self.mainexp.ctrapd.get_count() / acqtime
        self.mainexp.ctrapd.stop()

        return val

    def clear(self):
        self.mainexp.satcurve_p = []
        self.mainexp.satcurve_pl = []
        self.signal_satcurve_updateplots.emit()

    def fit(self):
        self.fitter.set_data(self.mainexp.satcurve_pl, self.mainexp.satcurve_p)

        fp = self.fitter.dofit()
        [xvals, yvals] = self.fitter.get_fitcurve_smooth()

        self.mainexp.satcurve_p_fit = xvals
        self.mainexp.satcurve_pl_fit = yvals

        fitreports = '#%d\nNV#%d (%.3f, %.3f)\nPLsat = %.2f kcps\nPsat = %.3f mW\nbg = %.3f kcps/mW' % \
                     (self.mainexp.wavenum,
                      self.mainexp.exp_params['Confocal']['nvnum'],
                      self.mainexp.exp_params['Confocal']['xpos'],
                      self.mainexp.exp_params['Confocal']['ypos'], (fp[0]*0.001), fp[1], (fp[2])*0.001)

        self.log(fitreports)
        self.mainexp.label_satcurve_fit.setText(fitreports)
        self.signal_satcurve_updatefits.emit()

    def run(self):
        self.cancel = False
        self.clear()
        sweeprng = np.linspace(self.mainexp.dbl_satcurve_voa_start.value(),
                               self.mainexp.dbl_satcurve_voa_stop.value(),
                               self.mainexp.int_satcurve_voa_numdivs.value() + 1)

        self.mainexp.ctrapd.reset()
        self.mainexp.ctrtrig.reset()
        self.mainexp.ctrapd.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'])

        voa = getattr(self.mainexp, self.mainexp.cbox_satcurve_voa.currentText())
        for v in sweeprng:
            if not self.cancel:
                voa.set_voltage(v)
                time.sleep(0.1)
                self.meas()

        if self.mainexp.thread_terminal.isRunning() or self.mainexp.thread_batch.isRunning():
            self.fit()
            self.save()

    def save(self):
        if self.isRunning():
            self.signal_satcurve_grab_screenshots.emit()
            self.wait_for_mainexp()
            time.sleep(0.1)
        else:  # For use when save_exp is called from a button
            self.mainexp.satcurve_grab_screenshots()

        graph = self.mainexp.pixmap_satcurve_graph
        pm = self.mainexp.cbox_satcurve_pm.currentText()

        if pm == 'pm100d':
            xvar = 'p532'
        elif pm == 'pm100d_orange':
            xvar = 'p590'
        elif pm.startswith('pm100d_'):
            xvar = 'p' + pm[7:]
        else:
            xvar = 'pUNKNOWN'

        filename = 'PL%s_%d' % (xvar, self.mainexp.wavenum)
        data_dict = {'pl': self.mainexp.satcurve_pl, 'xvals': self.mainexp.satcurve_p}

        self.save_data(filename, data_dict, graph=graph, fig=graph)
