from PyQt5.QtCore import pyqtSignal
import time, datetime, warnings
import numpy as np
import PyDAQmx

import fitters
from . import ExpThread

prefix = {'G': 1e9, 'M': 1e6, 'k': 1e3, '-': 1.0, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9}
# Intervals for updating plots
PLOT_UPDATE_FAST = 100      # Fast updates for 1d scans and small 2d scans.
PLOT_UPDATE_SLOW = 1000     # Slow updates, especially used for large 2d scans


# Function for rounding number to 8-ns intervals. Useful for making sure timing of the awg and pulseblaster is synced.
# Especially useful when stepping times in log scale
def round_tau(num, div=8e-9):
    return div * np.round(num.astype(float)/div)


class Sweep(ExpThread.ExpThread):

    signal_sweep_grab_screenshots = pyqtSignal()

    signal_sweep_fits_clear = pyqtSignal()
    signal_sweep_fits_update = pyqtSignal(str)

    signal_sweep_esr_initplots = pyqtSignal()
    signal_sweep_esr_updateplots = pyqtSignal()
    signal_sweep_esr_updateplots_start = pyqtSignal(int)
    signal_sweep_esr_updateplots_stop = pyqtSignal()

    signal_sweep_ple_initplots = pyqtSignal()
    signal_sweep_ple_updateplots = pyqtSignal()
    signal_sweep_ple_updateplots_start = pyqtSignal(int)
    signal_sweep_ple_updateplots_stop = pyqtSignal()

    signal_sweep_setval_manual_prompt = pyqtSignal(str, float)

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)
        self.pb = mainexp.pb
        # Make references to the main DAQmx Channels
        self.ctr0 = mainexp.ctrapd      # DAQmxCounterInput: main counter for PL/sig counts
        self.ctr1 = mainexp.ctrapd2     # DAQmxCounterInput: secondary counter for ref counts
        self.ctr2 = mainexp.ctrapd3     # DAQmxCounterInput: third counter for sig counts
        self.ctr3 = mainexp.ctrapd4     # DAQmxCounterInput: fourth counter for ref counts
        self.ctrclk = mainexp.ctrclk    # DAQmxCounterOutput: clock source for fast sweep
        self.ctrtrig = mainexp.ctrtrig  # DAQmxTriggerOutput: trigger for fast sweep or gate for CW slow sweep

        # Parameters that are dictated by the exp_name - these should be set from TaskHandler.sweep_set_exp()
        self.use_pb = False             # (True) run a pulsed experiment or (False) CW experiment
        self.use_wm = False             # (True) use wavemeter in PLE experiment
        self.isPLE = False              # (True) PLE or (False) ESR experiments
        self.newctr = False             # (True) Counters are defined by ticks or (False) are gated
        self.sweep_finished = False     # Currently useful only for checking if save_exp is called at the end.

        # Parameters that are user selectable - these are updated at the beginning of Sweep in prep_mainexp
        self.is2D = False               # 2D parameter sweep
        self.meander = False            # meander (1,2,3,3,2,1,...) instead of rastering (1,2,3,1,2,3,...) in 2D scan
        self.isINV = False              # cycle the inv parameter (typically for pi/2 phase cycling)
        self.isINV2 = False             # cycle the inv2 parameter (typically for conditioning DEER on/off)
        self.fastPLE = False            # run a fast analog sweep for PLE
        self.newctr_2d = False          # acquire the counter data with tick marks and record every trace
        self.pl_norm = False            # normalize PL data

        # PL normalization
        self.pl_bright = 1.0
        self.pl_dark = 0.0

        # checks whether to record ple ref
        self.ple_ref = True  # This gets set in prep_sweep

        # Sweep Parameters - these will be initialized when run
        self.var1 = ''
        self.sweeprng1 = []
        self.delay1 = 0.0

        self.var2 = ''
        self.sweeprng2 = []
        self.delay2 = 0.0

        # Fast ao sweep and simultaneous ai readout for PLE piezo scanning and wavelength monitoring
        # This can probably be extended to generic fast sweep if need be
        self.tlb_id = None
        self.ai = None
        self.ao = None

        # Tracking Conditions
        self.track_period = 0.0
        self.bool_period = False
        self.lasttracktime = -1.0

        self.fitter = fitters.Fitter()

        # Signal Definitions
        self.signal_sweep_grab_screenshots.connect(self.mainexp.sweep_grab_screenshots)

        # ESR Signals
        self.signal_sweep_esr_initplots.connect(mainexp.sweep_esr_initplots)
        self.signal_sweep_esr_updateplots.connect(mainexp.sweep_esr_updateplots)
        self.signal_sweep_esr_updateplots_start.connect(mainexp.plt_esr_update_timer.start)
        self.signal_sweep_esr_updateplots_stop.connect(mainexp.plt_esr_update_timer.stop)

        # # PLE Signals
        self.signal_sweep_ple_initplots.connect(mainexp.sweep_ple_initplots)
        self.signal_sweep_ple_updateplots.connect(mainexp.sweep_ple_updateplots)
        self.signal_sweep_ple_updateplots_start.connect(mainexp.plt_ple_update_timer.start)
        self.signal_sweep_ple_updateplots_stop.connect(mainexp.plt_ple_update_timer.stop)

        # Logging Fit Signals
        self.signal_sweep_fits_clear.connect(mainexp.sweep_fits_clear)
        self.signal_sweep_fits_update.connect(mainexp.sweep_fits_update)

        # setval signal
        self.signal_sweep_setval_manual_prompt.connect(mainexp.exp_params_setval_manual_prompt)

    def run(self):
        self.cancel = False  # Flag that gets set to True if user clicks the stop button
        self.sweep_finished = False  # Currently used only to bypass laser power measurements while backing up data
        self.mainexp.task_handler.cancel = False  # Enables TaskHandler so that Sweep can call setval()

        self.lasttracktime = -1.0  # this will force tracking on the first point

        self.run_script('sweep_init.py')

        self.prep_mainexp()  # sync settings to/from mainexp
        self.prepsweep()  # calculate the sweep range and set MW outputs

        if not self.cancel:
            self.initplots()  # prep the storage arrays and assign them to plots in the mainexp
            self.sweep()  # This is where the actual loops lie

        self.sweep_finished = True
        self.cleanup()  # Reset NI resources to make them available for other tasks. Turn off MW. Save/Integrate data

        self.run_script('sweep_finish.py')

    def __del__(self):
        self.wait()

    def prep_mainexp(self):
        # Load all the sweep settings into the thread. These values should no longer be modified from GUI during sweep.
        self.set_mainexp_gui()

        self.is2D = self.mainexp.chkbx_2dexp.isChecked()
        self.meander = self.mainexp.chkbx_2dexp_meander.isChecked()
        self.isINV = 'inv' in self.mainexp.exp_params['Pulse'].keys() and self.mainexp.chkbx_inv.isChecked()
        self.isINV2 = 'inv2' in self.mainexp.exp_params['Pulse'].keys() and self.mainexp.chkbx_inv2.isChecked()
        self.fastPLE = self.isPLE and self.mainexp.chkbx_PLE_fast.isChecked()
        self.newctr_2d = self.newctr and self.mainexp.chkbx_newctr_2d.isChecked()
        self.pl_norm = self.mainexp.chkbx_plnorm.isChecked()

        # Update settings into pulseblaster
        self.pb.isINV = self.isINV
        self.pb.isINV2 = self.isINV2
        self.pb.newctr = self.newctr

        # Build a filename
        datacode = 'PL'  # we are not taking any other data type for now
        key1 = str(self.mainexp.var1_name.currentText())
        axiscode = key1
        if self.is2D:
            key2 = str(self.mainexp.var2_name.currentText())
            axiscode += key2
        filename = '%s%s_%d' % (datacode, axiscode, self.mainexp.wavenum)

        self.mainexp.label_filename.setText(filename)

        # Save current sweep settings from GUI
        self.mainexp.export_sweep_settings(sweep_var=True)

        # PL Normalization (ESR-only)
        self.pl_bright = self.mainexp.dbl_plnorm_bright.value()
        self.pl_dark = self.mainexp.dbl_plnorm_dark.value()

        self.log_clear()
        self.log('%s started at %s' % (filename, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def set_mainexp_gui(self):
        self.mainexp.set_gui_btn_enable('all', False)
        self.mainexp.set_gui_input_enable('exp', False)
        self.mainexp.btn_exp_stop.setEnabled(True)

    def prepsweep(self):
        mainexp = self.mainexp

        # prep 1d variables
        self.var1 = mainexp.var1_name.currentText()
        if self.var1 == 'itr':   # it is a dummy variable
            start_x = 0
            stop_x = mainexp.var1_numdivs.value()
            numpnts1 = mainexp.var1_numdivs.value()
        elif self.var1 == 'timetrace':
            start_x = 0
            numpnts1 = mainexp.var1_numdivs.value() + 1
            delay = mainexp.var1_delay.value()*1e-3
            stop_x = delay*(numpnts1-1)
        else:
            start_x = mainexp.var1_start.value() * prefix[mainexp.var1_start_unit.currentText()]
            stop_x = mainexp.var1_stop.value() * prefix[mainexp.var1_stop_unit.currentText()]
            numpnts1 = mainexp.var1_numdivs.value() + 1

        if self.mainexp.chkbx_exp_logx.isChecked():
            self.sweeprng1 = np.logspace(np.log10(start_x), np.log10(stop_x), numpnts1)
            self.sweeprng1 = round_tau(self.sweeprng1)
        else:
            self.sweeprng1 = np.linspace(start_x, stop_x, numpnts1)

        mainexp.esr_rngx = self.sweeprng1
        self.delay1 = mainexp.var1_delay.value()

        if self.isPLE:
            # Check if a laser is being swept and set up readout references
            if 'piezo' in self.var1:
                tlb_id = self.var1[:-5]  # just cut the word piezo
                self.tlb_id = tlb_id
                self.ao = getattr(mainexp, '%s_ao' % tlb_id)
                self.ai = getattr(mainexp, '%s_ai' % tlb_id)
                self.ple_ref = True
            elif 'ctl' in self.var1:  # for ctl laser, use one ai to read cavity reference signal as well
                self.ai = getattr(mainexp, '%s_ai' % 'ctllaser')
                self.ple_ref = True
            # Sweeping other instrument parameters
            else:
                if self.fastPLE:
                    self.log('Warning: Cannot do fast PLE with variable %s. Doing slow scan.' % self.var1)
                    self.fastPLE = False

                # Get the reference anyway from the previous reference.
                self.ple_ref = self.tlb_id is not None and self.ai is not None

        # prep 2d variables anyway even if it's not used. ** need delay2 for PLE sweep **
        self.var2 = mainexp.var2_name.currentText()
        if self.var2 == 'itr':  # it is a dummy variable
            start_y = 0
            stop_y = mainexp.var2_numdivs.value()
            numpnts2 = mainexp.var2_numdivs.value()
        else:
            start_y = mainexp.var2_start.value() * prefix[mainexp.var2_start_unit.currentText()]
            stop_y = mainexp.var2_stop.value() * prefix[mainexp.var2_stop_unit.currentText()]
            numpnts2 = mainexp.var2_numdivs.value() + 1
        self.sweeprng2 = np.linspace(start_y, stop_y, numpnts2)
        mainexp.esr_rngy = self.sweeprng2
        self.delay2 = mainexp.var2_delay.value()

        # Disable 2D scan for newctr for now
        if self.newctr and self.is2D:
            self.log(
                '2D newctr sweep not supported yet. Need to force dynamic graph display and disable raw data output')
            self.cancel = True

        # Turn on MW sources with proper modulation settings and enable through PulseBlaster
        # todo: check this from pulseblaster instead. Require pb keeping track of mw1, mw2, awg1, awg2, but it should be much nicer
        if not self.isPLE and not self.cancel:
            exp_name = self.mainexp.cbox_exp_name.currentText()

            if self.mainexp.inst_chkbx_mw1_enable.isChecked():  # allow bypassing mw1 when debugging
                if 'awg' in exp_name:
                    # uses AWG so turn on mods on generator, and set to I/Q
                    self.mainexp.mw1.set_mod(1)
                    self.mainexp.set_inst_stat['mw1_iq'](1)
                else:
                    self.mainexp.mw1.set_mod(0)
                    self.mainexp.set_inst_stat['mw1_iq'](0)

            if self.mainexp.inst_chkbx_mw2_enable.isChecked():  # allow bypassing mw1 when debugging
                if 'qurep2' in exp_name:
                    # uses AWG so turn on mods on generator, and set to I/Q
                    self.mainexp.mw2.set_mod(1)
                    self.mainexp.set_inst_stat['mw2_iq'](1)
                else:
                    self.mainexp.mw2.set_mod(0)
                    self.mainexp.set_inst_stat['mw2_iq'](0)

        if not self.isPLE:
            pb_cw_flags = ['green']
            self.pb.stop()  # Make sure MW doesn't output to the sample before pulsing
            if self.mainexp.inst_chkbx_mw1_enable.isChecked():
                self.mainexp.mw1.set_output(1)
                pb_cw_flags.append('mw1')
            if self.mainexp.inst_chkbx_mw2_enable.isChecked():
                self.mainexp.mw2.set_output(1)
                pb_cw_flags.append('mw2')

            if not self.use_pb:
                self.pb.set_cw_custom(pb_cw_flags)

        self.mainexp.update_inst_stat()

    def initplots(self):
        # Initialize Data Storage
        # Update Plots in the GUI
        if not self.isPLE:
            self.initplots_esr()
        else:
            self.initplots_ple()

    def initplots_esr(self):
        numpnts1 = len(self.sweeprng1)
        numpnts2 = len(self.sweeprng2)

        if not self.newctr:
            if not self.is2D:
                if True:
                    self.mainexp.esrtrace_pl = np.empty(numpnts1)
                    self.mainexp.esrtrace_pl[:] = np.NaN
                if self.use_pb:
                    self.mainexp.esrtrace_sig = np.empty(numpnts1)
                    self.mainexp.esrtrace_sig[:] = np.NaN
                    self.mainexp.esrtrace_ref = np.empty(numpnts1)
                    self.mainexp.esrtrace_ref[:] = np.NaN
                    if self.isINV2:
                        self.mainexp.esrtrace_pl2 = np.empty(numpnts1)
                        self.mainexp.esrtrace_pl2[:] = np.NaN
                        self.mainexp.esrtrace_sig2 = np.empty(numpnts1)
                        self.mainexp.esrtrace_sig2[:] = np.NaN
                        self.mainexp.esrtrace_ref2 = np.empty(numpnts1)
                        self.mainexp.esrtrace_ref2[:] = np.NaN

            else:  # 2D scan
                if True:
                    self.mainexp.esrtrace_pl = np.zeros([numpnts1, numpnts2])
                    # self.mainexp.esrtrace_pl[:][:] = np.NaN
                    self.mainexp.esrtrace_pl[:][:] = 1.0
                if self.use_pb:
                    self.mainexp.esrtrace_sig = np.zeros([numpnts1, numpnts2])
                    # self.mainexp.esrtrace_sig[:][:] = np.NaN
                    self.mainexp.esrtrace_sig[:][:] = 1.0
                    self.mainexp.esrtrace_ref = np.zeros([numpnts1, numpnts2])
                    # self.mainexp.esrtrace_ref[:][:] = np.NaN
                    self.mainexp.esrtrace_ref[:][:] = 1.0
                    if self.isINV2:
                        self.mainexp.esrtrace_pl2 = np.empty([numpnts1, numpnts2])
                        self.mainexp.esrtrace_pl2[:] = np.NaN
                        self.mainexp.esrtrace_sig2 = np.empty([numpnts1, numpnts2])
                        self.mainexp.esrtrace_sig2[:] = np.NaN
                        self.mainexp.esrtrace_ref2 = np.empty([numpnts1, numpnts2])
                        self.mainexp.esrtrace_ref2[:] = np.NaN
        else:  # newctr gating
            numctr = len(self.pb.newctr_ctrticks)
            reps = np.uint32(self.pb.params['reps'])

            self.mainexp.esrtrace_pl = np.empty(numpnts1)
            self.mainexp.esrtrace_pl[:] = np.NaN
            # Store only the integrated counts
            if not self.newctr_2d:
                self.mainexp.esrtrace_newctr = np.empty([numctr, numpnts1])
                self.mainexp.esrtrace_newctr[:] = np.NaN
            # Store information of individual traces in a 3d array
            else:
                self.mainexp.esrtrace_newctr = np.empty([numctr, numpnts1, reps])
                self.mainexp.esrtrace_newctr[:] = np.NaN

        if not self.cancel:
            self.signal_sweep_esr_initplots.emit()
            self.signal_sweep_esr_updateplots.emit()
            if not (self.is2D and 'timetrace' in self.mainexp.cbox_exp_name.currentText()):
                self.signal_sweep_esr_updateplots_start.emit(PLOT_UPDATE_FAST)
            else:
                self.signal_sweep_esr_updateplots_start.emit(PLOT_UPDATE_SLOW)
            if self.isRunning():
                self.wait_for_mainexp()

    def initplots_ple(self):
        if not self.is2D:
            numpnts1 = len(self.sweeprng1)

            self.mainexp.esrtrace_pl = np.empty(numpnts1)
            self.mainexp.esrtrace_pl[:] = np.NaN
            self.mainexp.esrtrace_ref = np.empty(numpnts1)
            self.mainexp.esrtrace_ref[:] = np.NaN

        else:
            numpnts1 = len(self.sweeprng1)
            numpnts2 = len(self.sweeprng2)

            if self.meander:
                n_scans = 2
            else:
                n_scans = 1

            self.mainexp.esrtrace_pl = np.zeros([numpnts1, numpnts2*n_scans])
            self.mainexp.esrtrace_pl[:][:] = np.NaN

            if self.ple_ref:
                self.mainexp.esrtrace_ref = np.zeros([numpnts1*self.ai.numchan, numpnts2*n_scans])
                self.mainexp.esrtrace_ref[:][:] = np.NaN
            else:  # Create an empty array that will never be used (to flush out old data)
                self.mainexp.esrtrace_ref = np.zeros([numpnts1, numpnts2*n_scans])
                self.mainexp.esrtrace_ref[:][:] = np.NaN

        if not self.cancel:
            self.signal_sweep_ple_initplots.emit()
            self.signal_sweep_ple_updateplots.emit()
            if not self.is2D:
                self.signal_sweep_ple_updateplots_start.emit(PLOT_UPDATE_FAST)
            else:
                self.signal_sweep_ple_updateplots_start.emit(PLOT_UPDATE_SLOW)
            if self.isRunning():
                self.wait_for_mainexp()

    def sweep(self):
        exp_name = self.mainexp.cbox_exp_name.currentText()

        if 'timetrace' not in exp_name:
            if not self.isPLE or not self.fastPLE:
                self.setup_ctr_esr()
                if not self.is2D:
                    self.sweep_esr_1d()
                else:
                    self.sweep_esr_2d()
            else:
                if not self.is2D:
                    if not self.use_pb:
                        self.sweep_ple_1d_cw()
                    else:
                        self.sweep_ple_1d_pulse()
                else:
                    if not self.use_pb:
                        self.sweep_ple_2d_cw()
                    else:
                        self.sweep_ple_2d_pulse()
        else:
            if not self.is2D:
                self.sweep_timetrace_1d()
            else:
                self.sweep_timetrace_2d()

    def is_param_type(self, var, paramtype):
        return var in self.mainexp.exp_params[paramtype].keys()

    def setup_ctr_esr(self):
        if not self.use_pb:
            self.setup_ctr_cw()
        else:
            if not self.newctr:
                self.setup_ctr_pulse()
            else:
                self.setup_ctr_newctr()

    def setup_ctr_cw(self):
        self.ctr0.reset()
        self.ctrtrig.reset()
        self.ctr0.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'])

    def setup_ctr_pulse(self):
        self.ctr0.reset()
        self.ctr1.reset()
        self.ctr2.reset()
        self.ctr3.reset()
        self.ctr0.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctr0.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd']['addr_gate'])
        self.ctr1.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctr1.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd2']['addr_gate'])
        self.ctr2.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctr2.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd3']['addr_gate'])
        self.ctr3.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctr3.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd4']['addr_gate'])

    def setup_ctr_newctr(self):
        # Use only ctr0. The clocks are defined by pulseblaster on ctr0 (a.k.a. ctrapd addr_gate)
        self.ctr0.reset()
        numticks = len(set(np.array(self.pb.newctr_ctrticks).flatten()))
        reps = np.uint32(self.pb.params['reps'])
        self.ctr0.set_sample_clock(self.mainexp.inst_params['instruments']['ctrapd']['addr_gate'],
                                   PyDAQmx.DAQmx_Val_Rising, numticks*reps)
        self.ctr0.set_read_all_samples(True)

    def get_esr_data(self, delay):
        if not self.use_pb:  # cw esr
            self.ctr0.start()
            self.ctrtrig.set_time(delay)
            self.ctrtrig.start()
            flag_cancel = self.ctrtrig.wait_until_done_thd(self)
            if flag_cancel == 0:
                self.ctrtrig.stop()
                pl = self.ctr0.get_count() / delay
                self.ctr0.stop()
                return pl
            else:
                self.ctrtrig.reset()
                self.ctr0.reset()
                return np.NaN
        else:  # pulsed esr
            time.sleep(delay)

            self.ctr0.start()
            self.ctr1.start()
            self.ctr2.start()
            self.ctr3.start()

            self.pb.set_program(autostart=1)
            flag_cancel = self.pb.wait_until_finished_thd(self)

            if flag_cancel == 0:
                sig = self.ctr0.get_count()
                ref = self.ctr1.get_count()

                cts2 = self.ctr2.get_count()
                cts3 = self.ctr3.get_count()
                pl2 = np.NaN

                # ignore RuntimeWarning in the case of pl = NaN --- This shouldn't be necessary?
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', RuntimeWarning)

                    if not self.isINV:
                        pl = np.float64(sig) / ref  # redundant but allows for data processing if need be
                        if self.pl_norm:
                            pl = (pl - self.pl_dark)/(self.pl_bright - self.pl_dark)
                    else:
                        pl = (np.float64(sig) - np.float64(ref))/(np.float64(sig) + np.float64(ref))
                        if self.pl_norm:
                            pl = pl / (self.pl_bright - self.pl_dark) * (self.pl_bright + self.pl_dark)

                        if self.isINV2:
                            pl2 = (np.float64(cts2) - np.float64(cts3)) / (np.float64(cts2) + np.float64(cts3))
                            if self.pl_norm:
                                pl2 = pl2 / (self.pl_bright - self.pl_dark) * (self.pl_bright + self.pl_dark)

                self.ctr0.stop()
                self.ctr1.stop()
                self.ctr2.stop()
                self.ctr3.stop()

                return [sig, ref, pl, cts2, cts3, pl2]
            else:
                self.ctr0.stop()
                self.ctr1.stop()
                self.ctr2.stop()
                self.ctr3.stop()
                return [np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN]

    def get_esr_data_newctr(self, delay):
        time.sleep(delay)

        ctr_raw = self.get_esr_data_newctr_raw()

        ctrticks = self.pb.newctr_ctrticks

        reps = np.uint32(self.pb.params['reps'])
        numctr = len(ctrticks)
        numticks = len(set(np.array(ctrticks).flatten()))
        [sig, ref] = self.pb.newctr_sigref  # index of the counters to divide as sig/ref => PL

        ctr_diff = np.diff(ctr_raw)

        ticks = [[]] * numticks

        for i in range(numticks-1):
            ticks[i] = ctr_diff[i::numticks]

        ctr_all = np.zeros((numctr, reps))

        for i in range(numctr):
            for j in range(ctrticks[i][0], ctrticks[i][1]):
                ctr_all[i][:] += ticks[j]

        pl = np.sum(ctr_all[sig][:]) / np.sum(ctr_all[ref][:])

        return [ctr_all, pl]

    def get_esr_data_newctr_raw(self, itr=0):
        numticks = len(set(np.array(self.pb.newctr_ctrticks).flatten()))  # Assume all ticks must be used
        reps = np.uint32(self.pb.params['reps'])

        self.ctr0.start()

        self.pb.set_program()

        # wait for pb to finish
        self.pb.wait_until_finished_thd(self)

        # Now that pulseblaster is finished. No more counter ticks should be received.
        # Just read out everything and check if the number of ticks are correct.
        # ctr_raw = self.ctr0.get_counts(num_ticks * np.uint32(self.pb.params['reps']))
        ctr_raw = self.ctr0.get_counts(numticks * reps)

        #  not needed since we are forcing the readout on all the counters after waiting for pulseblaster
        # self.ctr0.wait_until_done()
        try:
            self.ctr0.stop()
        except PyDAQmx.DAQmxFunctions.DAQError:
            if len(ctr_raw) != (numticks * reps):
                print('Did not acquire all the samples. Need to rerun the experiment.')
                if itr < 2:
                    return self.get_esr_data_newctr_raw(itr=itr+1)
                else:
                    self.log('Failed to acquire all samples twice. You are doing something wrong!')
            else:
                self.log('Unknown counter error!')

        return ctr_raw

    def sweep_esr_1d(self):
        xvar = self.var1
        # check if the endpoints are valid pulse parameters
        errorstring = ''
        est_total_time = 0
        if 'CW' not in self.mainexp.cbox_exp_name.currentText():
            try:
                if self.is_param_type(xvar, 'Pulse'):
                    for i in [0, -1]:
                        x_try = self.sweeprng1[i]
                        self.setval_wrapper(xvar, x_try)
                        errorstring = '%s = %E' % (xvar, x_try)
                        self.pb.set_program(autostart=0)
                        est_total_time += self.pb.seq_time[0][0]

                    est_total_time *= len(self.sweeprng1) / 2
                else:
                    errorstring = 'The already defined sequence'
                    self.pb.set_program(autostart=0)
                    est_total_time += self.pb.seq_time[0][0] * len(self.sweeprng1)

                est_total_time += self.delay1 * len(self.sweeprng1)

            except ValueError:
                self.log('Invalid sweep endpoints. %s not valid.' % errorstring)
                self.cancel = True

        self.mainexp.label_sweep_time_est.setText('Est. Time %d seconds.' % est_total_time)
        self.mainexp.esr_pause = False

        index = 0
        for x in self.sweeprng1:
            if not self.cancel:
                if index == 0:
                    warnings.simplefilter('ignore', RuntimeWarning)

                self.track_if_needed()

                self.setval_wrapper(xvar, x)

                if not self.cancel:
                    if not self.isPLE:
                        if index == 0:
                            time.sleep(self.delay2)
                        if not self.newctr:
                            data = self.get_esr_data(self.delay1)
                            if not self.use_pb:
                                self.esr_update_1d_cw(data, index)
                            else:
                                if not self.isINV2:
                                    self.esr_update_1d_pulse(data[0], data[1], data[2], index)
                                else:
                                    self.esr_update_1d_inv2(data[0], data[1], data[2], data[3],
                                                                              data[4], data[5], index)
                        else:  # newctr gating
                            data = self.get_esr_data_newctr(self.delay1)
                            if not self.newctr_2d:
                                data = [np.sum(data[0], axis=1), data[1]]
                            self.esr_update_1d_newctr(data, index)

                    else:
                        data = self.get_esr_data(self.delay1)
                        if self.use_pb:
                            data = data[0]  # take only sig for PLE
                        if self.ple_ref:
                            ref = self.ai.get_voltages(1)
                            tlb = getattr(self.mainexp, self.tlb_id)
                            ref = ref[0] * tlb.scale + tlb.offset
                        else:
                            ref = np.NaN
                        self.ple_update_1d(data, ref, index)

            index += 1

        if self.cancel:
            self.pb.stop()
            self.pb.set_cw()

    def sweep_esr_2d(self):
        xvar = self.var1
        yvar = self.var2

        # check if the endpoints are valid pulse parameters
        errorstring = ''
        est_total_time = 0
        if 'CW' not in self.mainexp.cbox_exp_name.currentText():
            try:
                if self.is_param_type(yvar, 'Pulse'):
                    for j in [0, -1]:
                        y_try = self.sweeprng2[j]
                        self.setval_wrapper(yvar, y_try)

                        if self.is_param_type(xvar, 'Pulse'):
                            for i in [0, -1]:
                                x_try = self.sweeprng1[i]
                                self.setval_wrapper(xvar, x_try)
                                errorstring = '%s = %E, %s = %E' % (xvar, x_try, yvar, y_try)
                                self.pb.set_program(autostart=0)
                                est_total_time += self.pb.seq_time[0][0]
                            est_total_time *= len(self.sweeprng1) / 2
                        else:
                            errorstring = '%s = %E' % (yvar, y_try)
                            self.pb.set_program(autostart=0)
                            est_total_time += self.pb.seq_time[0][0] * len(self.sweeprng1)

                    est_total_time *= len(self.sweeprng2) / 2

                else:
                    if self.is_param_type(xvar, 'Pulse'):
                        for i in [0, -1]:
                            x_try = self.sweeprng1[i]
                            self.setval_wrapper(xvar, x_try)
                            errorstring = '%s = %E' % (xvar, x_try)
                            self.pb.set_program(autostart=0)
                            est_total_time += self.pb.seq_time[0][0]
                        est_total_time *= len(self.sweeprng1) / 2
                    else:
                        errorstring = 'The already defined sequence'
                        self.pb.set_program(autostart=0)
                        est_total_time += self.pb.seq_time[0][0] * len(self.sweeprng1)
                    est_total_time *= len(self.sweeprng2)

            except ValueError:
                self.log('Invalid sweep endpoints. %s not valid.' % errorstring)
                self.cancel = True

        est_total_time += (len(self.sweeprng1)*self.delay1 + self.delay2)*len(self.sweeprng2)
        self.mainexp.label_sweep_time_est.setText('Est. Time %d seconds.' % est_total_time)

        if not self.cancel:
            index2 = 0

            for y in self.sweeprng2:
                if not self.cancel:
                    self.setval_wrapper(yvar, y)
                    time.sleep(self.delay2)

                    if self.meander and index2 % 2:
                        sweeprng1 = np.flip(self.sweeprng1, 0)
                        index1 = len(sweeprng1) - 1
                    else:
                        sweeprng1 = self.sweeprng1
                        index1 = 0

                    for x in sweeprng1:
                        if not self.cancel:
                            self.track_if_needed()

                            self.setval_wrapper(xvar, x)

                            if not self.cancel:
                                if not self.isPLE:
                                    data = self.get_esr_data(self.delay1)
                                    if not self.use_pb:
                                        self.esr_update_2d_cw(data, index1, index2)
                                    else:
                                        if not self.isINV2:
                                            self.esr_update_2d_pulse(data[0], data[1], data[2],
                                                                     index1, index2)
                                        else:
                                            self.esr_update_2d_inv2(data[0], data[1], data[2],
                                                                         data[3], data[4], data[5],
                                                                         index1, index2)
                                else:
                                    data = self.get_esr_data(self.delay1)
                                    if self.use_pb:
                                        data = data[0]  # take only sig for PLE

                                    if self.ple_ref:
                                        ref = self.ai.get_voltages(1)
                                        tlb = getattr(self.mainexp, self.tlb_id)
                                        ref = ref[0] * tlb.scale + tlb.offset
                                    else:
                                        ref = np.NaN
                                    self.ple_update_2d(data, ref, index1, index2)

                        if self.meander and index2 % 2:
                            index1 -= 1
                        else:
                            index1 += 1

                    self.lasttracktime = -1.0  # force tracking on the first point in the next row
                index2 += 1

            if self.cancel:
                self.pb.stop()
                self.pb.set_cw()

    def setup_ctr_timetrace(self, index2=None):
        # todo: use pulse duration from pulseblaster class
        self.ctr0.reset()
        self.ctrclk.reset()

        if not self.is2D:
            numpnts2 = 1
        else:
            if index2 is None:
                numpnts2 = len(self.sweeprng2)
            else:
                numpnts2 = len(self.sweeprng2) - index2

        self.ctr0.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'], PyDAQmx.DAQmx_Val_Rising,
                                   (len(self.sweeprng1) + 1)*np.uint32(self.pb.params['reps'])*numpnts2)

        self.ctrclk.set_freq(1000.0 / self.delay1)  # delay is in ms
        self.ctrclk.set_finite_samples(len(self.sweeprng1) + 1)
        self.ctrclk.set_start_trigger(self.mainexp.inst_params['instruments']['ctrapd2']['addr_gate'], PyDAQmx.DAQmx_Val_Rising)
        self.ctrclk.set_retriggerable(True)

    def sweep_timetrace_1d(self):
        ctr_total = np.zeros(len(self.sweeprng1))

        self.setup_ctr_timetrace()

        # Check whether to do super fast continuous sampling
        numpnts = (len(self.sweeprng1) + 1) * np.uint32(self.pb.params['reps'])
        bool_continuous_sampling = numpnts >= self.ctr0.cont_buffer_size

        self.ctr0.set_read_all_samples(bool_continuous_sampling)
        self.ctr0.start()
        self.ctrclk.start()

        self.pb.start_programming()
        self.pb.pulse_func(self.pb)
        self.pb.stop_programming()
        self.pb.start()

        if not bool_continuous_sampling:  # Read data trace by trace
            for i in range(np.uint32(self.pb.params['reps'])):
                if not self.cancel:
                    # Get data in chunks equal to the trace length
                    ctr_raw = self.ctr0.get_counts(len(self.sweeprng1) + 1)
                    ctr_read = np.diff(ctr_raw)
                    ctr_total += ctr_read
                    ctr_avg = ctr_total/(i+1)
                    pl = ctr_avg/self.delay1*1000
                    self.esr_update_1d_timetrace(ctr_total, pl)

        else:  # Read data as they are available
            n_read = 0
            ctr_buffer = np.array([])
            i = 0

            while not self.cancel and n_read < numpnts:
                ctr_raw = self.ctr0.get_counts(self.ctr0.cont_buffer_size)
                n_read += len(ctr_raw)
                ctr_buffer = np.append(ctr_buffer, ctr_raw)

                while len(ctr_buffer) >= (len(self.sweeprng1) + 1):
                    ctr_read = np.diff(ctr_buffer[0:len(self.sweeprng1) + 1])
                    ctr_buffer = ctr_buffer[len(self.sweeprng1) + 1:]
                    ctr_total += ctr_read
                    i += 1

                ctr_avg = ctr_total/i
                pl = ctr_avg/self.delay1*1000

                self.esr_update_1d_timetrace(ctr_total, pl)

        if not self.cancel:
            self.ctr0.stop()
        else:
            try:
                self.ctr0.stop()
            except PyDAQmx.DAQmxFunctions.DAQError:
                pass  # This is normal since we are stopping before it finishes

        self.pb.stop()

    def sweep_timetrace_2d(self):
        if self.var2 == 'itr':
            self.sweep_timetrace_2d_fast()
        else:
            self.sweep_timetrace_2d_slow()

    def sweep_timetrace_2d_fast(self):
        if not self.cancel:
            self.setup_ctr_timetrace()

            numpnts_1d = (len(self.sweeprng1) + 1) * np.uint32(self.pb.params['reps'])
            numpnts = numpnts_1d * len(self.sweeprng2)
            bool_continuous_sampling = numpnts >= self.ctr0.cont_buffer_size

            self.ctr0.set_read_all_samples(bool_continuous_sampling)
            self.ctr0.start()
            self.ctrclk.start()

            self.pb.start_programming()
            self.pb.pulse_func(self.pb)
            self.pb.stop_programming()
            self.pb.start()

        if not bool_continuous_sampling:  # Read data trace by trace
            for index2 in range(len(self.sweeprng2)):
                if not self.cancel:
                    if self.need_to_track():
                        try:
                            self.ctr0.stop()  # This could result in losing a few traces in the buffer
                        except PyDAQmx.DAQmxFunctions.DAQError:
                            pass  # This is normal since we are stopping before it finishes

                        self.track_if_needed()

                        if not self.cancel:
                            # This set up the counter to acquire the remaining lines, not the whole thing
                            if bool_continuous_sampling:
                                self.setup_ctr_timetrace()
                                self.ctr0.set_read_all_samples(bool_continuous_sampling)
                            else:
                                self.setup_ctr_timetrace(index2=index2)

                            self.ctr0.start()
                            self.ctrclk.start()

                            self.pb.start_programming()
                            self.pb.pulse_func(self.pb)
                            self.pb.stop_programming()
                            self.pb.start()

                    # # Ignore the 'itr' setting and delay time completely since we are doing fast scans
                    # self.setval_wrapper(self.var2, y)
                    # time.sleep(self.delay2)

                    ctr_total = np.zeros(len(self.sweeprng1))
                    pl = np.zeros(len(self.sweeprng1))

                    # todo: ignore reps since it's not ever useful in 2d mode?
                    for i in range(np.uint32(self.pb.params['reps'])):
                        if not self.cancel:
                            # Get data in chunks equal to the trace length
                            ctr_raw = self.ctr0.get_counts(len(self.sweeprng1) + 1)
                            ctr_read = np.diff(ctr_raw)
                            ctr_total += ctr_read
                            ctr_avg = ctr_total / (i + 1)
                            pl = ctr_avg / self.delay1 * 1000

                    self.esr_update_2d_timetrace(ctr_total, pl, index2)
        else:  # Read data as they are available
            n_read = 0
            ctr_buffer = np.array([])
            index2 = 0

            while not self.cancel and n_read < numpnts:
                ctr_raw = self.ctr0.get_counts(self.ctr0.cont_buffer_size)
                n_read += len(ctr_raw)
                ctr_buffer = np.append(ctr_buffer, ctr_raw)

                while len(ctr_buffer) >= numpnts_1d and index2 < len(self.sweeprng2):
                    ctr_1d_reps = np.reshape(ctr_buffer[0:numpnts_1d], (-1, len(self.sweeprng1) + 1))
                    ctr_total = np.sum(np.diff(ctr_1d_reps, axis=-1), axis=0)
                    pl = ctr_total / np.uint32(self.pb.params['reps']) / self.delay1 * 1000

                    ctr_buffer = ctr_buffer[numpnts_1d:]
                    self.esr_update_2d_timetrace(ctr_total, pl, index2)
                    index2 += 1

        if not self.cancel:
            self.ctr0.stop()
        else:
            try:
                self.ctr0.stop()
            except PyDAQmx.DAQmxFunctions.DAQError:
                pass  # This is normal since we are stopping before it finishes

        self.pb.stop()

    def sweep_timetrace_2d_slow(self):
        index2 = 0
        for y in self.sweeprng2:
            self.track_if_needed()

            if not self.cancel:
                self.setval_wrapper(self.var2, y)
                time.sleep(self.delay2)

                ctr_total = np.zeros(len(self.sweeprng1))

                self.setup_ctr_timetrace_1d()
                self.ctr0.start()
                self.ctrclk.start()

                self.pb.start_programming()
                self.pb.pulse_func(self.pb)
                self.pb.stop_programming()
                self.pb.start()

                for i in range(np.uint32(self.pb.params['reps'])):
                    if not self.cancel:
                        # Get data in chunks equal to the trace length
                        ctr_raw = self.ctr0.get_counts(len(self.sweeprng1) + 1)
                        ctr_read = np.diff(ctr_raw)
                        ctr_total += ctr_read
                        ctr_avg = ctr_total / (i + 1)
                        pl = ctr_avg / self.delay1 * 1000

                self.esr_update_2d_timetrace(ctr_total, pl, index2)

                if not self.cancel:
                    self.ctr0.stop()
                else:
                    try:
                        self.ctr0.stop()
                    except PyDAQmx.DAQmxFunctions.DAQError:
                        pass  # This is normal since we are stopping before it finishes

                self.pb.stop()

            index2 += 1

    def setup_ctr_ple(self):
        if not self.use_pb:
            self.ctr0.reset()
            self.ctrclk.reset()
            self.ctrtrig.set_time(0.001)
            self.ctrtrig.reset()

            self.ao.reset()
            self.ai.reset()

            self.ctr0.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                       PyDAQmx.DAQmx_Val_Rising,
                                       len(self.sweeprng1) + 1)
            self.ctr0.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                            PyDAQmx.DAQmx_Val_Rising)

            self.ai.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.sweeprng1) + 1)
            self.ai.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                      PyDAQmx.DAQmx_Val_Rising)

            self.ao.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising,
                                     len(self.sweeprng1) + 1)
            self.ao.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                      PyDAQmx.DAQmx_Val_Rising)

            self.ctrclk.set_freq(1 / self.delay1)
            self.ctrclk.start()

        else:  # pulsed PLE
            self.ctr0.reset()
            self.ctr1.reset()
            self.ctrtrig.set_time(0.001)
            self.ctrtrig.reset()

            self.ao.reset()
            self.ai.reset()

            self.ctr0.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd']['addr_gate'])
            self.ctr0.set_sample_clock(self.mainexp.inst_params['instruments']['ctrapd3']['addr_gate'], PyDAQmx.DAQmx_Val_Rising,
                                       len(self.sweeprng1) + 1)
            self.ctr0.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                            PyDAQmx.DAQmx_Val_Rising)

            self.ctr1.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
            self.ctr1.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrapd2']['addr_gate'])
            self.ctr1.set_sample_clock(self.mainexp.inst_params['instruments']['ctrapd3']['addr_gate'], PyDAQmx.DAQmx_Val_Rising,
                                       len(self.sweeprng1) + 1)
            self.ctr1.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                            PyDAQmx.DAQmx_Val_Rising)

            self.ai.set_sample_clock(self.mainexp.inst_params['instruments']['ctrapd3']['addr_gate'], PyDAQmx.DAQmx_Val_Rising,
                                     len(self.sweeprng1) + 1)
            self.ai.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'], PyDAQmx.DAQmx_Val_Rising)

            self.ao.set_sample_clock(self.mainexp.inst_params['instruments']['ctrapd3']['addr_gate'], PyDAQmx.DAQmx_Val_Rising,
                                     len(self.sweeprng1) + 1)
            self.ao.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'], PyDAQmx.DAQmx_Val_Rising)

    def sweep_ple_1d_cw(self, rev=False, yindex=0):
        vlist = self.sweeprng1
        if rev:
            vlist = np.flipud(vlist)

        vlist = np.append(vlist, vlist[-1])

        self.ao.reset()
        self.ao.set_voltage(vlist[0])
        time.sleep(self.delay2)
        self.setup_ctr_ple()
        self.ao.set_voltages(vlist)

        # arm ao, ai, apd
        self.ao.start()
        self.ai.start()
        self.ctr0.start()

        if not self.is2D and self.use_wm:  # get wavemeter reading here if it isnt a 2d experiment
            self.mainexp.wmFreq = self.mainexp.wavemeter.getLambda()
            self.log("Laser Freq = %.3f (GHz)" % self.mainexp.wmFreq)

        # trigger
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        # Read the first point anyway
        ctr_raw = self.ctr0.get_counts(1)
        ai_read = self.ai.get_voltages(1)

        # Delete the first ai reading
        n_chan = len(self.ai.dev.split(','))
        for ch in reversed(range(n_chan)):
            # takes care of the case where ai_read contains multiple channels
            ai_read = np.delete(ai_read, ch * len(ai_read) / n_chan)

        n_read = 1
        t_update = 0.1
        numpnts1 = len(self.sweeprng1)
        last_counter = ctr_raw[-1]  # Actual counter value, monotonically counts up, need to be diff

        self.ctr0.set_read_all_samples(True)
        self.ai.set_read_all_samples(True)

        while not self.cancel and n_read < len(vlist):
            time.sleep(t_update)
            # Just try to read the entire array.
            ctr_raw = self.ctr0.get_counts(numpnts1)
            if len(ctr_raw):
                # Read ai for the same amount for synchronized display
                ai_read = self.ai.get_voltages(len(ctr_raw))
                ctr_diff = np.diff(np.append([last_counter], ctr_raw)) / self.delay1

                tlb = getattr(self.mainexp, self.tlb_id)
                ai_read_scaled = ai_read * tlb.scale + tlb.offset

                # Append the data to the array
                if not rev:
                    start = n_read - 1
                    end = n_read -1 +len(ctr_diff)
                else:
                    start = numpnts1 - n_read + 1 - len(ctr_diff)
                    end = numpnts1 - n_read + 1
                    ctr_diff = np.flipud(ctr_diff)
                    ai_read_scaled = np.flipud(ai_read_scaled)

                if not self.is2D:
                    self.mainexp.esrtrace_pl[start:end] = ctr_diff
                    for ch in range(n_chan):
                        self.mainexp.esrtrace_ref[ch * numpnts1 + start:ch * numpnts1 + end] = ai_read_scaled
                else:
                    self.mainexp.esrtrace_pl[start:end, yindex] = ctr_diff
                    for ch in range(n_chan):
                        self.mainexp.esrtrace_ref[ch * numpnts1 + start:ch * numpnts1 + end, yindex] = ai_read_scaled

                n_read += len(ctr_raw)
                last_counter = ctr_raw[-1]

        if hasattr(PyDAQmx.DAQmxFunctions, 'DAQWarning'):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',
                                      PyDAQmx.DAQmxFunctions.DAQWarning)  # for ignoring warnings when plotting NaNs

                self.ctrclk.stop()
                self.ctrclk.reset()
                try:
                    self.ao.stop()
                    self.ctr0.stop()
                    self.ai.stop()
                except PyDAQmx.DAQmxFunctions.DAQError:
                    # It is normal for the PyDAQmx to throw an error when stopped prematurely
                    pass
                self.ao.reset()
                self.ctr0.reset()
                self.ai.reset()

        self.ao.reset()
        self.setval_wrapper(self.var1, vlist[-1])

    def sweep_ple_1d_pulse(self, rev=False, yindex=0):
        vlist = self.sweeprng1
        if rev:
            vlist = np.flipud(vlist)

        vlist = np.append(vlist, vlist[-1])

        self.ao.reset()
        self.ao.set_voltage(vlist[0])
        time.sleep(self.delay2)
        self.setup_ctr_ple()
        self.ao.set_voltages(vlist)

        # arm ao, ai, apd
        self.ao.start()
        self.ai.start()
        self.ctr0.start()
        self.ctr1.start()

        # trigger
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        # now ao, ai, ctr0 are started but they will not start outputting/acquiring until receive clock signal from pb

        # set number of points for pb
        # start pulseblaster sequence

        # # ignore this, run pb in infinite loop, and stop pb after reading counters?
        # self.setval_wrapper('numpnts', len(self.sweeprng1) + 1)

        self.pb.start_programming()
        # Use ctr2 (ctrapd3) as clock signal

        line_start = self.pb.add_inst(['ctr2'], self.pb.inst_set.CONTINUE, 0, 1e-6)  # This is dead time at the beginning of the pixel
        self.pb.pulse_func(self.pb)  # Pulse sequence for each pixel
        self.pb.add_inst([], self.pb.inst_set.BRANCH, line_start, 1e-6)  # This is dead time at the end of the pixel
        self.pb.stop_programming()
        self.pb.start()

        # Read the first point anyway
        ctr0_raw = self.ctr0.get_counts(1)
        ctr1_raw = self.ctr1.get_counts(1)
        ai_read = self.ai.get_voltages(1)

        # Delete the first ai reading
        n_chan = len(self.ai.dev.split(','))
        for ch in reversed(range(n_chan)):
            # takes care of the case where ai_read contains multiple channels
            ai_read = np.delete(ai_read, ch * len(ai_read) / n_chan)

        n_read = 1
        t_update = 0.1
        numpnts1 = len(self.sweeprng1)
        last_counter0 = ctr0_raw[-1]  # Actual counter value, monotonically counts up, need to be diff
        last_counter1 = ctr1_raw[-1]  # Actual counter value, monotonically counts up, need to be diff

        self.ctr0.set_read_all_samples(True)
        self.ctr1.set_read_all_samples(True)
        self.ai.set_read_all_samples(True)

        while not self.cancel and n_read < len(vlist):
            time.sleep(t_update)
            # Just try to read the entire array.
            ctr0_raw = self.ctr0.get_counts(numpnts1)
            if len(ctr0_raw):
                # Read ai for the same amount for synchronized display
                ctr1_raw = self.ctr1.get_counts(len(ctr0_raw))
                ai_read = self.ai.get_voltages(len(ctr0_raw))
                n_chan = len(self.ai.dev.split(','))

                ctr0_diff = np.diff(np.append([last_counter0], ctr0_raw))
                ctr1_diff = np.diff(np.append([last_counter1], ctr1_raw))

                tlb = getattr(self.mainexp, self.tlb_id)
                ai_read_scaled = ai_read * tlb.scale + tlb.offset

                # Append the data to the array
                if not rev:
                    start = n_read - 1
                    end = n_read - 1 + len(ctr0_diff)
                else:
                    start = numpnts1 - n_read + 1 - len(ctr0_diff)
                    end = numpnts1 - n_read + 1
                    ctr0_diff = np.flipud(ctr0_diff)
                    ai_read_scaled = np.flipud(ai_read_scaled)

                # todo: use ctr1
                if not self.is2D:
                    self.mainexp.esrtrace_pl[start:end] = ctr0_diff
                    for ch in range(n_chan):
                        self.mainexp.esrtrace_ref[ch * numpnts1 + start:ch * numpnts1 + end] = ai_read_scaled
                else:
                    self.mainexp.esrtrace_pl[start:end, yindex] = ctr0_diff
                    for ch in range(n_chan):
                        self.mainexp.esrtrace_ref[ch * numpnts1 + start:ch * numpnts1 + end, yindex] = ai_read_scaled

                n_read += len(ctr0_raw)
                last_counter0 = ctr0_raw[-1]
                last_counter1 = ctr1_raw[-1]

        if hasattr(PyDAQmx.DAQmxFunctions, 'DAQWarning'):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', PyDAQmx.DAQmxFunctions.DAQWarning)  # for ignoring warnings when plotting NaNs

                self.ctrclk.stop()
                self.ctrclk.reset()
                try:
                    self.ao.stop()
                    self.ctr0.stop()
                    self.ctr1.stop()
                    self.ai.stop()
                except PyDAQmx.DAQmxFunctions.DAQError:
                    # It is normal for the PyDAQmx to throw an error when stopped prematurely
                    pass
                self.ao.reset()
                self.ctr0.reset()
                self.ctr1.reset()
                self.ai.reset()

        self.pb.stop()

        self.ao.reset()
        self.setval_wrapper(self.var1, vlist[-1])

    def sweep_ple_2d_cw(self):
        yvar = self.var2

        if self.use_wm:
            self.mainexp.wmFreq = np.zeros(np.size(self.sweeprng2))

        if not self.cancel:
            index2 = 0
            for y in self.sweeprng2:
                self.track_if_needed()
                if not self.cancel:
                    self.setval_wrapper(yvar, y)
                    time.sleep(self.delay2)
                if self.use_wm:
                    # get wavemeter reading
                    self.mainexp.wmFreq[index2] = self.mainexp.wavemeter.getLambda()
                    self.log("Laser Freq = %.3f (GHz)" % self.mainexp.wmFreq[index2])
                if not self.cancel:
                    self.sweep_ple_1d_cw(rev=False, yindex=index2)
                if not self.cancel and self.meander:
                    self.sweep_ple_1d_cw(rev=True, yindex=index2 + len(self.sweeprng2))

                index2 += 1

    def sweep_ple_2d_pulse(self):
        yvar = self.var2

        if not self.cancel:
            index2 = 0
            for y in self.sweeprng2:
                if not self.cancel:
                    self.track_if_needed()
                if not self.cancel:
                    self.setval_wrapper(yvar, y)
                    time.sleep(self.delay2)
                if not self.cancel:
                    self.sweep_ple_1d_pulse(rev=False, yindex=index2)
                if not self.cancel and self.meander:
                    self.sweep_ple_1d_pulse(rev=True, yindex=index2 + len(self.sweeprng2))

                index2 += 1

    def setval_wrapper(self, var_name, val):
        if self.is_param_type(var_name, 'Manual'):
            self.signal_sweep_setval_manual_prompt.emit(var_name, val)
            self.mainexp.mutex.lock()
            try:
                self.mainexp.wait_manual_setval.wait(self.mainexp.mutex)
            finally:
                self.mainexp.mutex.unlock()

            if not self.cancel and self.mainexp.chkbx_tracker_period.isChecked():
                self.track(1)

        if not self.cancel:
            self.mainexp.task_handler.setval(var_name, val, log=False)

    def need_to_track(self):
        # Update the track_period and bool_period - this allows changing parameters while scan is running
        track_period = self.mainexp.dbl_tracker_period.value() * 60
        bool_period = self.mainexp.chkbx_tracker_period.isChecked()
        # Add 10s to the calculation so it doesn't end up tracking every point
        # except for when track_period == 0, the user is definitely trying to track every point
        if track_period > 1:
            track_period = track_period + 10

        return (time.time() - self.lasttracktime > track_period) and bool_period

    def track_if_needed(self):
        if self.need_to_track():
            self.pb.set_cw()
            self.track()

            # backup experiment, except at the beginning when it is empty
            if self.mainexp.chkbx_autosave.isChecked() and self.lasttracktime > -1.0:
                self.save_exp()

            self.lasttracktime = time.time()

    def track(self, numtrack=1):
        self.mainexp.thread_tracker.numtrack = numtrack
        self.mainexp.thread_tracker.start()
        self.mainexp.thread_tracker.wait()

        self.set_mainexp_gui()

        if not self.isPLE:
            self.setup_ctr_esr()

    def cleanup(self):
        if not self.isPLE:
            self.cleanup_esr()
        else:
            self.cleanup_ple()

    def cleanup_esr(self):
        self.signal_sweep_esr_updateplots_stop.emit()
        self.signal_sweep_esr_updateplots.emit()
        self.wait_for_mainexp()

        self.mainexp.log('%s finished at %s' % (self.mainexp.label_filename.text(),
                                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        if self.mainexp.chkbx_autosave.isChecked():
            self.save_exp()

        self.mainexp.set_gui_btn_enable('all', True)
        self.mainexp.set_gui_input_enable('exp', True)
        self.mainexp.btn_exp_stop.setEnabled(False)

        # turn off all microwave sources
        for entry in self.mainexp.exp_params['Instrument']:
            if 'freq' in entry:
                ins = entry[:-4]
                getattr(getattr(self.mainexp, ins), 'set_output')(0)

        self.mainexp.update_inst_stat()
        self.ctr0.reset()
        self.ctr1.reset()
        self.ctr2.reset()
        self.ctr3.reset()
        self.ctrclk.reset()
        self.ctrtrig.reset()

        # if one of the sweep variable in a 2d sweep is itr, integrate it (conditioning is done in integrate_esr())
        self.integrate_esr()

        if self.mainexp.cbox_fittype.currentText() != '' and not self.is2D and self.mainexp.chkbx_exp_autofit.isChecked():
            self.dofit()
            if self.mainexp.chkbx_autosave.isChecked():
                self.save_exp()

    def integrate_esr(self):
        if 'itr' in [self.var1, self.var2] and self.is2D and self.mainexp.chkbx_autosave.isChecked():
            # Basically create another sweep with the correct parameters and feed in the integrated data
            self.is2D = False

            if self.var1 == 'itr':
                int_dir = 0
                self.mainexp.task_handler.swap_sweep_var()
            else:
                int_dir = 1

            # This is basically a dummy sweep doing data averaging.
            if not self.use_pb:
                self.mainexp.esrtrace_pl = np.nanmean(self.mainexp.esrtrace_pl, axis=int_dir)
            else:
                if True:
                    self.mainexp.esrtrace_sig = np.nansum(self.mainexp.esrtrace_sig, axis=int_dir)
                    self.mainexp.esrtrace_ref = np.nansum(self.mainexp.esrtrace_ref, axis=int_dir)

                if self.isINV2:
                    self.mainexp.esrtrace_sig2 = np.nansum(self.mainexp.esrtrace_sig2, axis=int_dir)
                    self.mainexp.esrtrace_ref2 = np.nansum(self.mainexp.esrtrace_ref2, axis=int_dir)

                if 'timetrace' not in self.mainexp.cbox_exp_name.currentText():
                    if not self.isINV:
                        if True:
                            if True:
                                self.mainexp.esrtrace_pl = np.divide(self.mainexp.esrtrace_sig, self.mainexp.esrtrace_ref)
                            if self.pl_norm:
                                self.mainexp.esrtrace_pl = (self.mainexp.esrtrace_pl - self.pl_dark) /\
                                                           (self.pl_bright - self.pl_dark)
                        if self.isINV2:
                            if True:
                                self.mainexp.esrtrace_pl2 = np.divide(self.mainexp.esrtrace_sig2, self.mainexp.esrtrace_ref2)
                            if self.pl_norm:
                                self.mainexp.esrtrace_pl2 = (self.mainexp.esrtrace_pl2 - self.pl_dark) / \
                                                            (self.pl_bright - self.pl_dark)
                    else:
                        if True:
                            if True:
                                self.mainexp.esrtrace_pl = np.divide(np.float64(self.mainexp.esrtrace_sig) - np.float64(self.mainexp.esrtrace_ref),
                                                                     np.float64(self.mainexp.esrtrace_sig) + np.float64(self.mainexp.esrtrace_ref))

                            if self.pl_norm:
                                self.mainexp.esrtrace_pl = self.mainexp.esrtrace_pl /\
                                                           (self.pl_bright - self.pl_dark) * (self.pl_bright + self.pl_dark)
                        if self.isINV2:
                            if True:
                                self.mainexp.esrtrace_pl2 = np.divide(np.float64(self.mainexp.esrtrace_sig2) - np.float64(self.mainexp.esrtrace_ref2),
                                                                      np.float64(self.mainexp.esrtrace_sig2) + np.float64(self.mainexp.esrtrace_ref2))

                            if self.pl_norm:
                                self.mainexp.esrtrace_pl2 = self.mainexp.esrtrace_pl2 /\
                                                            (self.pl_bright - self.pl_dark) * (self.pl_bright + self.pl_dark)
                else:
                    self.mainexp.esrtrace_pl = self.mainexp.esrtrace_sig / self.mainexp.var1_delay.value() * 1000 / self.mainexp.var2_numdivs.value()

            self.signal_sweep_esr_initplots.emit()
            self.signal_sweep_esr_updateplots.emit()

            self.wait_for_mainexp()

            datacode = 'PL'
            axiscode = self.mainexp.var1_name.currentText()

            # save this integrated trace. might as well create a new serial number
            filename = '%s%s_%d' % (datacode, axiscode, self.mainexp.wavenum)
            self.mainexp.label_filename.setText(filename)

            self.wait_for_mainexp()

            self.save_exp()

    def cleanup_ple(self):
        self.signal_sweep_ple_updateplots_stop.emit()
        self.signal_sweep_ple_updateplots.emit()
        self.wait_for_mainexp()

        self.mainexp.log('%s finished at %s' % (self.mainexp.label_filename.text(),
                                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        if self.mainexp.chkbx_autosave.isChecked():
            self.save_exp()

        self.mainexp.set_gui_btn_enable('all', True)
        self.mainexp.set_gui_input_enable('esr', True)
        self.mainexp.btn_exp_stop.setEnabled(False)

        for tlb in self.mainexp.tlblist:
            getattr(self.mainexp, '%s_ai' % tlb).reset()
            getattr(self.mainexp, '%s_ao' % tlb).reset()
        self.ctr0.reset()
        self.ctr1.reset()
        self.ctr2.reset()
        self.ctr3.reset()
        self.ctrclk.reset()
        self.ctrtrig.reset()

    def save_exp(self, ext=False):
        time.sleep(0.1)  # fix the issue of the graph not finish updating

        if self.isRunning() and not ext:
            self.signal_sweep_grab_screenshots.emit()
            self.wait_for_mainexp()
            time.sleep(0.1)
        else:  # For use when save_exp is called from a button
            self.mainexp.sweep_grab_screenshots()

        graph = self.mainexp.pixmap_sweep_graph
        fig = self.mainexp.pixmap_sweep_fig

        self.mainexp.export_sweep_settings(sweep_var=True)

        filename = self.mainexp.label_filename.text()
        exp_name = self.mainexp.cbox_exp_name.currentText()

        # Start Building Metadata file
        # Copy the dictionary of exp_params first, then add other parameters to save
        sweep_params = dict((k, v) for k, v in self.mainexp.exp_params.items())

        # sweep_params pull var1 and var2 info from the GUI to take care of flipping axes in integrate_esr()
        # is2D is taken from Sweep since this is properly taken care of with integrate_esr() - allows repeating sweep
        sweep_params['Sweep'] = {'pulsename': exp_name,
                                 'var1_name': self.mainexp.var1_name.currentText(),
                                 'var1_start': self.mainexp.var1_start.value(),
                                 'var1_start_unit': self.mainexp.var1_stop_unit.currentText(),
                                 'var1_stop': self.mainexp.var1_stop.value(),
                                 'var1_stop_unit': self.mainexp.var1_stop_unit.currentText(),
                                 'var1_numdivs': self.mainexp.var1_numdivs.value(),
                                 'var1_delay': self.mainexp.var1_delay.value(),
                                 'var2_name': self.mainexp.var2_name.currentText(),
                                 'var2_start': self.mainexp.var2_start.value(),
                                 'var2_start_unit': self.mainexp.var2_start_unit.currentText(),
                                 'var2_stop': self.mainexp.var2_stop.value(),
                                 'var2_stop_unit': self.mainexp.var2_stop_unit.currentText(),
                                 'var2_numdivs': self.mainexp.var2_numdivs.value(),
                                 'var2_delay': self.mainexp.var2_delay.value(),
                                 'is_pb': self.use_pb,
                                 'is_inv': self.isINV,
                                 'is_norm': self.pl_norm,
                                 'chxbx_2desr': self.is2D}

        sweep_params['readout_params'] = dict((k, v) for k, v in self.pb.readout_params.items())
        try:
            sweep_params['readout_params'].update({'p532': self.mainexp.pm100d.get_pow()*1e3})
        except:
            pass

        if 'orange' in exp_name and self.sweep_finished:
            if hasattr(self.mainexp, 'pm100d_orange'):
                self.mainexp.log('Turning on Orange Laser to measure power.')
                self.mainexp.log('Waiting 10 seconds to stabilize...')
                self.pb.set_cw_custom(['orange'])
                time.sleep(10)
                sweep_params['readout_params'].update({'p590': self.mainexp.pm100d_orange.get_pow() * 1e3})
                self.mainexp.pb.set_cw()
                self.mainexp.log('Finished Orange Laser measurements.')
            else:
                sweep_params['readout_params'].update({'p590': 0})

        sweep_params['sample'] = self.mainexp.linein_sample_name.text()

        # Start Building Data File
        data_dict = {'pl': self.mainexp.esrtrace_pl}

        if self.use_pb:
            if not self.newctr:
                data_dict.update({'sig': self.mainexp.esrtrace_sig,
                                  'ref': self.mainexp.esrtrace_ref})
                if self.isINV2:
                    data_dict.update({'sig2': self.mainexp.esrtrace_sig2,
                                      'ref2': self.mainexp.esrtrace_ref2,
                                      'pl2': self.mainexp.esrtrace_pl2})
            else:
                data_dict.update({'ctr': self.mainexp.esrtrace_newctr})

        if self.isPLE:
            data_dict.update({'ref': self.mainexp.esrtrace_ref})
        if self.use_wm:
            data_dict.update({'wmFreq': self.mainexp.wmFreq})
        if True:
            data_dict.update({'xvals': self.mainexp.esr_rngx})
        if self.mainexp.thread_sweep.is2D:
            data_dict.update({'yvals': self.mainexp.esr_rngy})

        self.save_data(filename, data_dict, graph=graph, fig=fig, sweep_params=sweep_params)

    def dofit(self, ext=False):
        fitter_name = self.mainexp.cbox_fittype.currentText()

        # for compatibility with both conventions of fit_sin and sin
        if 'fit_' in fitter_name:
            func = fitter_name[4:]
        else:
            func = fitter_name

        self.fitter.set_function(func)

        self.fitter.set_data(self.mainexp.esrtrace_pl, self.mainexp.esr_rngx)

        try:
            fp = self.fitter.dofit()
            [fit_x, fit_y] = self.fitter.get_fitcurve_smooth()

            if fitter_name == 'fit_sin':
                timevect = self.fitter.fitter.get_pulsetimes()
                self.log('pi/2, pi, 3pi/2 pulse times are %.2f ns, %.2f ns, %.2f ns'
                                           % (timevect[0]*1e9, timevect[1]*1e9, timevect[2]*1e9))
            elif fitter_name == 'fit_expdecay':
                self.log('T2 = %.2f us, n = 1' % (fp[1]*1e6))
            elif fitter_name == 'fit_powerdecay':
                self.log('T2 = %.2f us, n = %.1f' % (fp[2]*1e6, fp[1]))
            elif fitter_name == 'fit_lorentzian':
                self.log('freq = %.3f MHz' % (fp[1]/1e6))

            self.mainexp.esr_fitx = fit_x
            self.mainexp.esr_fity = fit_y

            fit_results = ''
            fit_results += func
            fit_results += '\r---------'

            params = self.fitter.params()

            for i in range(len(params)):
                fit_results += '\r'
                fit_results += '%s: %.4e' % (params[i], fp[i])

            self.signal_sweep_fits_update.emit(fit_results)

            if self.isRunning() and not ext:
                self.wait_for_mainexp()
        except:
            self.log('Unable to fit: either RuntimeError or ValueError. Need better catching.')

        return self.fitter.fitter

    # Data manipulation

    def esr_update_1d_cw(self, val, index):
        self.mainexp.esrtrace_pl[index] = val

    def esr_update_1d_pulse(self, sig, ref, pl, index):
        self.mainexp.esrtrace_sig[index] = sig
        self.mainexp.esrtrace_ref[index] = ref
        self.mainexp.esrtrace_pl[index] = pl

    def esr_update_1d_inv2(self, sig, ref, pl, sig2, ref2, pl2, index):
        self.mainexp.esrtrace_sig[index] = sig
        self.mainexp.esrtrace_ref[index] = ref
        self.mainexp.esrtrace_pl[index] = pl
        self.mainexp.esrtrace_sig2[index] = sig2
        self.mainexp.esrtrace_ref2[index] = ref2
        self.mainexp.esrtrace_pl2[index] = pl2

    def esr_update_1d_timetrace(self, total, pl):
        self.mainexp.esrtrace_ref = np.zeros(len(total))
        self.mainexp.esrtrace_sig = total
        self.mainexp.esrtrace_pl = pl

    def esr_update_1d_newctr(self, data, index):
        self.mainexp.esrtrace_pl[index] = data[1]

        numctr = len(self.pb.newctr_ctrticks)

        # plot the counts for each counter
        if not self.newctr_2d:
            for i in range(numctr):
                self.mainexp.esrtrace_newctr[i][index] = data[0][i]
        else:
            for i in range(numctr):
                self.mainexp.esrtrace_newctr[i][index][:] = data[0][i][:]

    def esr_update_2d_cw(self, val, x, y):
        self.mainexp.esrtrace_pl[x][y] = val

    def esr_update_2d_pulse(self, sig, ref, pl, x, y):
        self.mainexp.esrtrace_sig[x][y] = sig
        self.mainexp.esrtrace_ref[x][y] = ref
        self.mainexp.esrtrace_pl[x][y] = pl

    def esr_update_2d_inv2(self, sig, ref, pl, sig2, ref2, pl2, x, y):
        self.mainexp.esrtrace_sig[x][y] = sig
        self.mainexp.esrtrace_ref[x][y] = ref
        self.mainexp.esrtrace_pl[x][y] = pl
        self.mainexp.esrtrace_sig2[x][y] = sig2
        self.mainexp.esrtrace_ref2[x][y] = ref2
        self.mainexp.esrtrace_pl2[x][y] = pl2

    def esr_update_2d_timetrace(self, total, pl, index):
        for i in range(len(pl)):
            self.mainexp.esrtrace_pl[i][index] = pl[i]
            self.mainexp.esrtrace_sig[i][index] = total[i]

    def ple_update_1d(self, pl, ref, index):
        self.mainexp.esrtrace_pl[index] = pl
        self.mainexp.esrtrace_ref[index] = ref

    def ple_update_2d(self, pl, ref, x, y):
        self.mainexp.esrtrace_pl[x][y] = pl
        self.mainexp.esrtrace_ref[x][y] = ref
