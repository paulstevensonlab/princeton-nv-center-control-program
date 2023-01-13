from PyQt5.QtCore import pyqtSignal

import os, time
import numpy as np
from PyQt5 import QtGui

from . import ExpThread


class TaskHandler(ExpThread.ExpThread):

    signal_task_handler_exp_set = pyqtSignal(str)
    signal_taskhandler_update_params_table = pyqtSignal()
    signal_taskhandler_update_params_label = pyqtSignal()
    signal_taskhandler_map_updatecursor = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        self.signal_task_handler_exp_set.connect(mainexp.sweep_exp_set)
        self.signal_taskhandler_update_params_table.connect(mainexp.update_params_table)
        self.signal_taskhandler_update_params_label.connect(mainexp.update_params_label)
        self.signal_taskhandler_update_params_label.connect(mainexp.update_params_label)
        self.signal_taskhandler_map_updatecursor.connect(mainexp.map_updatecursor)

    def everything_finished(self):
        return not (self.mainexp.thread_tracker.isRunning() or
                    not self.experiments_finished())

    def experiments_finished(self):
        return not (self.mainexp.thread_confocal.isRunning() or
                    self.mainexp.thread_sweep.isRunning() or
                    self.mainexp.thread_spectrometer.isRunning() or
                    self.mainexp.thread_picoharp.isRunning() or
                    self.mainexp.thread_satcurve.isRunning() or
                    self.mainexp.thread_liveapd.isRunning() or
                    self.mainexp.thread_seqapd.isRunning())

    def run(self):
        # This is not used anything at all. Take care of things through Batch, Terminal
        pass

    '''
    Helper Functions to be called from Scripts and Terminal
    These functions contain a wait() called on appropriate threads.
    They work only when they are called from a main event loop "run()" in another QThread, e.g. Batch, Terminal
    '''
    def reset(self):
        self.cancel = False

    def track(self):
        if not self.cancel:
            if self.everything_finished():
                self.mainexp.tracker_start()
                self.mainexp.thread_tracker.wait()

            time.sleep(0.1)

    def confocal(self, *args, avg=1):
        if not self.cancel:
            if len(args):
                if len(args) == 7:
                    self.mainexp.dbl_confocal_x_start.setValue(args[0])
                    self.mainexp.dbl_confocal_x_stop.setValue(args[1])
                    self.mainexp.int_confocal_x_numdivs.setValue(args[2])
                    self.mainexp.dbl_confocal_y_start.setValue(args[3])
                    self.mainexp.dbl_confocal_y_stop.setValue(args[4])
                    self.mainexp.int_confocal_y_numdivs.setValue(args[5])
                    self.mainexp.dbl_confocal_acqtime.setValue(args[6])
                    self.mainexp.int_confocal_live_avg.setValue(avg)
                else:
                    raise Exception('expect 6 arguments: x1, x2, sizeX, y1, y2, sizeY, acqtime')

            self.mainexp.tab_main.setCurrentIndex(0)  # set to confocal
            self.mainexp.confocal_start()
            self.mainexp.thread_confocal.wait()

            time.sleep(0.1)

    def setexp(self, exp_name):
        if not self.cancel:
            self.signal_task_handler_exp_set.emit(exp_name)
            if self.isRunning():
                self.wait_for_mainexp()

            time.sleep(0.1)

    def setval(self, varname, val, log=True, ext=False):  # set log=False during the sweep
        if not self.cancel:
            self.mainexp.exp_params_setval(varname, val, log=(self.mainexp.thread_terminal.isRunning() and log))

            if varname == 'nvnum':
                self.mainexp.dbl_tracker_xpos.setValue(float(self.mainexp.table_nvlist.item(val-1, 0).text()))
                self.mainexp.dbl_tracker_ypos.setValue(float(self.mainexp.table_nvlist.item(val-1, 1).text()))
                self.mainexp.dbl_tracker_zpos.setValue(float(self.mainexp.table_nvlist.item(val-1, 2).text()))
                self.mainexp.chkbx_plnorm.setChecked(False)
                self.mainexp.tracker_drive()

                time.sleep(0.1)

            self.signal_taskhandler_update_params_table.emit()

            if varname == 'nvnum':
                numtrack = self.mainexp.int_nvlist_numtrack.value()

                if numtrack:
                    self.mainexp.tracker_start()
                    if not ext:  # No wait when it is externally called from GUI
                        self.mainexp.thread_tracker.wait()
                    time.sleep(0.1)

                self.signal_taskhandler_map_updatecursor.emit()

            time.sleep(0.1)

    def getval(self, varname):
        if not self.cancel:
            val = self.mainexp.exp_params_getval(varname)
            self.log('%s = %s' % (varname, str(val)))
            return val
        else:
            return 0

    def do1d(self, *args, logx=False):
        if not self.cancel:
            if len(args) > 0:
                if len(args) == 7:
                    self.mainexp.var1_name.blockSignals(True)
                    self.mainexp.var1_name.setCurrentIndex(self.mainexp.var1_name.findText(args[0]))
                    self.mainexp.var1_name.blockSignals(False)
                    self.mainexp.var1_start.setValue(args[1])
                    self.mainexp.var1_start_unit.setCurrentIndex(self.mainexp.var1_start_unit.findText(args[2]))
                    self.mainexp.var1_stop.setValue(args[3])
                    self.mainexp.var1_stop_unit.setCurrentIndex(self.mainexp.var1_stop_unit.findText(args[4]))
                    self.mainexp.var1_numdivs.setValue(args[5])
                    self.mainexp.var1_delay.setValue(args[6])
                    self.mainexp.chkbx_exp_logx.setChecked(logx)
                else:
                    raise Exception('expect 7 arguments: '
                                    'var1_name, var1_start, var1_start_unit, var1_stop, var1_stop_unit, '
                                    'var1_numdivs, var1_delay')

            self.mainexp.chkbx_autosave.setChecked(True)
            self.mainexp.chkbx_2dexp.setChecked(False)
            self.mainexp.sweep_start()
            self.mainexp.thread_sweep.wait()

            time.sleep(0.1)

    def do2d(self, *args, logx=False, meander=False):
        if not self.cancel:
            self.mainexp.chkbx_2dexp.setChecked(True)

            if len(args) > 0:
                if len(args) == 14:
                    self.mainexp.var1_name.blockSignals(True)
                    self.mainexp.var1_name.setCurrentIndex(self.mainexp.var1_name.findText(args[0]))
                    self.mainexp.var1_name.blockSignals(False)
                    self.mainexp.var1_start.setValue(args[1])
                    self.mainexp.var1_start_unit.setCurrentIndex(self.mainexp.var1_start_unit.findText(args[2]))
                    self.mainexp.var1_stop.setValue(args[3])
                    self.mainexp.var1_stop_unit.setCurrentIndex(self.mainexp.var1_stop_unit.findText(args[4]))
                    self.mainexp.var1_numdivs.setValue(args[5])
                    self.mainexp.var1_delay.setValue(args[6])
                    self.mainexp.var2_name.blockSignals(True)
                    self.mainexp.var2_name.setCurrentIndex(self.mainexp.var2_name.findText(args[7]))
                    self.mainexp.var2_name.blockSignals(False)
                    self.mainexp.var2_start.setValue(args[8])
                    self.mainexp.var2_start_unit.setCurrentIndex(self.mainexp.var2_start_unit.findText(args[9]))
                    self.mainexp.var2_stop.setValue(args[10])
                    self.mainexp.var2_stop_unit.setCurrentIndex(self.mainexp.var2_stop_unit.findText(args[11]))
                    self.mainexp.var2_numdivs.setValue(args[12])
                    self.mainexp.var2_delay.setValue(args[13])
                    self.mainexp.chkbx_exp_logx.setChecked(logx)
                    self.mainexp.chkbx_2dexp_meander.setChecked(meander)
                else:
                    raise Exception('expect 14 arguments: '
                                    'var1_name, var1_start, var1_start_unit, var1_stop, var1_stop_unit, '
                                    'var1_numdivs, var1_delay, '
                                    'var2_name, var2_start, var2_start_unit, var2_stop, var2_stop_unit, '
                                    'var2_numdivs, var2_delay, meander=False')

            self.mainexp.chkbx_autosave.setChecked(True)
            self.mainexp.sweep_start()
            self.mainexp.thread_sweep.wait()

            time.sleep(0.1)

    def fit_mw1freq(self, offset=0.0, dec=3, autosave=True):
        if not self.cancel:
            self.mainexp.cbox_fittype.setCurrentIndex(self.mainexp.cbox_fittype.findText('Gaussian'))

            fitter = self.mainexp.thread_sweep.dofit(ext=True)

            mwfreq = round(fitter.fp[1] / 1e6, dec) * 1e6
            self.setval('mw1freq', mwfreq + offset)
            self.log('MW Frequency set to %.3f MHz (%.3f + %.3f MHz)' %
                                             (mwfreq / 1e6, (mwfreq - offset) / 1e6, offset / 1e6))

            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)
            #         update NV table
            n_row = self.getval('nvnum') - 1
            self.mainexp.table_nvlist.setItem(n_row, 3, QtGui.QTableWidgetItem('%.3f MHz' % (mwfreq / 1e6)))

            self.mainexp.nvlist_update()

    def fit_mw2freq(self, offset=0.0, dec=3, autosave=True):
        if not self.cancel:
            self.mainexp.cbox_fittype.setCurrentIndex(self.mainexp.cbox_fittype.findText('Gaussian'))

            fitter = self.mainexp.thread_sweep.dofit(ext=True)

            mwfreq = round(fitter.fp[1] / 1e6, dec) * 1e6
            self.setval('mw2freq', mwfreq + offset)
            self.log('MW Frequency set to %.3f MHz (%.3f + %.3f MHz)' %
                                             (mwfreq / 1e6, (mwfreq - offset) / 1e6, offset / 1e6))

            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)

    def go_to_max(self, autosave=True):
        if not self.cancel:
            varname = self.mainexp.thread_sweep.var1
            newindex = np.argmax(self.mainexp.esrtrace_pl)
            newvalue = self.mainexp.thread_sweep.sweeprng1[newindex]
            self.setval(varname, newvalue)
            self.log('Set variable %s to %.3f for max PL.' % (varname, newvalue))
            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)

            return bool(newindex == 0 or newindex == len(self.mainexp.thread_sweep.sweeprng1)-1)

    def go_to_min(self, autosave=True):
        if not self.cancel:
            varname = self.mainexp.thread_sweep.var1
            newindex = np.argmin(self.mainexp.esrtrace_pl)
            newvalue = self.mainexp.thread_sweep.sweeprng1[newindex]
            self.setval(varname, newvalue)
            self.log('Set variable %s to %.3f for min PL.' % (varname, newvalue))
            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)

            return bool(newindex == 0 or newindex == len(self.mainexp.thread_sweep.sweeprng1) - 1)

    def fit_rabi(self, pipulsewidth=56e-9, plcal=True, autosave=True):
        if not self.cancel:
            self.mainexp.cbox_fittype.setCurrentIndex(self.mainexp.cbox_fittype.findText('sin'))

            fitter = self.mainexp.thread_sweep.dofit(ext=True)
            phase_in_0_2pi = fitter.fp[2]-2*np.pi*np.floor(fitter.fp[2]/2/np.pi) # add multiples of 2 pi to the phase to keep it in (0, 2pi)
            pipulsewidth_fitted = (np.pi - phase_in_0_2pi + np.pi/2)/2/np.pi/fitter.fp[1]*1e9

            mwpow = self.mainexp.exp_params['Instrument']['mw1pow']
            pipulsewidth_ns = pipulsewidth*1e9

            mwpow_toset = round(mwpow + 20 * np.log10(pipulsewidth_fitted / pipulsewidth_ns), 2)
            self.setval('mw1pow', mwpow_toset)

            self.log('fitted pi-pulse %d ns. Setting mw1pow to %.1f dBm for %d ns pi-pulse.'
                                             % (pipulsewidth_fitted, mwpow_toset, pipulsewidth_ns))

            if plcal:
                pl_bright = fitter.fp[3] + abs(fitter.fp[0])
                pl_dark = fitter.fp[3] - abs(fitter.fp[0])
                if not self.mainexp.chkbx_plnorm.isChecked():
                    self.mainexp.dbl_plnorm_bright.setValue(pl_bright)
                    self.mainexp.dbl_plnorm_dark.setValue(pl_dark)
                    self.mainexp.chkbx_plnorm.setChecked(True)
                else:  # data was already normalized
                    pl_bright = self.mainexp.dbl_plnorm_dark.value() + \
                                pl_bright * (
                                            self.mainexp.dbl_plnorm_bright.value() - self.mainexp.dbl_plnorm_dark.value())
                    pl_dark = self.mainexp.dbl_plnorm_dark.value() + \
                              pl_dark * (self.mainexp.dbl_plnorm_bright.value() - self.mainexp.dbl_plnorm_dark.value())
                self.log('PL levels: (bright, dark) = (%.3f, %.3f)' % (pl_bright, pl_dark))

            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)

    def fit_rabi_parameters(self):
        if not self.cancel:
            self.mainexp.cbox_fittype.setCurrentIndex(self.mainexp.cbox_fittype.findText('sin'))

            fitter = self.mainexp.thread_sweep.dofit(ext=True)

            time.sleep(0.1)
            return fitter.fp


    def fit_rabi2(self, pipulsewidth=56e-9, plcal=False, autosave=True):
        if not self.cancel:
            self.mainexp.cbox_fittype.setCurrentIndex(self.mainexp.cbox_fittype.findText('sin'))

            fitter = self.mainexp.thread_sweep.dofit(ext=True)
            pipulsewidth_fitted = (np.pi - fitter.fp[2] + np.pi/2)/2/np.pi/fitter.fp[1]*1e9

            mwpow = self.mainexp.exp_params['Instrument']['mw2pow']
            pipulsewidth_ns = pipulsewidth*1e9

            mwpow_toset = round(mwpow + 20 * np.log10(pipulsewidth_fitted / pipulsewidth_ns), 1)
            self.setval('mw2pow', mwpow_toset)

            self.log('fitted pi-pulse %d ns. Setting mw2pow to %.1f dBm for %d ns pi-pulse.'
                             % (pipulsewidth_fitted, mwpow_toset, pipulsewidth_ns))

            if plcal:
                pl_bright = fitter.fp[3] + abs(fitter.fp[0])
                pl_dark = fitter.fp[3] - abs(fitter.fp[0])
                if not self.mainexp.chkbx_plnorm.isChecked():
                    self.mainexp.dbl_plnorm_bright.setValue(pl_bright)
                    self.mainexp.dbl_plnorm_dark.setValue(pl_dark)
                    self.mainexp.chkbx_plnorm.setChecked(True)
                else:  # data was already normalized
                    pl_bright = self.mainexp.dbl_plnorm_dark.value() + \
                                pl_bright * (
                                            self.mainexp.dbl_plnorm_bright.value() - self.mainexp.dbl_plnorm_dark.value())
                    pl_dark = self.mainexp.dbl_plnorm_dark.value() + \
                              pl_dark * (self.mainexp.dbl_plnorm_bright.value() - self.mainexp.dbl_plnorm_dark.value())
                self.log('PL levels: (bright, dark) = (%.3f, %.3f)' % (pl_bright, pl_dark))

            time.sleep(0.1)

            if autosave:
                self.mainexp.thread_sweep.save_exp(ext=True)

            time.sleep(0.1)

    def seqapd(self, int_time=None, sampling_time=None):
        if not self.cancel:
            if int_time is not None:
                self.mainexp.dbl_seqapd_int_time.setValue(int_time)
            if sampling_time is not None:
                self.mainexp.dbl_seqapd_acqtime.setValue(sampling_time)
            self.mainexp.thread_seqapd.start()
            self.mainexp.thread_seqapd.wait()

    def satcurve(self, start=None, stop=None, numdivs=None, delay=None, voa=None, pm=None):
        if not self.cancel:
            if None not in [start, stop, numdivs, delay]:
                self.mainexp.dbl_satcurve_voa_start.setValue(start)
                self.mainexp.dbl_satcurve_voa_stop.setValue(stop)
                self.mainexp.int_satcurve_voa_numdivs.setValue(numdivs)
                self.mainexp.dbl_satcurve_acqtime.setValue(delay)
            if voa is not None:
                self.mainexp.cbox_satcurve_voa.setCurrentIndex(self.mainexp.cbox_satcurve_voa.findText(voa))
            if pm is not None:
                self.mainexp.cbox_satcurve_pm.setCurrentIndex(self.mainexp.cbox_satcurve_pm.findText(pm))
            self.mainexp.thread_satcurve.start()
            self.mainexp.thread_satcurve.wait()

    def picoharp(self, int_time=None, res=None, offset=None, mode=None):
        if not self.cancel:
            if int_time is not None:
                self.mainexp.int_picoharp_acqtime.setValue(int(int_time))
            if res is not None:
                self.mainexp.cbox_picoharp_res_acq.setCurrentIndex(self.mainexp.cbox_picoharp_res_acq.findText(str(res)))
            if offset is not None:
                self.mainexp.int_picoharp_offset.setValue(int(offset))
            if mode is not None:
                self.mainexp.cbox_picoharp_mode.setCurrentIndex(mode)

            self.mainexp.chkbx_picoharp_autosave.setChecked(True)
            self.mainexp.thread_picoharp.start()
            self.mainexp.thread_picoharp.wait()

    def spectrometer(self, exptime=None, center=None, ybins=None, grating=None):
        if not self.cancel:
            if exptime is not None:
                self.mainexp.dbl_spectrometer_exptime.setValue(exptime)
            if center is not None:
                self.mainexp.dbl_spectrometer_centerwavelength.setValue(center)
            if ybins is not None and type(ybins) is list:
                self.mainexp.int_spectrometer_ybin_start.setValue(ybins[0])
                self.mainexp.int_spectrometer_ybin_stop.setValue(ybins[1])
            if grating is not None:
                self.mainexp.cbox_spectrometer_grating.setCurrentIndex(grating-1)

            self.mainexp.chkbx_autosave.setChecked(True)

            self.mainexp.thread_spectrometer.start()
            self.mainexp.thread_spectrometer.wait()

#   Quality of life functions added. Need to check if these are necessary

    def set_inv(self,inv):
        self.mainexp.chkbx_inv.setChecked(inv)

    def set_mw_checked(self,src=0,setflag=False):
        if src == 1:
            self.mainexp.inst_chkbx_mw1_enable.setChecked(setflag)
        elif src == 2:
            self.mainexp.inst_chkbx_mw2_enable.setChecked(setflag)
            return
        return
