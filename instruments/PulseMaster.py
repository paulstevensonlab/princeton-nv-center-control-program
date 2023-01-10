import instruments as instr
import numpy as np
import math as math
import time
import os
import warnings


# Default function for self.pulse_func to hook on to
def pb_default(pm):
    print('no function is defined')


def default_pulse_list():
    return ['', 'CW', 'CW2', 'PLE_CW', 'PLE_CW_WM']


def default_seq_time():
    return [[0, 0]]  # [time, n_loops] For storing sequence time and loop information


class PulseMaster(instr.PulseBlaster.PBESRPro):

    def __init__(self, awg=[], pb_dict={}):
        super().__init__()
        self.pb_init()
        self.pb_core_clock(500 * self.constants['MHz'])

        # dictionary for storing pbnum, key, inversion
        self.pb_dict = pb_dict
        self.tracker_laser = ['green']

        self.pulse_list = default_pulse_list()
        self.update_pulse_list()
        self.pulse_func = pb_default
        self.pulse_name = 'default'

        # Store the references to AWGs so that they can be programmed
        self.awg = awg
        for awgnum in range(len(self.awg)):
            setattr(self, 'awg_wfm%d' % awgnum, [np.array([]), np.array([])])
        self.awg_enable = False
        self.awg_srate = 250e6
        self.custom_readout = False
        self.params_readoutcal_enable = False  # enable the readout pulse parameters. e.g. aom_delay

        self.readout_params = {'aom_delay': 700e-9,
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

        self.inst_num = 0  # Keep track of instruction number
        self.seq_time = default_seq_time()

        self.params = self.default_params()
        self.isINV = False
        self.isINV2 = False
        self.newctr = False
        self.newctr_ctrticks = [[0, 1], [2, 3]]  # ticks to subtract for each counter
        self.newctr_sigref = [0, 1]  # index of the counters to divide as sig/ref => PL

    def set_pb_dict(self, d):
        self.pb_dict = d

    # Get all the pulse list from the different python files
    # todo: add option to disable some files and migrate file locations to exp_config
    def update_pulse_list(self, log=False):
        self.pulse_list = default_pulse_list()
        # Assume the mainexp is running in the root directory
        pb_func_dir = os.path.join(os.getcwd(), 'pb_functions')

        pulse_files = sorted([f for f in os.listdir(pb_func_dir)
                              if os.path.isfile(os.path.join(pb_func_dir, f)) and f.endswith('.py')])

        # Executing Files except for import_pb_functions, which will be appended at the end
        try:
            pulse_files.remove('import_pb_functions.py')
            import_pb_functions = open(os.path.join(pb_func_dir, 'import_pb_functions.py')).read()
            for f in pulse_files:
                try:
                    # Execute the pulse definitions with only 'self' defined in locals
                    # The locals() will then have only the methods defined inside this call, not all the previous ones.
                    exec(open(os.path.join(pb_func_dir, f)).read() + import_pb_functions, globals(), {'self': self})
                    if log:
                        print('Loaded PulseBlaster Functions: ' + f)
                except Exception:
                    warnings.warn('File Error: ' + f)
        except ValueError:
            warnings.warn('import_pb_functions.py is not defined!')

    def default_params(self):
        self.custom_readout = False

        params = {'reps': 1e5}
        if self.params_readoutcal_enable:
            params.update(self.readout_params)
        return params

    def set_pulse(self, pulse_name):
        try:
            self.pulse_func = getattr(self, ('pb_'+pulse_name))
            getattr(self, ('pb_'+pulse_name)+'_params')(self)
            self.pulse_name = pulse_name
            self.awg_enable = 'awg' in pulse_name
        except AttributeError:
            print(pulse_name+" is not configured.")

    def pulse_func_inv(self, inv):
        self.params['inv'] = inv
        self.pulse_func(self)

    def pulse_func_inv2(self, inv, inv2):
        # just assume we'd do inv if inv2 is selected
        self.params['inv'] = inv
        self.params['inv2'] = inv2
        self.pulse_func(self)

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
                awglist.append(awg.alias)

        self.start_programming()

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
            self.pulse_func(self)  # all the looping and counter gating need to be defined in pulse_func() "eg: pb_rabi()"
        else:
            if 'inv' not in self.params.keys() or not self.isINV:  # conventional ESR data acquisition
                if self.params_readoutcal_enable: # use longer readout pulse with more flexible timing
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops-1, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_sep)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - 2*time_det - time_sep)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_sep)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.END_LOOP, outer_loop, time_green - aom_delay - 2 * time_det - time_sep)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
                else:  # use manually trimmed readout pulse to speed up some short sequences, e.g. Rabi
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark - (2*time_det + time_sep - (time_green - aom_delay)))
                    outer_loop = self.add_inst([], self.inst_set.LOOP, n_loops, (2*time_det + time_sep - (time_green - aom_delay)))
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops-1, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)))
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst([], self.inst_set.END_LOOP, outer_loop, time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)))
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
            else:  # take interleaved data with alternating INV phase using ctr0 and ctr1
                # here sync the counters with the green (the old standard set of experiments)
                # Conveniently, this sequence doesn't need to be trimmed as there is no ref gate
                if 'inv2' not in self.params.keys() or not self.isINV2:
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
                else:
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr2'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,0 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr3'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=0,1 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr2'], self.inst_set.CONTINUE, 0, time_det, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr3'], self.inst_set.CONTINUE, 0, time_det)
                    self.add_inst(['green'], self.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)

        if self.awg_enable:
            self.set_awg(delay=time_dark+awg_offset)

        # Make sure PB stops correctly in the case where user does not end with BRANCH or STOP. Useful for PLE Pulsed
        self.add_inst([], self.inst_set.STOP, 0, 1e-6)

        self.stop_programming()
        if autostart:
            self.start()

    def set_program_newctr(self, autostart=True, infinite=False):
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

        self.start_programming()

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
            self.start_programming()
            self.pulse_func(self)  # all the looping and counter gating need to be defined in pulse_func()
            self.stop_programming()
        else:
            if 'inv' not in self.params.keys() or not self.isINV:  # conventional ESR data acquisition
                if self.params_readoutcal_enable:  # use longer readout pulse with more flexible timing
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_sep - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0,
                                  time_green - aom_delay - 2 * time_det - time_sep - time_trig)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_sep - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.END_LOOP, outer_loop,
                                  time_green - aom_delay - 2 * time_det - time_sep - time_trig)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
                else:  # use manually trimmed readout pulse to speed up some short sequences, e.g. Rabi
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0,
                                  time_dark - (2 * time_det + time_sep - (time_green - aom_delay)))
                    outer_loop = self.add_inst([], self.inst_set.LOOP, n_loops,
                                               (2 * time_det + time_sep - (time_green - aom_delay)))
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst([], self.inst_set.CONTINUE, 0,
                                  time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func(self)
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_sep - (time_green - aom_delay - time_det))
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst([], self.inst_set.END_LOOP, outer_loop,
                                  time_dark - (time_det + time_sep - (time_green - aom_delay - time_det)) - time_trig)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
            else:  # take interleaved data with alternating INV phase using ctr0 and ctr1
                # here sync the counters with the green (the old standard set of experiments)
                # Conveniently, this sequence doesn't need to be trimmed as there is no ref gate
                # FIXME: fix this for inv and inv2
                #  THIS DOESN'T WORK YET
                if 'inv2' not in self.params.keys() or not self.isINV2:
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv(0)  # program awg with INV=0
                    # INV=0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv(1)  # program awg with INV=1
                    # INV=1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig,
                                  awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.END_LOOP, outer_loop, time_green - aom_delay - time_det)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)
                else:
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
                    outer_loop = self.add_inst(awglist, self.inst_set.LOOP, n_loops, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    inner_loop = self.add_inst(['green'], self.inst_set.LOOP, n_inner_loops - 1, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,0 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(awglist, self.inst_set.CONTINUE, 0, time_dark)
                    if self.awg_enable:
                        self.clear_inst_awg()
                    self.pulse_func_inv2(0, 0)  # program awg with INV=0
                    # INV=0,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.END_LOOP, inner_loop, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 0)  # program awg with INV=1
                    # INV=1,0 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(0, 1)  # program awg with INV=1
                    # INV=0,1 readout - extend awg waveform if awg_enable
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst([], self.inst_set.CONTINUE, 0, time_dark, awgblank=self.awg_enable)
                    self.pulse_func_inv2(1, 1)  # program awg with INV=1
                    # INV=1,1 readout - no need to extend awg waveform here, just blank to make sure awg ends with zero
                    self.add_inst([], self.inst_set.CONTINUE, 0, mw_delay, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, aom_delay)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green - aom_delay - time_det - time_trig, awgblank=self.awg_enable)
                    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)

            if self.awg_enable:
                self.set_awg(delay=time_dark + awg_offset)

        self.stop_programming()
        if autostart:
            self.start()

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
        self.start_programming()
        self.add_inst(['green', 'mw1'], self.inst_set.CONTINUE, 0, 1)
        self.add_inst(['green'], self.inst_set.BRANCH, 0, 1)
        self.stop_programming()

        # self.set_awg()
        self.start()

    def set_cw(self):
        self.start_programming()
        self.add_inst(self.tracker_laser, self.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(self.tracker_laser, self.inst_set.BRANCH, 0, 1e-6)
        self.stop_programming()
        self.start()

    def set_cw_custom(self, flags):
        self.start_programming()
        self.add_inst(flags, self.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(flags, self.inst_set.BRANCH, 0, 1e-6)
        self.stop_programming()
        self.start()

    def set_cw_mw(self):
        self.start_programming()
        self.add_inst(['green', 'mw1'], self.inst_set.CONTINUE, 0, 1e-6)
        self.add_inst(['green', 'mw1'], self.inst_set.BRANCH, 0, 1e-6)
        self.stop_programming()
        self.start()

    def set_static(self, pbflags_dec):
        self.start_programming()
        self.pb_inst_pbonly64(pbflags_dec, self.inst_set.CONTINUE, 0, 1000)
        self.pb_inst_pbonly64(pbflags_dec, self.inst_set.BRANCH, 0, 1000)
        self.stop_programming()
        self.start()

    def add_inst(self, flag_list, op_code, inst_data, inst_length, awgblank=False):
        if not awgblank:
            flag_num = self.get_flag_num(flag_list)

            if inst_length != 0:
                if inst_length*1e9 < 10:
                    print('Pulse Duration too short!')
                    print(inst_length*1e9,flag_list)
                    raise ValueError('PulseBlaster instruction shorter than 10 ns')
                self.inst_num = self.pb_inst_pbonly64(flag_num, op_code, int(inst_data), inst_length * 1e9)

                if op_code == self.inst_set.CONTINUE:
                    self.seq_time[-1][0] += inst_length
                elif op_code == self.inst_set.LOOP:
                    self.seq_time.append([inst_length, int(inst_data)])
                elif op_code == self.inst_set.END_LOOP:
                    loop_time = self.seq_time.pop()
                    loop_time[0] += inst_length
                    self.seq_time[-1][0] += loop_time[0] * loop_time[1]
                # This assumes BRANCH goes back to the first instruction, which is true almost all the time.
                elif op_code == self.inst_set.BRANCH:
                    self.seq_time[-1][0] += inst_length
                    self.seq_time[-1][1] = op_code  # to indicate it is running infinitely
                elif op_code == self.inst_set.STOP:
                    self.seq_time[-1][0] += inst_length
                    self.seq_time[-1][1] = op_code
                else:
                    raise RuntimeError('Unsupported command: JSR, RTS, LONG_DELAY, WAIT, RTI not implemented')
            return self.inst_num
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

        inst_length = round(inst_length / 4e-9) * 4e-9
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
                    return self.add_inst(flag_list, self.inst_set.CONTINUE, 0, inst_length)
                else:
                    return self.add_inst(flag_list, op_code, inst_data, inst_length)

    def clear_inst_awg(self):
        for awgnum in range(len(self.awg)):
            setattr(self, 'awg_wfm%d' % awgnum, [np.array([]), np.array([])])

    def get_flag_num(self, flag_list, add=False):
        if not self.pb_dict:
            flag_num = 0
            if 'green' in flag_list:
                flag_num += 0
            elif not add:
                flag_num += pow(2, 0)
            if 'scope' in flag_list or 'orange' in flag_list:
                flag_num += pow(2, 1)
            if 'ctr0' in flag_list:
                flag_num += pow(2, 2)
            if 'ctr1' in flag_list:
                flag_num += pow(2, 3)
            if 'mw1' in flag_list:
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
        while self.pb_read_status() == 4:  # while PulseBlaster is running
            time.sleep(0.1)

    def wait_until_finished_thd(self, thread_esr):
        while self.pb_read_status() == 4 and not thread_esr.cancel:  # while PulseBlaster is running
            time.sleep(0.1)
        if thread_esr.cancel:
            return 1
        else:
            return 0

    def start_programming(self):
        self.pb_start_programming(self.PULSE_PROGRAM)
        self.seq_time = default_seq_time()
        self.inst_num = 0

    def stop_programming(self):
        self.pb_stop_programming()
        if len(self.seq_time) > 1:
            with warnings.catch_warnings():
                warnings.simplefilter('always')
                warnings.warn('There is a LOOP that does not have END_LOOP!')

    def start(self):
        self.pb_start()

    def stop(self):
        self.pb_stop()

    def list_functions(self):
        return self.pulse_list


if __name__ == '__main__':
    print('PulseMaster Test')
    pm = PulseMaster()
    pm.set_pulse('rabi')
    # pm.simple_test()
    pm.set_param('pulsewidth', 50e-9)
    pm.set_program()

    print(pm.params)

