import instruments as instr
import numpy as np
import math as math
import time
import warnings


class PulseMaster:

    def __init__(self, pb=None, awg=[], pb_dict={}):
        if pb is None:
            # TODO: add error handling
            pb = instr.PulseBlaster.PBESRPro()
            pb.pb_init()
            pb.pb_core_clock(500 * pb.constants['MHz'])

        # dictionary for storing pbnum, key, inversion
        self.pb_dict = pb_dict
        self.tracker_laser = ['green']

        self.pulse_func = self.pb_default
        self.pulse_name = 'default'
        self.pb = pb
        self.awg = awg
        for awgnum in range(len(self.awg)):
            setattr(self, 'awg_wfm%d' % awgnum, [np.array([]), np.array([])])
        self.awg_enable = False
        self.awg_srate = 250e6
        self.custom_readout = False
        self.params_readoutcal_enable = False  # enable the readout pulse parameters. e.g. aom_delay
        self.params_repump_enable = False  # enable the repumping and readout lasers control

        self.readout_params = {'aom_delay': 800e-9,
                               'awg_offset': -200e-9,
                               'awg_preedge': 80e-9,
                               'awg_postedge': 20e-9,
                               'mw_delay': 20e-9,
                               'time_dark': 1000e-9,
                               'time_green': 3e-6,
                               'time_det': 300e-9,
                               'time_sep': 1000e-9,
                               'aom2_delay': 800e-9,
                               'time_initial': 100e-9}

        self.params = self.default_params()
        self.isINV = False
        self.isINV2 = False
        self.newctr = False
        self.newctr_ctrticks = [[0, 1], [2, 3]]  # ticks to subtract for each counter
        self.newctr_sigref = [0, 1]  # index of the counters to divide as sig/ref => PL

    def set_pb_dict(self, d):
        self.pb_dict = d

    def default_params(self):
        self.params_repump_enable = False
        self.custom_readout = False

        params = {'reps': 1e5}
        if self.params_readoutcal_enable:
            params.update(self.readout_params)
        return params

    def repump_params(self):
        self.params_repump_enable = True

        return {'pulsewidth_repumping': 50e-9,
                'pulsewidth_readout': 50e-9,
                'repumping_delay': 700e-9,
                'readout_delay': 850e-9,
                'tau_repump': 50e-9,
                'reps': 1e3}

        # todo: add time_det

    def set_pulse(self, pulse_name):
        try:
            self.pulse_func = getattr(self, ('pb_'+pulse_name))
            getattr(self, ('pb_'+pulse_name)+'_params')()
            self.pulse_name = pulse_name
            self.awg_enable = 'awg' in pulse_name
        except AttributeError:
            print(pulse_name+" is not configured.")

    def pulse_func_inv(self, inv):
        self.params['inv'] = inv
        self.pulse_func()

    def pulse_func_inv2(self, inv, inv2):
        # just assume we'd do inv if inv2 is selected
        self.params['inv'] = inv
        self.params['inv2'] = inv2
        self.pulse_func()

    def pb_default(self):
        print('no function is defined')

    def pb_aomdelay_params(self):
        self.params = self.default_params()
        self.params.update({'aomdelay': 1e-6, 'timedetect': 5e-7, 'timedark':5e-6})
        self.custom_readout = True

    def pb_aomdelay(self):
        loop_start = self.add_inst(['green'], self.pb.inst_set.LOOP, self.params['reps'],self.params['aomdelay'])
        self.add_inst(['ctr0', 'green','ctr1'], self.pb.inst_set.CONTINUE, 0, self.params['timedetect'])
        self.add_inst([''], self.pb.inst_set.END_LOOP, loop_start, self.params['timedark'])
        self.add_inst(['green'], self.pb.inst_set.STOP, 0, 1e-6)

    def pb_odmr_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 100e-6, 'tau': 100e-6})
        self.custom_readout = True

    def pb_odmr(self):
        loop_start = self.add_inst(['green', 'ctr1'], self.pb.inst_set.LOOP, self.params['reps'], self.params['tau'])
        self.add_inst(['green', 'mw1', 'ctr0'], self.pb.inst_set.END_LOOP, loop_start, self.params['pulsewidth'])
        self.add_inst(['green'], self.pb.inst_set.STOP, 0, 1e-6)

    def pb_odmr2_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 100e-6, 'tau': 100e-6})
        self.custom_readout = True

    def pb_odmr2(self):
        loop_start = self.add_inst(['green', 'ctr1'], self.pb.inst_set.LOOP, self.params['reps'], self.params['tau'])
        self.add_inst(['green', 'mw2', 'ctr0'], self.pb.inst_set.END_LOOP, loop_start, self.params['pulsewidth'])
        self.add_inst(['green'], self.pb.inst_set.STOP, 0, 1e-6)

    def pb_rabi_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})

    def pb_rabi(self):
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

    def pb_rabi2_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})

    def pb_rabi2(self):
        self.add_inst(['mw2'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

    def pb_orangeread_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 100e-9, 'reps': 1e3, 'tau': 1000e-9, 'orangeread': 1})
        self.custom_readout = True

    def pb_orangeread(self):
        pb = self.pb
        if self.params_readoutcal_enable:
            for key in self.readout_params.keys():
                self.readout_params[key] = self.params[key]

        aom_delay = self.readout_params['aom_delay']
        mw_delay = self.readout_params['mw_delay']
        time_dark = self.readout_params['time_dark']
        time_green = self.readout_params['time_green']
        time_det = self.readout_params['time_det']
        time_sep = self.readout_params['time_sep']
        aom2_delay = self.readout_params['aom2_delay']
        time_initial = self.readout_params['time_initial']

        n_loops = int(self.params['reps'])
        outer_loop = self.add_inst([], pb.inst_set.LOOP, n_loops, mw_delay)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_initial)
        self.add_inst([], pb.inst_set.CONTINUE, 0, aom_delay)
        self.add_inst(['orange'], pb.inst_set.CONTINUE, 0, aom2_delay)
        self.add_inst(['orange', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det)
        self.add_inst(['orange'], pb.inst_set.CONTINUE, 0, time_green - time_det - aom2_delay)
        self.add_inst([], pb.inst_set.CONTINUE, 0, time_sep - (time_green - time_det - aom2_delay))
        self.add_inst(['ctr1'], pb.inst_set.CONTINUE, 0, time_det)
        self.add_inst([], pb.inst_set.END_LOOP, outer_loop,
                      time_dark - time_det - mw_delay - (time_sep - (time_green - time_det - aom2_delay)))
        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay)
        self.add_inst(['orange'], pb.inst_set.STOP, 0, 1e-6)

    def pb_timetrace_orange_params(self):
        self.params = self.default_params()
        self.params.update({'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_orange': 25e-3, 't_end': 1e-6, 'reps': 1e3, 'timetrace': 0.0})

    def pb_timetrace_orange(self):
        # todo: move the headers elsewhere?
        self.pb.pb_start_programming(self.pb.PULSE_PROGRAM)

        self.add_inst(['ctr1'], self.pb.inst_set.CONTINUE, 0, self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
        self.add_inst(['green'], self.pb.inst_set.CONTINUE, 0, self.params['t_green'])
        self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['t_wait'])
        self.add_inst(['orange'], self.pb.inst_set.CONTINUE, 0, self.params['t_orange'])
        self.add_inst([], self.pb.inst_set.BRANCH, 0, self.params['t_end'])

        self.pb.pb_stop_programming()
        # self.pb.pb_start()

    def pb_newctr_rabi_params(self):
        self.newctr_ctrticks = [[0, 1], [2, 3]]
        self.newctr_sigref = [0, 1]
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})

    def pb_newctr_rabi(self):
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

    def pb_newctr_rabi_chargestate_params(self):
        self.newctr_ctrticks = [[0, 1], [2, 3], [4, 5]]
        self.newctr_sigref = [1, 2]
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0, 't_orange': 1e-3, 't_orange_dark': 2e-6})
        self.custom_readout = True

    def pb_newctr_rabi_chargestate(self):
        pb = self.pb

        reps = self.params['reps']

        n_inner_loops = 100
        n_loops = math.floor(reps / n_inner_loops)

        awglist = ['scope']  # Trigger the scope where the AWG is supposed to start
        if self.awg_enable:
            for awg in self.awg:
                awglist.append(awg.alias)

        if self.params_readoutcal_enable:
            for key in self.readout_params.keys():
                self.readout_params[key] = self.params[key]

        aom_delay = self.readout_params['aom_delay']
        awg_offset = self.readout_params['awg_offset']
        mw_delay = self.readout_params['mw_delay']
        time_dark = self.readout_params['time_dark']
        time_green = self.readout_params['time_green']
        time_det = self.readout_params['time_det']
        time_sep = self.readout_params['time_sep']
        time_trig = 20e-9  # todo: make it adjustable via gui

        # use manually trimmed readout pulse to speed up some short sequences, e.g. Rabi
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
        self.add_inst(awglist, pb.inst_set.CONTINUE, 0,
                      time_dark - (2 * time_det + time_sep - (time_green - aom_delay)))
        outer_loop = self.add_inst([], pb.inst_set.LOOP, n_loops,
                                   (2 * time_det + time_sep - (time_green - aom_delay)))
        if self.awg_enable:
            self.clear_inst_awg()
        # do charge state readout
        self.add_inst(['orange', 'ctr0'], self.pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['orange'], self.pb.inst_set.CONTINUE, 0, self.params['t_orange']-time_trig)
        self.add_inst(['ctr0'], self.pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['t_orange_dark']-time_trig)
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])
        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay)
        inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst([], pb.inst_set.CONTINUE, 0,
                      time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
        if self.awg_enable:
            self.clear_inst_awg()
        # do charge state readout
        self.add_inst(['orange', 'ctr0'], self.pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['orange'], self.pb.inst_set.CONTINUE, 0, self.params['t_orange']-time_trig)
        self.add_inst(['ctr0'], self.pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['t_orange_dark']-time_trig)
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])
        self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay)

        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
        self.add_inst([], pb.inst_set.END_LOOP, outer_loop,
                      time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
        self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)

    def pb_awg_rabi_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'vi': 0.0, 'vq': 0.0, 'reps': 1e5, 'tau': 0.0})

    def pb_awg_rabi(self):
        self.add_inst_awg('awg1', [self.params['vi'], self.params['vq']], self.params['pulsewidth'])
        self.add_inst_awg([], [], self.params['tau'])

    def pb_t1_params(self):
        self.pb_rabi_params()
        self.params.update({'inv': 0})

    def pb_t1(self):
        if np.uint32(self.params['inv']) == 0:
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        else:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])

        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

    def pb_DQ_t1_params(self):
        self.pb_rabi_params()
        self.params.update({'inv': 0})

    def pb_DQ_t1(self):
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

        if np.uint32(self.params['inv']) == 0:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        else:
            self.add_inst(['mw2'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])

    def pb_SQ_t1_params(self):
        self.pb_rabi_params()
        self.params.update({'inv': 0})

    def pb_SQ_t1(self):
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])
        if np.uint32(self.params['inv']) == 0:
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        else:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])

    def pb_cal_xx_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 20e-9, 'n': 1, 'inv': 0})

    def pb_cal_xx(self):
        numpulses = np.uint32(self.params['n']) + np.uint32(self.params['inv'])

        for i in range(numpulses):
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth'])
            if i != numpulses - 1:
                self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau'])

    def pb_awg_cal_xx_params(self):
        self.params = self.default_params()
        self.params.update({'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'reps': 1e5, 'tau': 20e-9, 'n': 1, 'inv': 0})

    def pb_awg_cal_xx(self):
        numpulses = np.uint32(self.params['n']) + np.uint32(self.params['inv'])

        for i in range(numpulses):
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            if i != numpulses - 1:
                self.add_inst_awg([], [], self.params['tau'])

    def pb_awg_cal_xy_params(self):
        self.params = self.default_params()
        self.params.update({'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'y180pw': 20e-9, 'y180vi': 0.0, 'y180vq': 0.0,
                            'reps': 1e5, 'tau': 20e-9, 'n': 1, 'inv': 0})

    def pb_awg_cal_xy(self):
        numpulses = np.uint32(self.params['n']) + np.uint32(self.params['inv'])

        for i in range(numpulses):
            if not i%2:  # X
                self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            else:
                self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            if i != numpulses - 1:
                self.add_inst_awg([], [], self.params['tau'])

    def pb_awg_cal_bootstrap_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 28e-9, 'x90vi': 300.0, 'x90vq': 0.0,
                            'y90pw': 28e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'x180pw': 56e-9, 'x180vi': 300.0, 'x180vq': 0.0,
                            'y180pw': 56e-9, 'y180vi': 0.0, 'y180vq': 300.0,
                            'reps': 1e5, 'tau': 20e-9, 'seq': 1})

    def pb_awg_cal_bootstrap(self):
        int_seq = np.uint32(self.params['seq'])

        if int_seq == 1:  # X90
            self.add_inst_awg1_x90()
        elif int_seq == 2:  # Y90
            self.add_inst_awg1_y90()
        elif int_seq == 3:  # X90 - X180
            self.add_inst_awg1_x90()
            self.add_inst_tau()
            self.add_inst_awg1_x180()
        elif int_seq == 4:  # Y90 - Y180
            self.add_inst_awg1_y90()
            self.add_inst_tau()
            self.add_inst_awg1_y180()
        elif int_seq == 5:  # Y180 - X90
            self.add_inst_awg1_y180()
            self.add_inst_tau()
            self.add_inst_awg1_x90()
        elif int_seq == 6:  # X180 - Y90
            self.add_inst_awg1_x180()
            self.add_inst_tau()
            self.add_inst_awg1_y90()
        elif int_seq == 7:  # Y90 - X90
            self.add_inst_awg1_y90()
            self.add_inst_tau()
            self.add_inst_awg1_x90()
        elif int_seq == 8:  # X90 - Y90
            self.add_inst_awg1_x90()
            self.add_inst_tau()
            self.add_inst_awg1_y90()
        elif int_seq == 9:  # X90 - X180 - Y90
            self.add_inst_awg1_x90()
            self.add_inst_tau()
            self.add_inst_awg1_x180()
            self.add_inst_tau()
            self.add_inst_awg1_y90()
        elif int_seq == 10:  # Y90 - X180 - X90
            self.add_inst_awg1_y90()
            self.add_inst_tau()
            self.add_inst_awg1_x180()
            self.add_inst_tau()
            self.add_inst_awg1_x90()
        elif int_seq == 11:  # X90 - Y180 - Y90
            self.add_inst_awg1_x90()
            self.add_inst_tau()
            self.add_inst_awg1_y180()
            self.add_inst_tau()
            self.add_inst_awg1_y90()
        elif int_seq == 12:  # Y90 - Y180 - X90
            self.add_inst_awg1_y90()
            self.add_inst_tau()
            self.add_inst_awg1_y180()
            self.add_inst_tau()
            self.add_inst_awg1_x90()

    def add_inst_awg1_x90(self):
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])

    def add_inst_awg1_y90(self):
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    def add_inst_awg1_x180(self):
        self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])

    def add_inst_awg1_y180(self):
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])

    def add_inst_tau(self):
        self.add_inst_awg([], [], self.params['tau'])

    def pb_awg_cpmg_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'r180pw': 20e-9, 'r180vi': 0.0, 'r180vq': 0.0,
                            'reps': 1e5, 'tau': 0.0, 'n': 1, 'inv': 0})

    def pb_awg_cpmg(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['n'])):
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
            self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_xy2_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'y180pw': 20e-9, 'y180vi': 0.0, 'y180vq': 0.0, 'reps': 1e5, 'tau': 0.0, 'k': 1, 'inv': 0})

    def pb_awg_xy2(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])

    def pb_awg_xy4_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'y180pw': 20e-9, 'y180vi': 0.0, 'y180vq': 0.0, 'reps': 1e5, 'tau': 0.0, 'k': 1, 'inv': 0})

    def pb_awg_xy4(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_xy8_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'y180pw': 20e-9, 'y180vi': 0.0, 'y180vq': 0.0, 'reps': 1e5, 'tau': 0.0, 'k': 1, 'inv': 0})

    def pb_awg_xy8(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

        # redundant programming:
        # program with awgonly at first to build awg waveform
        # then program pulseblaster loop -- this is to avoid limitation on pulseblaster instructions
        #
        # AWG Programming only
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2, awgonly=True)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], awgonly=True)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2, awgonly=True)
        #
        # Pulseblaster Programming only
        if True:
            # X
            start_xy8 = self.add_inst([], self.pb.inst_set.LOOP, np.uint32(self.params['k']), self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['x180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['y180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['x180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['y180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
            # Y
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['y180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
            # X
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['x180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
            # Y
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['y180pw'])
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
            # X
            self.add_inst([], self.pb.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['x180pw'])
            self.add_inst([], self.pb.inst_set.END_LOOP, start_xy8, self.params['tau'] / 2 - self.params['x180pw'] / 2)
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_xy16_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'x180pw': 20e-9, 'x180vi': 0.0, 'x180vq': 0.0,
                            'y180pw': 20e-9, 'y180vi': 0.0, 'y180vq': 0.0, 'reps': 1e5, 'tau': 0.0, 'k': 1, 'inv': 0})

    def pb_awg_xy16(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)

            # -X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [-self.params['x180vi'], -self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # -Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [-self.params['y180vi'], -self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # -X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [-self.params['x180vi'], -self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # -Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [-self.params['y180vi'], -self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # -Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [-self.params['y180vi'], -self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # -X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [-self.params['x180vi'], -self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # -Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [-self.params['y180vi'], -self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # -X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [-self.params['x180vi'], -self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_xy8_reporter_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 40e-9, 'x90vi': 300.0, 'x90vq': 0.0, 'y90pw': 40e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'x180pw': 80e-9, 'x180vi': 300.0, 'x180vq': 0.0, 'y180pw': 80e-9, 'y180vi': 0.0, 'y180vq': 300.0,
                            'reps': 1e5, 'tau': 0.0, 'tau_p': 0.0, 'k': 1, 'inv': 0})

    def pb_awg_xy8_reporter(self):
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

        # Free Precession
        self.add_inst_awg([], [], self.params['tau_p'])

        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])

    def pb_awg_xy8_interp_params(self):
        self.pb_awg_xy8_params()

    def pb_awg_xy8_interp(self):
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

        # Quantum Interpolation: arXiv:1604.01677
        tau2_ns = round(self.params['tau']/2*1e9)
        t0 = round(4e-9 * int(tau2_ns/4), 9)  # building block U0
        t1 = round(4e-9 * int(tau2_ns/4 + 1), 9)  # building block U1

        m = 0
        sample = float(tau2_ns % 4)/4.0  # fraction of 4ns awg sampling time

        # todo: add error checking for too high of sampling rate
        # Q-interpolation can only improve resolution to 1/4k = 1/k ns

        for j in range(4*np.uint32(self.params['k'])):
            m += sample

            if abs(m) <= 0.5:
                t = t0
            else:
                t = t1
                m -= 1.0

            if j % 4 == 0 or j % 4 == 1:
                # X
                self.add_inst_awg([], [], t - self.params['x180pw'] / 2)
                self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
                self.add_inst_awg([], [], t - self.params['x180pw'] / 2)
                # Y
                self.add_inst_awg([], [], t - self.params['y180pw'] / 2)
                self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
                self.add_inst_awg([], [], t - self.params['y180pw'] / 2)
            else:
                # Y
                self.add_inst_awg([], [], t - self.params['y180pw'] / 2)
                self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
                self.add_inst_awg([], [], t - self.params['y180pw'] / 2)
                # X
                self.add_inst_awg([], [], t - self.params['x180pw'] / 2)
                self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
                self.add_inst_awg([], [], t - self.params['x180pw'] / 2)

        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_qurep_init_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 48e-9, 'x90vi': 300.0, 'x90vq': 0.0,
                            'y90pw': 48e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'y180pw': 96e-9, 'y180vi': 0.0, 'y180vq': 300.0,
                            'reps': 2e6, 'tau': 720e-9, 'dt': 52e-9})

    def pb_awg_qurep_init(self):
        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=['mw1','mw2'])
        self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        # Y90
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
        self.add_inst_awg([], [], self.params['dt'])

    def pb_awg_qurep_readout_params(self):
        self.pb_awg_qurep_init_params()
        self.params.update({'inv': 0})

    def pb_awg_qurep_readout(self):
        # wait for mw1 to turn on
        self.add_inst_awg([], [], self.params['dt'])

        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=['mw1','mw2'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)

        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    def pb_awg_qurep_rabi_params(self):
        self.pb_awg_qurep_init_params()
        self.pb_awg_qurep_readout_params()  # this overwrites the awg_qurep_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9, 'deerpulsewidth': 36e-9})

    def pb_awg_qurep_rabi(self):
        self.pb_awg_qurep_init()

        # pulse on DEER
        self.add_inst_awg([], [], self.params['deerpulsewidth'], customflags=['mw2'])
        # wait for tau_p
        self.add_inst_awg([], [], self.params['tau_p'])

        self.pb_awg_qurep_readout()

    def pb_awg_qurep_ramsey_params(self):
        self.pb_awg_qurep_init_params()
        self.pb_awg_qurep_readout_params()  # this overwrites the awg_qurep_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9})

    def pb_awg_qurep_ramsey(self):
        self.pb_awg_qurep_init()

        # DEER pi/2
        self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])
        # DEER free evolution
        self.add_inst_awg([], [], self.params['tau_p'])
        # DEER pi/2
        self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])

        self.pb_awg_qurep_readout()

    def pb_awg_qurep_echo_params(self):
        self.pb_awg_qurep_init_params()
        self.pb_awg_qurep_readout_params()  # this overwrites the awg_qurep_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9})

    def pb_awg_qurep_echo(self):
        self.pb_awg_qurep_init()

        # DEER pi/2
        self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])
        # DEER free evolution and pi
        self.add_inst_awg([], [], self.params['tau_p']/2 - self.params['y180pw']/2)
        self.add_inst_awg([], [], self.params['y180pw'], customflags=['mw2'])
        self.add_inst_awg([], [], self.params['tau_p']/2 - self.params['y180pw']/2)
        # DEER pi/2
        self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])

        self.pb_awg_qurep_readout()

    def pb_awg_qurep2_init_params(self):
        self.pb_awg_qurep_init_params()
        self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0})

    def pb_awg_qurep2_init(self):
        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                   [self.params['deer_y180vi'], self.params['deer_y180vq']]], self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        # Y90
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

        # wait for mw1 to turn off
        self.add_inst_awg([], [], self.params['dt'])

    def pb_awg_qurep2_readout_params(self):
        self.pb_awg_qurep_readout_params()
        self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0})

    def pb_awg_qurep2_readout(self):
        # wait for mw1 to turn on
        self.add_inst_awg([], [], self.params['dt'])

        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                   [self.params['deer_y180vi'], self.params['deer_y180vq']]], self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        # -Y90
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    def pb_awg_qurep2_deer_params(self):
        self.pb_awg_qurep_readout_params()
        self.params.update({'x90pw': 32e-9, 'x90vi': 300.0, 'x90vq': 0.0, 'y90pw': 32e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'y180pw': 72e-9, 'y180vi': 0.0, 'y180vq': 300.0,
                            'deerpw': 0.0, 'deervi': 0.0, 'deervq': 0.0,
                            'reps': 1e7, 'tau': 500e-9, 'inv': 0, 'inv2': 0})

    def pb_awg_qurep2_deer(self):
        # wait for mw1 to turn on
        self.add_inst_awg([], [], self.params['dt'])

        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])

        if np.uint32(self.params['inv2']) == 0:  # do DEER
            self.add_inst_awg('awg2', [self.params['deervi'], self.params['deervq']], self.params['deerpw'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2 - self.params['deerpw'])
        else:
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)

        # -Y90
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    def pb_awg_qurep2_rabi_params(self):
        self.pb_awg_qurep2_init_params()
        self.pb_awg_qurep2_readout_params()  # this overwrites the awg_qurep2_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9, 'deerpulsewidth': 36e-9, 'deer_vi': 0.0, 'deer_vq': 0.0})

    def pb_awg_qurep2_rabi(self):
        self.pb_awg_qurep2_init()

        # pulse on DEER
        self.add_inst_awg('awg2', [self.params['deer_vi'], self.params['deer_vq']], self.params['deerpulsewidth'], customflags=['mw2'])
        # wait for tau_p
        self.add_inst_awg([], [], self.params['tau_p'])

        self.pb_awg_qurep2_readout()

    def pb_awg_qurep2_ramsey_params(self):
        self.pb_awg_qurep2_init_params()
        self.pb_awg_qurep2_readout_params()  # this overwrites the awg_qurep2_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9,
                            'deer_x90pw': 48e-9, 'deer_x90vi': 300.0, 'deer_x90vq': 0.0,
                            'deer_y90pw': 48e-9, 'deer_y90vi': 300.0, 'deer_y90vq': 0.0})

    def pb_awg_qurep2_ramsey(self):
        self.pb_awg_qurep2_init()

        # pulse on DEER
        self.add_inst_awg('awg2', [self.params['deer_x90vi'], self.params['deer_x90vq']], self.params['deer_x90pw'])
        # wait for tau_p
        self.add_inst_awg([], [], self.params['tau_p'])
        self.add_inst_awg('awg2', [self.params['deer_y90vi'], self.params['deer_x90vq']], self.params['deer_y90pw'])

        self.pb_awg_qurep2_readout()

    def pb_awg_qurep2_echo_params(self):
        self.pb_awg_qurep2_init_params()
        self.pb_awg_qurep2_readout_params()  # this overwrites the awg_qurep2_init_params() but makes logical flow
        self.params.update({'tau_p': 1500e-9,
                            'deer_x90pw': 48e-9, 'deer_x90vi': 300.0, 'deer_x90vq': 0.0,
                            'deer_y90pw': 48e-9, 'deer_y90vi': 300.0, 'deer_y90vq': 0.0})

    def pb_awg_qurep2_echo(self):
        self.pb_awg_qurep2_init()

        # pulse on DEER
        self.add_inst_awg('awg2', [self.params['deer_x90vi'], self.params['deer_x90vq']], self.params['deer_x90pw'])
        self.add_inst_awg([], [], self.params['tau_p']/2 - self.params['y180pw']/2)
        self.add_inst_awg('awg2', [self.params['deer_y180vi'], self.params['deer_y180vq']], self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau_p']/2 - self.params['y180pw']/2)
        self.add_inst_awg('awg2', [self.params['deer_y90vi'], self.params['deer_x90vq']], self.params['deer_y90pw'])

        self.pb_awg_qurep2_readout()

    def pb_awg_qurep2_hh_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 48e-9, 'x90vi': 300.0, 'x90vq': 0.0,
                            'y90pw': 48e-9, 'y90vi': 300.0, 'y90vq': 0.0,
                            'pulsewidth': 960e-9, 'vi': 0.0, 'vq': 300.0,
                            'deer_x90vi': 300.0, 'deer_x90vq': 0.0,
                            'deer_y90vi': 300.0, 'deer_y90vq': 0.0,
                            'deerpulsewidth': 96e-9, 'deer_vi': 0.0, 'deer_vq': 300.0,
                            'dt': 52e-9, 'inv': 0})

    def pb_awg_qurep2_hh(self):
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['x90vi'], self.params['x90vq']],
                                             [self.params['deer_x90vi'], self.params['deer_x90vq']]],
                          self.params['x90pw'])

        self.add_inst_awg([], [], self.params['dt'])
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['vi'], self.params['vq']],
                                             [self.params['deer_vi'], self.params['deer_vq']]],
                          self.params['deerpulsewidth'])
        self.add_inst_awg('awg1', [self.params['vi'], self.params['vq']],
                          self.params['dt'])
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['vi'], self.params['vq']],
                                             [self.params['deer_y90vi'], self.params['deer_y90vq']]],
                          self.params['y90pw'])
        self.add_inst_awg('awg1', [self.params['vi'], self.params['vq']],
                          self.params['pulsewidth'] - self.params['deerpulsewidth'] - self.params['dt'] - self.params['y90pw'])

        self.add_inst_awg([], [], self.params['dt'])

        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    def pb_awg_deer_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 32e-9, 'x90vi': 300.0, 'x90vq': 0.0, 'y90pw': 32e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'y180pw': 72e-9, 'y180vi': 0.0, 'y180vq': 300.0, 'deerpulsewidth': 0.0,
                            'reps': 1e7, 'tau': 500e-9, 'inv': 0, 'inv2': 0})

    def pb_awg_deer(self):
        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
        if np.uint32(self.params['inv2']) == 0:  # do DEER
            self.add_inst_awg([], [], self.params['deerpulsewidth'], customflags=['mw2'])
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2 - self.params['deerpulsewidth'])
        else:
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        # Y90
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])

    def pb_awg_2ctrdeer_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 32e-9, 'x90vi': 300.0, 'x90vq': 0.0, 'y90pw': 32e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'y180pw': 72e-9, 'y180vi': 0.0, 'y180vq': 300.0, 'deerpulsewidth': 0.0,
                            'reps': 1e7, 'tau': 500e-9, 'inv': 0})

    def pb_awg_2ctrdeer(self):
        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV, but it's not
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
        self.add_inst_awg([], [], self.params['deerpulsewidth'], customflags=['mw2'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2 - self.params['deerpulsewidth'])
        # Y90
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])

    def pb_awg_deer_cpmg_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'r180pw': 20e-9, 'r180vi': 0.0, 'r180vq': 0.0,
                            'reps': 1e5, 'tau': 0.0, 'n': 1, 'inv': 0, 'inv2': 0})

    def pb_awg_deer_cpmg(self):
        if np.uint32(self.params['inv2']) == 0:  # do DEER
            flags = ['mw2']
        else:
            flags = None

        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['n'])):
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
            self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_newctr_awg_deer_cpmg_params(self):
        self.newctr_ctrticks = [[0, 1], [2, 3], [4, 5], [6,7]]
        self.newctr_sigref = [0, 2]
        self.params = self.default_params()
        self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'r180pw': 20e-9, 'r180vi': 0.0, 'r180vq': 0.0,
                            'reps': 1e5, 'tau': 0.0, 'n': 1, 'inv': 0, 'inv2': 0})

    def pb_newctr_awg_deer_cpmg(self):
        if np.uint32(self.params['inv2']) == 0:  # do DEER
            flags = ['mw2']
        else:
            flags = None

        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['n'])):
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
            self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['r180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_deer_xy4_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 28e-9, 'r90vi': 0.0, 'r90vq': 300.0, 'x180pw': 28e-9, 'x180vi': 300.0, 'x180vq': 0.0,
                            'y180pw': 56e-9, 'y180vi': 0.0, 'y180vq': 300.0, 'reps': 1e5, 'tau': 0.0, 'k': 1,
                            'inv': 0, 'inv2': 0})

    def pb_awg_deer_xy4(self):
        if np.uint32(self.params['inv2']) == 0:  # do DEER
            flags = ['mw2']
        else:
            flags = None

        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_deer_xy8_params(self):
        self.params = self.default_params()
        self.params.update({'r90pw': 28e-9, 'r90vi': 0.0, 'r90vq': 300.0, 'x180pw': 28e-9, 'x180vi': 300.0, 'x180vq': 0.0,
                            'y180pw': 56e-9, 'y180vi': 0.0, 'y180vq': 300.0, 'reps': 1e5, 'tau': 0.0, 'k': 1,
                            'inv': 0, 'inv2': 0})

    def pb_awg_deer_xy8(self):
        if np.uint32(self.params['inv2']) == 0:  # do DEER
            flags = ['mw2']
        else:
            flags = None

        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
        for i in range(np.uint32(self.params['k'])):
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            # Y
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
            # X
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'], customflags=flags)
            self.add_inst_awg([], [], self.params['tau']/2 - self.params['x180pw']/2)
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
        else:
            self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    def pb_awg_echo_params(self):
        self.params = self.default_params()
        self.params.update({'x90pw': 32e-9, 'x90vi': 300.0, 'x90vq': 0.0, 'y90pw': 32e-9, 'y90vi': 0.0, 'y90vq': 300.0,
                            'y180pw': 72e-9, 'y180vi': 0.0, 'y180vq': 300.0, 'reps': 1e7, 'tau': 500e-9, 'inv': 0})

    def pb_awg_echo(self):
        # X90
        self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
        # Y, pi pulse on DEER spin should be same time as on NV
        self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau']/2 - self.params['y180pw']/2)
        # Y90
        if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
            self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
        else:
            self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])

    def pb_awg_twopulse_params(self):
        self.params = self.default_params()
        self.params.update({'r1pw': 20e-9, 'r1vi': 0.0, 'r1vq': 0.0, 'r2pw': 20e-9, 'r2vi': 0.0, 'r2vq': 0.0,
                            'reps': 1e5, 'dt': 100e-9})

    def pb_awg_twopulse(self):
        self.add_inst_awg('awg1', [self.params['r1vi'], self.params['r1vq']], self.params['r1pw'])
        self.add_inst_awg([], [], self.params['dt'])
        self.add_inst_awg('awg1', [self.params['r2vi'], self.params['r2vq']], self.params['r2pw'])

    def pb_cpmg_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth_pi': 56e-9, 'pulsewidth_pi2': 28e-9, 'pulsewidth_pi32': 84e-9, 'tau': 100e-9, 'n': 1.0, 'dt': 0, 'inv': 0})

    def pb_cpmg(self):
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
        for i in range(np.uint32(self.params['n'])):
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi']/2)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi'])
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi']/2
                          + self.params['dt'])
        if np.uint32(self.params['inv']) == 0: # determine whether to apply pi/2 or 3pi/2 pulse
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
        else:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi32'])

    # allow sweeping of the deer pulse, assuming all time durations are mod(10 ns)
    # **tau and pulsewidth_pi and deerpulsewidth has to be mod(20)
    def pb_deer_mamin_params(self):
        self.params = self.default_params()
        self.params.update({'pulsewidth_pi': 200e-9, 'pulsewidth_pi2': 100e-9, 'pulsewidth_pi32': 100e-9, 'deerpulsewidth': 200e-9,
                            'tau': 2e-6, 'dt': 0.0, 'inv': 0})

    def pb_deer_mamin(self):
        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])  # NV pi/2

        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi']/2)
        self.add_inst(['mw2'], self.pb.inst_set.CONTINUE, 0, self.params['deerpulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi']/2 - self.params['deerpulsewidth'])

        self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi'])

        self.add_inst(['mw2'], self.pb.inst_set.CONTINUE, 0, self.params['deerpulsewidth'])
        self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi2']/2 - self.params['deerpulsewidth'])

        if np.uint32(self.params['inv']) == 0:  # determine whether to apply pi/2 or 3pi/2 pulse
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
        else:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_pi32'])

    def pb_4ctr_test_params(self):
        self.params = self.default_params()
        self.params.update({'inv': 0, 'inv2': 0})

    def pb_4ctr_test(self):
        if np.uint32(self.params['inv']) == 0:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, 100e-9)
            if np.uint32(self.params['inv2']) == 0:
                self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, 100e-9)
            else:
                self.add_inst(['mw1', 'mw2'], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, 100e-9)
        else:
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, 100e-9)
            if np.uint32(self.params['inv2']) == 0:
                self.add_inst([''], self.pb.inst_set.CONTINUE, 0, 100e-9)
            else:
                self.add_inst(['mw2'], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst([''], self.pb.inst_set.CONTINUE, 0, 100e-9)
            self.add_inst(['mw1'], self.pb.inst_set.CONTINUE, 0, 100e-9)

    def pb_SiV_exp_params(self):
        self.params = self.repump_params()

    def pb_SiV_exp(self):
        # this is now taken care of in the set_program
        pass
        # self.add_inst(['SiV_repumping'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_repumping'])
        # self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['tau_repump'])
        # self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['repumping_delay'])
        # self.add_inst(['SiV_readout'], self.pb.inst_set.CONTINUE, 0, self.params['readout_delay'])
        # self.add_inst(['SiV_readout', 'ctr0'], self.pb.inst_set.CONTINUE, 0, self.params['pulsewidth_readout'])
        # self.add_inst([''], self.pb.inst_set.CONTINUE, 0, self.params['repumping_delay'] + self.params['readout_delay'])

    def pb_PLE_pulsed_params(self):
        self.params = self.repump_params()
        self.params.update({'numpnts': 100, 'reps': 500, 't1': 1e-5, 't2': 1e-5})
        self.custom_readout = True

    def pb_PLE_pulsed(self):
        pass


        # loop_start = self.add_inst(['ctr2'], self.pb.inst_set.LOOP, np.uint32(self.params['numpnts'])+1, self.params['t1'])
        # self.add_inst([''], self.pb.inst_set.END_LOOP, loop_start, self.params['t2'])
        # self.add_inst([''], self.pb.inst_set.STOP, 0, 1e-6)

    def set_param(self, key, value):
        if key in self.params:
            self.params[key] = value
            # print('PulseMaster set_param')
        else:
            print('Key '+key+' not found!')

    def set_program(self, autostart=True, infinite=False):
        if not self.newctr:
            self.set_program_oldctr(autostart, infinite)
        else:
            self.set_program_newctr(autostart, infinite)

    def set_program_oldctr(self, autostart=True, infinite=False):
        '''
        Sets pulsed ESR to desired sequence (called when you run Rabi experiment

        Returns:

        '''

        # todo: clean this up. put parameters in self when initialized and add an option to load from yaml
        pb = self.pb

        if not infinite:
            reps = self.params['reps']
        else:  # use to create semi-infinite loop. e.g. for picoharp use.
            reps = 1e8

        n_inner_loops = 100
        n_loops = math.floor(reps/n_inner_loops)

        awglist = ['scope']  #  Trigger the scope where the AWG is supposed to start
        if self.awg_enable:
            for awg in self.awg:
                awglist.append(awg.alias)

        pb.pb_start_programming(self.pb.PULSE_PROGRAM)

        if not self.params_repump_enable:  # not PLE repumping scheme. todo: make it more generic
            if self.params_readoutcal_enable:
                for key in self.readout_params.keys():
                    self.readout_params[key] = self.params[key]

            aom_delay = self.readout_params['aom_delay']
            awg_offset = self.readout_params['awg_offset']
            mw_delay = self.readout_params['mw_delay']
            time_dark = self.readout_params['time_dark']
            time_green = self.readout_params['time_green']
            time_det = self.readout_params['time_det']
            time_sep = self.readout_params['time_sep']

            if self.custom_readout:  # pulse_names with custom readout sequence,
                self.pulse_func()  # all the looping and counter gating need to be defined in pulse_func() "eg: pb_rabi()"
            else:
                if 'inv' not in self.params.keys() or not self.isINV:  # conventional ESR data acquisition
                    if self.params_readoutcal_enable: # use longer readout pulse with more flexible timing
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                        outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func()
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops-1, aom_delay)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_sep)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - 2*time_det - time_sep)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func()
                        self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_sep)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.END_LOOP, outer_loop, time_green - aom_delay - 2 * time_det - time_sep)
                        self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
                    else:  # use manually trimmed readout pulse to speed up some short sequences, e.g. Rabi
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark - (2*time_det + time_sep - (time_green - aom_delay)))
                        outer_loop = self.add_inst([], pb.inst_set.LOOP, n_loops, (2*time_det + time_sep - (time_green - aom_delay)))
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func()
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay)
                        inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops-1, aom_delay)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                        self.add_inst(['ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)))
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func()
                        self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                        self.add_inst(['ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst([], pb.inst_set.END_LOOP, outer_loop, time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)))
                        self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
                else:  # take interleaved data with alternating INV phase using ctr0 and ctr1
                    # here sync the counters with the green (the old standard set of experiments)
                    # Conveniently, this sequence doesn't need to be trimmed as there is no ref gate
                    if 'inv2' not in self.params.keys() or not self.isINV2:
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                        outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func_inv(0)  # program awg with INV=0
                        # INV=0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv(1)  # program awg with INV=1
                        # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func_inv(0)  # program awg with INV=0
                        # INV=0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv(1)  # program awg with INV=1
                        # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                        self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
                    else:
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                        outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func_inv2(0, 0)  # program awg with INV=0
                        # INV=0,0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(1, 0)  # program awg with INV=1
                        # INV=1,0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(0, 1)  # program awg with INV=1
                        # INV=1,0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr2'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(1, 1)  # program awg with INV=1
                        # INV=1,0 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr3'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                        self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                        if self.awg_enable:
                            self.clear_inst_awg()
                        self.pulse_func_inv2(0, 0)  # program awg with INV=0
                        # INV=0,0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(1, 0)  # program awg with INV=1
                        # INV=1,0 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr1'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(0, 1)  # program awg with INV=1
                        # INV=0,1 readout - extend awg waveform if awg_enable
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                        self.add_inst(['green', 'ctr2'], pb.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                        self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                        self.pulse_func_inv2(1, 1)  # program awg with INV=1
                        # INV=1,1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                        self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                        self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                        self.add_inst(['green', 'ctr3'], pb.inst_set.CONTINUE, 0, time_det)
                        self.add_inst(['green'], pb.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                        self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)

            if self.awg_enable:
                self.set_awg(delay=time_dark+awg_offset)

        else:  # repumping sequence
            pulsewidth_repumping = self.params['pulsewidth_repumping']
            pulsewidth_readout = self.params['pulsewidth_readout']
            repumping_delay = self.params['repumping_delay']
            readout_delay = self.params['readout_delay']
            tau_repump = self.params['tau_repump']

            # todo: add options for fast ple scan
            outer_loop = self.add_inst(['SiV_repumping'], pb.inst_set.LOOP, n_loops, pulsewidth_repumping)
            # self.pulse_func()
            self.add_inst([], pb.inst_set.CONTINUE, 0, repumping_delay + tau_repump)
            inner_loop = self.add_inst(['SiV_readout'], pb.inst_set.LOOP, n_inner_loops - 1, readout_delay)
            self.add_inst(['SiV_readout', 'ctr0'], pb.inst_set.CONTINUE, 0, pulsewidth_readout)
            self.add_inst([], pb.inst_set.CONTINUE, 0, readout_delay + repumping_delay)
            self.add_inst(['SiV_repumping'], pb.inst_set.CONTINUE, 0, pulsewidth_repumping)
            # self.pulse_func()
            self.add_inst([], pb.inst_set.END_LOOP, inner_loop, repumping_delay + tau_repump)
            self.add_inst(['SiV_readout'], pb.inst_set.CONTINUE, 0, readout_delay)
            self.add_inst(['SiV_readout', 'ctr0'], pb.inst_set.CONTINUE, 0, pulsewidth_readout)
            self.add_inst([], pb.inst_set.END_LOOP, outer_loop, readout_delay + repumping_delay)
            self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)

        pb.pb_stop_programming()
        if autostart:
            pb.pb_start()

    def set_program_newctr(self, autostart=True, infinite=False):
        pb = self.pb

        if not infinite:
            reps = self.params['reps']
        else:  # use to create semi-infinite loop. e.g. for picoharp use.
            reps = 1e8

        n_inner_loops = 100
        n_loops = math.floor(reps / n_inner_loops)

        awglist = ['scope']  # Trigger the scope where the AWG is supposed to start
        if self.awg_enable:
            for awg in self.awg:
                awglist.append(awg.alias)

        pb.pb_start_programming(self.pb.PULSE_PROGRAM)

        if self.params_readoutcal_enable:
            for key in self.readout_params.keys():
                self.readout_params[key] = self.params[key]

        aom_delay = self.readout_params['aom_delay']
        awg_offset = self.readout_params['awg_offset']
        mw_delay = self.readout_params['mw_delay']
        time_dark = self.readout_params['time_dark']
        time_green = self.readout_params['time_green']
        time_det = self.readout_params['time_det']
        time_sep = self.readout_params['time_sep']
        time_trig = 20e-9  # todo: make it adjustable via gui

        if self.custom_readout:  # pulse_names with custom readout sequence,
            self.pulse_func()  # all the looping and counter gating need to be defined in pulse_func() "eg: pb_rabi()"
        else:
            if 'inv' not in self.params.keys() or not self.isINV:  # conventional ESR data acquisition
                if self.params_readoutcal_enable:  # use longer readout pulse with more flexible timing
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func()
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_sep - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0,
                                  time_green - aom_delay - 2 * time_det - time_sep - time_trig)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func()
                    self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_sep - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.END_LOOP, outer_loop,
                                  time_green - aom_delay - 2 * time_det - time_sep - time_trig)
                    self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
                else:  # use manually trimmed readout pulse to speed up some short sequences, e.g. Rabi
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0,
                                  time_dark - (2 * time_det + time_sep - (time_green - aom_delay)))
                    outer_loop = self.add_inst([], pb.inst_set.LOOP, n_loops,
                                               (2 * time_det + time_sep - (time_green - aom_delay)))
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func()
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay)
                    inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst([], pb.inst_set.CONTINUE, 0,
                                  time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func()
                    self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst([], pb.inst_set.END_LOOP, outer_loop,
                                  time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
                    self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
            else:  # take interleaved data with alternating INV phase using ctr0 and ctr1
                # here sync the counters with the green (the old standard set of experiments)
                # Conveniently, this sequence doesn't need to be trimmed as there is no ref gate
                # TODO: fix this for inv and inv2
                # TODO: THIS DOESN'T WORK YET
                if 'inv2' not in self.params.keys() or not self.isINV2:
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig,
                                  awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                    self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)
                else:
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, pb.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], pb.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,0 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(awglist, pb.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=0,1 readout - extend awg waveform if awg_enable
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], pb.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], pb.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], pb.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], pb.inst_set.STOP, 0, 1e-6)

            if self.awg_enable:
                self.set_awg(delay=time_dark + awg_offset)

        pb.pb_stop_programming()
        if autostart:
            pb.pb_start()

    def set_awg(self, delay=0.0):
        for num in range(len(self.awg)):
            awg_wfm = getattr(self, 'awg_wfm%d' % num)
            awg_amplitude = 350.0  # mV

            wfm1_norm = self.awg_norm_pulse(awg_wfm[0], awg_amplitude, delay)
            wfm2_norm = self.awg_norm_pulse(awg_wfm[1], awg_amplitude, delay)

            self.awg[num].set_output(0)

            ch1_min = min(wfm1_norm) * awg_amplitude / 1000.0
            ch1_max = max(wfm1_norm) * awg_amplitude / 1000.0
            ch2_min = min(wfm2_norm) * awg_amplitude / 1000.0
            ch2_max = max(wfm2_norm) * awg_amplitude / 1000.0

            if not (ch1_min == 0 and ch1_max == 0):
                self.awg[num].set_wfm(1, wfm1_norm, sampl=self.awg_srate)
                self.awg[num].set_amplitude_wfm(1, ch1_min, ch1_max)
                self.awg[num].set_triggered(1, 1)
            else:  # just set DC
                self.awg[num].set_triggered(1, 0)  # cannot burst DC
                self.awg[num].set_func(1, 'DC')
                self.awg[num].set_dc(1, 0.0)
            error = self.awg[num].get_error()
            if error:
                print('AWG%d, ch%d error:' % (num + 1, 1))
                print(error)

            if not (ch2_min == 0 and ch2_max == 0):
                self.awg[num].set_wfm(2, wfm2_norm, sampl=self.awg_srate)
                self.awg[num].set_amplitude_wfm(2, ch2_min, ch2_max)
                self.awg[num].set_triggered(2, 1)
            else:  # just set DC
                self.awg[num].set_triggered(2, 0)  # cannot burst DC
                self.awg[num].set_func(2, 'DC')
                self.awg[num].set_dc(2, 0.0)

            if not (ch1_min == 0 and ch1_max == 0) or not (ch2_min == 0 and ch2_max == 0):
                self.awg[num].set_view('DUAL')

            error = self.awg[num].get_error()
            if error:
                print('AWG%d, ch%d error:' % (num + 1, 2))
                print(error)

            self.awg[num].set_output(1)

    def awg_norm_pulse(self, wfm, awg_amplitude, delay=0.0):

        pts_delay = int(round(delay*1e9))

        wfm = np.append(np.array([0.0]*(32+pts_delay)), wfm)  # guarantees the waveform starts at zero with at least 32 points
        wfm = np.append(wfm, np.array([0.0]*32*4))  # guarantees the waveform ends at zero with at least 32 points

        awg_preedge = self.readout_params['awg_preedge']
        awg_postedge = self.readout_params['awg_postedge']

        wfm = self.expand_awg_pulse(wfm, awg_preedge, awg_postedge)

        wfm_norm = wfm / awg_amplitude
        return wfm_norm

    def expand_awg_pulse(self, wfm, t_pre, t_post):
        # take a numpy array with 1 GS/s sampling rate, extend each pulse tails by 100 ns (10 samples)
        # raise error if there is any overlap
        # downsample to the correct srate at the end

        srate = 1e9
        pts_pre = round(t_pre * srate)
        pts_extend = round((t_pre + t_post) * srate)

        i = 0

        while i < len(wfm):
            if wfm[i] != 0 and wfm[i + 1] == 0:
                # falling edge. do something
                if not wfm[i + 1:i + pts_extend + 1].any():
                    wfm[i + 1:i + pts_extend + 1] = wfm[i]
                    i = i + pts_extend + 1
                else:
                    j = 0
                    while j < pts_extend and wfm[i + j + 1] == 0:
                        j += 1
                    if wfm[i + j + 1] == wfm[i]:
                        # this is okay. the IQ value are still the same
                        wfm[i + 1:i + j + 1] = wfm[i]
                        i = i + j + 1
                    else:
                        print('blank time not long enough between changes')
                        # error and skip out
                        i = len(wfm)
            else:
                i += 1

        # print(len(wfm))
        if not wfm[0:pts_pre].any():
            wfm = wfm[pts_pre:]
        else:
            print('waveform does not have enough zeros at the beginning')
        # print(len(wfm))

        # now downsample the waveform to the awg_srate
        downsamp_ratio = round(1e9/self.awg_srate)
        wfm = wfm[::downsamp_ratio]
        wfm = np.append(wfm, np.array([0.0]*32))

        return wfm

    def test(self):
        pb = self.pb

        pb.pb_start_programming(self.pb.PULSE_PROGRAM)
        self.add_inst(['green', 'mw1'], pb.inst_set.CONTINUE, 0, 1)
        self.add_inst(['green'], pb.inst_set.BRANCH, 0, 1)
        pb.pb_stop_programming()

        # self.set_awg()
        pb.pb_start()

    def set_cw(self):
        pb = self.pb
        pb.pb_start_programming(self.pb.PULSE_PROGRAM)
        self.add_inst(self.tracker_laser, pb.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(self.tracker_laser, pb.inst_set.BRANCH, 0, 1e-6)
        pb.pb_stop_programming()
        pb.pb_start()

    def set_cw_custom(self, flags):
        pb = self.pb
        pb.pb_start_programming(self.pb.PULSE_PROGRAM)
        self.add_inst(flags, pb.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(flags, pb.inst_set.BRANCH, 0, 1e-6)
        pb.pb_stop_programming()
        pb.pb_start()

    def set_cw_mw(self):
        pb = self.pb
        pb.pb_start_programming(self.pb.PULSE_PROGRAM)
        self.add_inst(['green', 'mw1'], pb.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(['green', 'mw1'], pb.inst_set.BRANCH, 0, 1e-6)
        pb.pb_stop_programming()
        pb.pb_start()

    def set_static(self, pbflags_dec):
        pb = self.pb
        pb.pb_start_programming(self.pb.PULSE_PROGRAM)
        self.pb.pb_inst_pbonly64(pbflags_dec, pb.inst_set.CONTINUE, 0, 1000)
        self.pb.pb_inst_pbonly64(pbflags_dec, pb.inst_set.BRANCH, 0, 1000)
        pb.pb_stop_programming()
        pb.pb_start()

    def add_inst(self, flag_list, op_code, inst_data, inst_length, awgblank=False):
        if not awgblank:
            flag_num = self.get_flag_num(flag_list)

            if inst_length == 0:
                return 0  # todo: return address of previous inst instead of 0?
            else:
                if inst_length*1e9 < 10:
                    print('Pulse Duration too short!')
                    raise ValueError('PulseBlaster instruction shorter than 10 ns')
                return self.pb.pb_inst_pbonly64(flag_num, op_code, int(inst_data), inst_length*1e9)
        else:
            # this low-level call is convoluted but should make high-level calls easy
            # call add_inst_awg with specific pb parameters
            # add_inst_awg calls back to this add_inst with awgblank=False
            return self.add_inst_awg([], [], inst_length, customflags=flag_list, op_code=op_code, inst_data=inst_data)

    def add_inst_awg(self, awglist, awgval, inst_length, customflags=None, op_code=None, inst_data=None, awgonly=False):
        '''
        awglist: a list containing the AWG names
        awgval: a list containing two-vector of AWG values
        '''
        if not isinstance(awglist, list) and len(awgval) == 2:
            awglist = [awglist]
            awgval = [awgval]

        # build a waveform array with 1ns resolution
        awg_srate = 1e9
        awg_pts = int(round(inst_length * awg_srate))

        # todo: work out this warning
        if awg_pts % 4:
            print('warning: awg inst_length %d is not a multiple of 4 ns' % awg_pts)

        if awg_pts == 0:
            return 0
        else:
            if customflags is None:
                flag_list = []
            else:
                flag_list = customflags

            for awgnum in range(len(self.awg)):
                # check from the instrument list if each instrument has an instruction
                awg_wfm = getattr(self, 'awg_wfm%d' % awgnum)
                awgname = self.awg[awgnum].alias
                if awgname in awglist:
                    index = awglist.index(awgname)
                    if (awgval[index][0] != 0) or (awgval[index][1] != 0):
                        # replace awg name with mw name
                        mwname = self.awg[awgnum].alias.replace('awg', 'mw')
                        if mwname not in flag_list:
                            flag_list.append(mwname)
                    awg_wfm[0] = np.append(awg_wfm[0], np.array([awgval[index][0]] * awg_pts))
                    awg_wfm[1] = np.append(awg_wfm[1], np.array([awgval[index][1]] * awg_pts))
                else:
                    awg_wfm[0] = np.append(awg_wfm[0], np.array([0] * awg_pts))
                    awg_wfm[1] = np.append(awg_wfm[1], np.array([0] * awg_pts))

            if not awgonly:
                if op_code is None or inst_data is None:
                    return self.add_inst(flag_list, self.pb.inst_set.CONTINUE, 0, inst_length)
                else:
                    return self.add_inst(flag_list, op_code, inst_data, inst_length)

    def clear_inst_awg(self):
        for awgnum in range(len(self.awg)):
            setattr(self, 'awg_wfm%d' % awgnum, [np.array([]), np.array([])])

    def get_flag_num(self, flag_list, add=False):
        if not self.pb_dict:
            flag_num = 0
            if 'green' in flag_list or 'SiV_readout' in flag_list:
                flag_num += 0
            elif not add:
                flag_num += pow(2, 0)
            if 'scope' in flag_list or 'orange' in flag_list:
                flag_num += pow(2, 1)
            if 'ctr0' in flag_list:
                flag_num += pow(2, 2)
            if 'ctr1' in flag_list:
                flag_num += pow(2, 3)
            if 'mw1' in flag_list or 'SiV_repumping' in flag_list:
                flag_num += pow(2, 4)
                flag_num += pow(2, 8)  # use for scope viewing
            if 'mw2' in flag_list:
                flag_num += pow(2, 5)
                flag_num += pow(2, 9)  # use for scope viewing
            if 'awg1' in flag_list:
                flag_num += pow(2, 6)
            if 'awg2' in flag_list:
                flag_num += pow(2, 7)
            if 'ctr2' in flag_list:
                flag_num += pow(2, 10)
            if 'ctr3' in flag_list:
                flag_num += pow(2, 11)
        else:
            _pbnum = self.pb_dict['pbnum']
            _key = self.pb_dict['key']
            _inv = self.pb_dict['inv']

            if flag_list:
                unknown_flags = [flag for flag in flag_list if flag and flag not in _key]
                if unknown_flags:
                    print('Unknown flags: check pb_dict.csv')
                    print(unknown_flags)

            # This is written in a very dumb way. If anyone reads this, please try to clean it up. -Peace 09/19/17
            # create an array of zeros up to the max digit
            reversed_bin = [0] * (np.max(_pbnum) + 1)
            # for any bit defined in the dict, set that bit
            for i, num in enumerate(_pbnum):
                # bit value = (key in flaglist) XOR inv
                reversed_bin[num] = int(bool(_key[i] in flag_list) != bool(_inv[i]))

            pb_bin = reversed_bin[::-1]  # reverse the bits
            pb_bin = map(str, pb_bin)  # convert to string
            pb_bin = ''.join(pb_bin)

            flag_num = int(pb_bin, 2)
        return flag_num

    def wait_until_finished(self):
        while self.pb.pb_read_status() == 4:  # while PulseBlaster is running
            time.sleep(0.1)

    def wait_until_finished_thd(self, thread_esr):
        while self.pb.pb_read_status() == 4 and not thread_esr.cancel:  # while PulseBlaster is running
            time.sleep(0.1)
        if thread_esr.cancel:
            return 1
        else:
            return 0

    def stop(self):
        self.pb.pb_stop()

    def list_functions(self):
        return sorted([f[3:] for f in dir(self)
                       if (callable(getattr(self, f)) and
                           ('pb_' in f) and
                           (f+'_params' in dir(self)))])


if __name__ == '__main__':
    print('PulseMaster Test')
    pm = PulseMaster()
    pm.set_pulse('rabi')
    # pm.simple_test()
    pm.set_param('pulsewidth', 50e-9)
    pm.set_program()

    print(pm.params)

