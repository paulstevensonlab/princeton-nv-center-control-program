from PyQt5.QtCore import pyqtSignal
import fitters
import numpy as np
import time, PyDAQmx
from . import ExpThread
import datetime

class Tracker(ExpThread.ExpThread):

    # Define signals for communicating with mainexp
    signal_tracker_updateplot = pyqtSignal(int)
    signal_tracker_updateplot_freq = pyqtSignal(str)
    signal_tracker_updatelog = pyqtSignal(float, float)
    signal_tracker_updatecursor = pyqtSignal()

    def __init__(self, mainexp):  # Tracker does not need wait_condition
        super().__init__(mainexp)

        self.galpie = mainexp.galpie
        self.ctrapd = mainexp.ctrapd
        self.ctrclk = mainexp.ctrclk
        self.ctrtrig = mainexp.ctrtrig

        self.fitter = fitters.fit_tracker()
        self.fitter_z = fitters.fit_tracker_z()

        self.numtrack = 1  # number of times to track on a spot
        self.logdata = True  # record to the history the position, laser power, PL (only record at the end of multiple tracks)
        self.piezo_delay = 0.5  # time delay after setting piezo
        self.freq_delay = 0.5

        self.tracker_pos = []
        self.tracker_rng = []
        self.tracker_numdivs = 0
        self.tracker_acqtime = 0.0
        self.tracker_pltime = 0.0
        self.tracker_freq_numdivs = 0.0
        self.tracker_freq_acqtime = 0.0

        self.tracker_finished_func = None  # Function(s) to be executed after tracking (to resume something)

        self.signal_tracker_updateplot.connect(mainexp.tracker_updateplot)
        self.signal_tracker_updateplot_freq.connect(mainexp.tracker_updateplot_freq)
        self.signal_tracker_updatelog.connect(mainexp.tracker_updatelog)
        self.signal_tracker_updatecursor.connect(mainexp.map_updatecursor)

    def update_mainexp(self):
        mainexp = self.mainexp

        self.tracker_pos = [mainexp.dbl_tracker_xpos.value(),
                            mainexp.dbl_tracker_ypos.value(),
                            mainexp.dbl_tracker_zpos.value()]
        self.tracker_rng = [mainexp.dbl_tracker_xrng.value(),
                            mainexp.dbl_tracker_yrng.value(),
                            mainexp.dbl_tracker_zrng.value()]
        self.tracker_numdivs = mainexp.int_tracker_numdivs.value()
        self.tracker_acqtime = mainexp.dbl_tracker_acqtime.value()
        self.tracker_pltime = mainexp.dbl_tracker_pltime.value()

        self.tracker_freq_numdivs = mainexp.int_tracker_freq_numdivs.value()
        self.tracker_freq_acqtime = mainexp.dbl_tracker_freq_acqtime.value()

    def sweep_pos(self, direction):
        # direction should be 0, 1 or 2
        # range should be scan range in microns
        # lower level function which will be called by the tracker
        scanrng = np.linspace(self.tracker_pos[direction] - self.tracker_rng[direction],
                              self.tracker_pos[direction] + self.tracker_rng[direction],
                              self.tracker_numdivs + 1)
        # one more point added at end because we do np.diff which reduces vector size by 1
        scanrng = np.append(scanrng, scanrng[-1])

        # reset the counters and ao
        self.galpie.reset()
        self.ctrapd.reset()
        self.ctrclk.reset()
        self.ctrtrig.reset()

        if direction == 2:
            self.galpie.set_position(2, scanrng[0])
            time.sleep(self.piezo_delay)

        # set up the swept voltage analog channel
        self.galpie.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        self.galpie.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                      PyDAQmx.DAQmx_Val_Rising)

        # setup the counters to acquire and gate properly
        self.mainexp.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                              PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        self.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                   PyDAQmx.DAQmx_Val_Rising)
        self.ctrclk.set_freq(1 / self.tracker_acqtime)

        # sweep this direction over scanrng
        self.galpie.set_positions(direction, scanrng)
        self.galpie.start()

        # start the counters, and measure
        self.ctrapd.start()
        self.ctrclk.start()
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        ctr_raw = self.ctrapd.get_counts(len(scanrng))
        # continually incrementing counter, so np.diff (which reduces size by 1)
        ctr_read = np.diff(ctr_raw) / self.tracker_acqtime

        self.galpie.wait_until_done()
        self.ctrapd.wait_until_done()
        self.galpie.stop()
        self.ctrclk.stop()
        self.ctrapd.stop()

        # output the tracker counters in the unit of kcps
        return [scanrng[0:-1], (ctr_read/1000)]

    def track_pos(self, direction):
        [xvals, data] = self.sweep_pos(direction)

        try:
            self.fitter.set_data(data, xvals=xvals)
            fp = self.fitter.dofit()
            fitdata = self.fitter.get_fitcurve()
            peakcenter = fp[1]
            peakwidth = np.abs(fp[2])
            peak_sig = fp[0]**2
            peak_offset = fp[3]

            print('%s sig: %.2f, bkg: %.2f, ratio: %.2f, width: %.2e\n' % (datetime.datetime.now(), peak_sig, peak_offset, peak_sig/peak_offset, peakwidth))

            tol = 1.5  # how far out of scanning range the optimal point can be
            if abs(peakcenter - np.mean(xvals)) > abs(xvals[0] - xvals[-1])/2 * tol:
                # print('Optimal Point outside of %f times the range' % tol)
                # print('Setting to mid range')
                newpos = np.mean(xvals)
            else:
                newpos = peakcenter
        except RuntimeError:
            # print('optimal parameters not found, setting to mid range')
            newpos = self.tracker_pos[direction]
            fitdata = np.ones(self.tracker_numdivs + 1) * np.mean(data)

        return [xvals, data, fitdata, np.round(newpos * 1000.0) / 1000.0]

    # Zhiyang modified for two peak fitting in z-direction
    # def track_pos(self, direction):
    #     [xvals, data] = self.sweep_pos(direction)
    #
    #     try:
    #         if direction == 2:
    #             self.fitter_z.set_data(data, xvals=xvals)
    #             fp = self.fitter_z.dofit()
    #             fitdata = self.fitter_z.get_fitcurve()
    #             peakcenter = min(fp[1], fp[4])
    #             tol = 1.5  # how far out of scanning range the optimal point can be
    #             if abs(peakcenter - np.mean(xvals)) > abs(xvals[0] - xvals[-1]) / 2 * tol:
    #                 # print('Optimal Point outside of %f times the range' % tol)
    #                 # print('Setting to mid range')
    #                 newpos = np.mean(xvals)
    #             else:
    #                 newpos = peakcenter
    #         else:
    #             self.fitter.set_data(data, xvals=xvals)
    #             fp = self.fitter.dofit()
    #             fitdata = self.fitter.get_fitcurve()
    #             peakcenter = fp[1]
    #             tol = 1.5  # how far out of scanning range the optimal point can be
    #             if abs(peakcenter - np.mean(xvals)) > abs(xvals[0] - xvals[-1])/2 * tol:
    #                 # print('Optimal Point outside of %f times the range' % tol)
    #                 # print('Setting to mid range')
    #                 newpos = np.mean(xvals)
    #             else:
    #                 newpos = peakcenter
    #     except RuntimeError:
    #         # print('optimal parameters not found, setting to mid range')
    #         newpos = self.tracker_pos[direction]
    #         fitdata = np.ones(self.tracker_numdivs + 1) * np.mean(data)
    #
    #     return [xvals, data, fitdata, np.round(newpos * 1000.0) / 1000.0]

    def set_pos(self, direction, pos):
        if direction == 2:  # For piezo, do a ramp to avoid hysteresis
            rampvals = np.linspace(self.tracker_pos[direction] - self.tracker_rng[direction], pos, self.tracker_numdivs + 1)

            # move to initial position and wait
            self.galpie.set_position(2, rampvals[0])
            time.sleep(self.piezo_delay)

            self.galpie.reset()
            self.ctrapd.reset()
            self.ctrclk.reset()
            self.ctrtrig.reset()

            self.galpie.set_sample_clock('/Dev1/PFI7', PyDAQmx.DAQmx_Val_Rising, len(rampvals))
            self.galpie.set_start_trigger('/Dev1/PFI2', PyDAQmx.DAQmx_Val_Rising)
            self.ctrtrig = self.ctrtrig
            self.ctrclk.set_freq(1 / self.tracker_acqtime)
            self.galpie.set_positions(2, rampvals.tolist())

            # start the counters, and measure
            self.ctrclk.start()
            self.ctrtrig.start()
            self.ctrtrig.wait_until_done()
            self.ctrtrig.stop()

            self.galpie.wait_until_done()
            self.galpie.stop()
            self.ctrclk.stop()

        self.galpie.reset()
        self.galpie.set_position(direction, pos)

    def get_pl(self):
        if self.tracker_pltime > 0.001:
            # Reset the counter back to single shot mode
            self.ctrapd.reset()
            self.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
            self.ctrclk.reset()
            self.ctrtrig.reset()

            self.ctrapd.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'])

            self.ctrapd.start()
            self.ctrtrig.set_time(self.tracker_pltime)
            self.ctrtrig.start()
            self.ctrtrig.wait_until_done()
            self.ctrtrig.stop()
            pl = self.ctrapd.get_count() / self.tracker_pltime / 1000.0
            self.ctrapd.stop()
        else:
            pl = np.nan

        return pl

    def sweep_wavemeter(self):
        # range should be scan range in GHz
        # first get the current voltage for scanning the range
        voltage_current = self.mainexp.ctlfreq.get_piezo()
        rng = getattr(self.mainexp, 'dbl_tracker_ctlfreq_rng').value()
        scanrng = np.linspace(-rng, +rng, self.tracker_freq_numdivs + 1)

        # one more point added at end because we do np.diff which reduces vector size by 1,
        # the ctlfreq.scale make sure that the number we set corresponds to GHz.
        scanrng = np.append(scanrng, scanrng[-1]) * self.mainexp.ctlfreq.scale + voltage_current

        freq_current = self.mainexp.ctlfreq.get_freq()

        # reset the counters and ao
        self.mainexp.ctlfreq.piezo_ao.reset()
        self.ctrapd.reset()
        self.ctrclk.reset()
        self.ctrtrig.reset()
        print('current freq is ', freq_current)
        self.mainexp.ctlfreq.piezo_ao.set_position(scanrng[0])
        time.sleep(self.freq_delay)

        # set up the swept voltage analog channel
        self.mainexp.ctlfreq.piezo_ao.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                               PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        self.mainexp.ctlfreq.piezo_ao.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                                PyDAQmx.DAQmx_Val_Rising)

        # setup the counters to acquire and gate properly
        self.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        self.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                          PyDAQmx.DAQmx_Val_Rising)
        self.ctrclk.set_freq(1 / self.tracker_freq_acqtime)
        # set to the first point of the scan range and get the start and end freq for calibration.

        freq_start = self.mainexp.ctlfreq.get_freq()
        print('Track freq start at: %f', freq_start)
        # sweep this direction over scanrng
        self.mainexp.ctlfreq.piezo_ao.set_positions(scanrng)
        self.mainexp.ctlfreq.piezo_ao.start()

        # start the counters, and measure
        self.ctrapd.start()
        self.ctrclk.start()
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        ctr_raw = self.ctrapd.get_counts(len(scanrng))
        # continually incrementing counter, so np.diff (which reduces size by 1)
        ctr_read = np.diff(ctr_raw) / self.tracker_freq_acqtime

        self.mainexp.ctlfreq.piezo_ao.wait_until_done()
        self.ctrapd.wait_until_done()
        self.mainexp.ctlfreq.piezo_ao.stop()
        self.ctrclk.stop()
        self.ctrapd.stop()

        freq_end = self.mainexp.ctlfreq.get_freq()
        print('Track freq end at: %f', freq_end)

        # Use three points, current, start, end, to correct for nonlinearity in frequency
        begin = np.linspace(freq_start, freq_current, int(self.tracker_freq_numdivs/2), endpoint=False)
        mid = np.array([freq_current])
        end = np.flip(np.linspace(freq_end, freq_current, int(self.tracker_freq_numdivs/2), endpoint=False))
        scanrng_freq = np.append(begin, mid)
        scanrng_freq = np.append(scanrng_freq, end)
        # Convert to relative frequency for convinience in fitting and display
        scanrng_freq = scanrng_freq - freq_current

        # output the tracker counters in the unit of kcps
        return [scanrng_freq, (ctr_read/1000)]

    def track_wavemeter(self):
        [xvals, data] = self.sweep_wavemeter()

        try:
            self.fitter.set_data(data, xvals)
            fp = self.fitter.dofit()
            fitdata = self.fitter.get_fitcurve()
            peakcenter = fp[1]
            tol = 1.5  # how far out of scanning range the optimal point can be
            if abs(peakcenter) > getattr(self.mainexp, 'dbl_tracker_ctlfreq_rng') * tol:
                # print('Optimal Point outside of %f times the range' % tol)
                # print('Setting to mid range')
                newpos = 0
            else:
                newpos = peakcenter
        except RuntimeError:
            # print('optimal parameters not found, setting to mid range')
            newpos = 0
            fitdata = np.ones(self.tracker_freq_numdivs + 1) * np.mean(data)

        return [xvals, data, fitdata, np.round(newpos * 1000.0) / 1000.0]

    def sweep_tlb(self, laser_name):
        ao = getattr(self.mainexp, laser_name + '_ao')
        volt_per_ghz = getattr(self.mainexp, laser_name).scale
        v = ao.get_voltage()
        frng = getattr(self.mainexp, 'dbl_tracker_%s_rng' % laser_name).value()
        scanrng = np.linspace(v - frng * volt_per_ghz, v + frng * volt_per_ghz,
                              self.tracker_freq_numdivs + 1)
        # one more point added at end because we do np.diff which reduces vector size by 1
        scanrng = np.append(scanrng, scanrng[-1])

        # reset the counters and ao
        ao.reset()
        self.ctrapd.reset()
        self.ctrclk.reset()
        self.ctrtrig.reset()
        ao.set_voltage(scanrng[0])
        time.sleep(self.freq_delay)

        # set up the swept voltage analog channel
        ao.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                 PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        ao.set_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                              PyDAQmx.DAQmx_Val_Rising)

        # setup the counters to acquire and gate properly
        self.ctrapd.set_sample_clock(self.mainexp.inst_params['instruments']['ctrclk']['addr_out'],
                                     PyDAQmx.DAQmx_Val_Rising, len(scanrng))
        self.ctrapd.set_arm_start_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'],
                                          PyDAQmx.DAQmx_Val_Rising)
        self.ctrclk.set_freq(1 / self.tracker_freq_acqtime)
        # sweep this direction over scanrng
        ao.set_voltages(scanrng)
        ao.start()

        # start the counters, and measure
        self.ctrapd.start()
        self.ctrclk.start()
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()

        ctr_raw = self.ctrapd.get_counts(len(scanrng))
        # continually incrementing counter, so np.diff (which reduces size by 1)
        ctr_read = np.diff(ctr_raw) / self.tracker_freq_acqtime

        ao.wait_until_done()
        self.ctrapd.wait_until_done()
        ao.stop()
        self.ctrclk.stop()
        self.ctrapd.stop()

        # output the tracker counters in the unit of kcps
        return [scanrng[0:-1], (ctr_read / 1000)]
    
    def track_tlb(self, laser_name):
        [xvals, data] = self.sweep_tlb(laser_name)

        try:
            self.fitter.set_data(data, xvals)
            fp = self.fitter.dofit()
            fitdata = self.fitter.get_fitcurve()
            peakcenter = fp[1]
            tol = 1.5  # how far out of scanning range the optimal point can be

            if abs(peakcenter - np.mean(xvals)) > abs(xvals[0] - xvals[-1])/2 * tol:
                # print('Optimal Point outside of %f times the range' % tol)
                # print('Setting to mid range')
                newpos = np.mean(xvals)
            else:
                newpos = peakcenter
        except RuntimeError:
            # print('optimal parameters not found, setting to mid range')
            newpos = np.mean(xvals)
            fitdata = np.ones(self.tracker_freq_numdivs + 1) * np.mean(data)

        return [xvals, data, fitdata, np.round(newpos * 1000.0) / 1000.0]

    def run(self):
        self.update_mainexp()

        self.run_script('tracker_init.py')

        dir_name = ['xpos', 'ypos', 'zpos']

        for _ in range(self.numtrack):
            self.galpie.set_position([0, 1, 2], self.tracker_pos)
            time.sleep(self.piezo_delay)

            for direction in range(3):
                if self.tracker_rng[direction] > 0.001:  # if the range is  nonzero
                    [xvals, data, fitdata, pos] = self.track_pos(direction)
                    self.set_pos(direction, pos)

                    self.mainexp.trace_tracker_xvals[direction] = xvals
                    self.mainexp.trace_tracker_yvals[direction] = np.array(data)
                    self.mainexp.trace_tracker_yfit[direction] = np.array(fitdata)
                    getattr(self.mainexp, 'dbl_tracker_%s' % dir_name[direction]).setValue(pos)
                    self.mainexp.exp_params['Confocal'][dir_name[direction]] = float(pos)
                else:  # spit out empty arrays to plot to make it obvious that it's not tracking
                    numpnts = self.tracker_numdivs + 1
                    self.mainexp.trace_tracker_xvals[direction] = np.empty(numpnts)*np.NaN
                    self.mainexp.trace_tracker_yvals[direction] = np.empty(numpnts)*np.NaN
                    self.mainexp.trace_tracker_yfit[direction] = np.empty(numpnts)*np.NaN
                    self.mainexp.exp_params['Confocal'][dir_name[direction]] = float(self.tracker_pos[direction])

                self.signal_tracker_updateplot.emit(direction)

        for laser_name in self.mainexp.tlblist:
            if getattr(self.mainexp, 'dbl_tracker_%s_rng' % laser_name).value() > 0.001:  # if the range is  nonzero
                [xvals, data, fitdata, pos] = self.track_tlb(laser_name)
                ao = getattr(self.mainexp, laser_name + '_ao')
                ao.reset()
                ao.set_voltage(pos)
                setattr(self.mainexp, 'trace_tracker_%s_xvals' % laser_name, xvals)
                setattr(self.mainexp, 'trace_tracker_%s_yvals' % laser_name, np.array(data))
                setattr(self.mainexp, 'trace_tracker_%s_yfit' % laser_name, np.array(fitdata))
                self.mainexp.exp_params['Instrument'][laser_name + 'piezo'] = pos
            else:  # spit out empty arrays to plot to make it obvious that it's not tracking
                numpnts = self.tracker_freq_numdivs + 1
                setattr(self.mainexp, 'trace_tracker_%s_xvals' % laser_name, np.empty(numpnts)*np.NaN)
                setattr(self.mainexp, 'trace_tracker_%s_yvals' % laser_name, np.empty(numpnts)*np.NaN)
                setattr(self.mainexp, 'trace_tracker_%s_yfit' % laser_name, np.empty(numpnts)*np.NaN)

            self.signal_tracker_updateplot_freq.emit(laser_name)

        # for tracking the PLE frequency, set the direction to be 4.
        if hasattr(self.mainexp, 'wavemeter') and self.mainexp.wavemeter.isconnected and hasattr(self.mainexp, 'ctlfreq'):
            frng = getattr(self.mainexp, 'dbl_tracker_ctlfreq_rng').value()
            if self.mainexp.wavemeter.isconnected and frng > 0.001:  # if the frequency track range is nonzero
                [xvals, data, fitdata, pos] = self.track_wavemeter()
                self.mainexp.ctlfreq.piezo_ao.reset()
                self.mainexp.ctlfreq.set_freq(pos)
                setattr(self.mainexp, 'trace_tracker_ctlfreq_xvals', xvals)
                setattr(self.mainexp, 'trace_tracker_ctlfreq_yvals', np.array(data))
                setattr(self.mainexp, 'trace_tracker_ctlfreq_yfit', np.array(fitdata))
                self.mainexp.exp_params['Instrument']['ctlfreqwm'] = pos
            else:  # spit out empty arrays to plot to make it obvious that it's not tracking
                numpnts = self.tracker_freq_numdivs + 1
                setattr(self.mainexp, 'trace_tracker_ctlfreq_xvals', np.empty(numpnts)*np.NaN)
                setattr(self.mainexp, 'trace_tracker_ctlfreq_yvals', np.empty(numpnts)*np.NaN)
                setattr(self.mainexp, 'trace_tracker_ctlfreq_yfit', np.empty(numpnts)*np.NaN)

            self.signal_tracker_updateplot_freq.emit('ctlfreq')

        if self.logdata:
            pl = self.get_pl()
            try:
                p532 = self.mainexp.pm100d.get_pow() * 1e3
            except:
                p532 = np.nan
            self.signal_tracker_updatelog.emit(pl, p532)
        else:
            self.logdata = True

        self.signal_tracker_updatecursor.emit()

        self.numtrack = 1

        self.mainexp.ctrapd.reset()
        self.mainexp.ctrclk.reset()
        self.mainexp.ctrtrig.reset()
        self.mainexp.galpie.reset()
        self.mainexp.set_gui_btn_enable('all', True)
        self.mainexp.set_gui_input_enable('tracker', True)

        # todo: this is hard-coded and should be deleted
        if self.mainexp.chkbx_tracker_flip.isChecked():
            self.mainexp.flip1.write(not self.mainexp.flip1.track_state)
            time.sleep(0.55)  # wait period for flipper to flip (transit time set to 500ms in APT User software

        time.sleep(self.mainexp.dbl_tracker_wait.value())    # for UHV z-tracking
        if self.tracker_finished_func is not None:
            if not isinstance(self.tracker_finished_func, list):
                self.tracker_finished_func()
            else:
                for func in self.tracker_finished_func:
                    func()
            self.tracker_finished_func = None

        self.run_script('tracker_finish.py')
