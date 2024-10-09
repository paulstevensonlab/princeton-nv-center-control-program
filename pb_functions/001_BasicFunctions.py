def pb_odmr_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 100e-6, 'tau': 100e-6})
    self.custom_readout = True

# modified by ZY 09/22/2021
def pb_odmr(self):
    loop_start = self.add_inst(['green'], self.inst_set.LOOP, self.params['reps'], 1e-6)
    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['tau']-self.params['pulsewidth'])
    self.add_inst(['green', 'mw1', 'ctr0'], self.inst_set.END_LOOP, loop_start, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)

def pb_odmr_switched_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 100e-6, 'tau': 100e-6})
    self.custom_readout = True

def pb_odmr_switched(self):
    loop_start = self.add_inst(['green'], self.inst_set.LOOP, self.params['reps'], 1e-6)
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['tau'] - self.params['pulsewidth'])
    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, 1e-6)
    self.add_inst(['green', 'mw1', 'ctr0'], self.inst_set.END_LOOP, loop_start, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)


def pb_odmr2_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 100e-6, 'tau': 100e-6})
    self.custom_readout = True


def pb_odmr2(self):
    loop_start = self.add_inst(['green'], self.inst_set.LOOP, self.params['reps'], 1e-6)
    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['tau']-self.params['pulsewidth'])
    self.add_inst(['green', 'mw2', 'ctr0'], self.inst_set.END_LOOP, loop_start, self.params['pulsewidth'])
    self.add_inst(['green'], self.inst_set.STOP, 0, 1e-6)

def pb_odmr_pulsed_2tone_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth1': 50e-6, 'pulsewidth2': 1e-6,
                        'tau': 10e-6, 'tau2': 10e-6})

def pb_odmr_pulsed_2tone(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth1'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])
    self.add_inst(['mw2'], self.inst_set.CONTINUE, 0, self.params['pulsewidth2'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau2'])


def pb_rabi_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})


def pb_rabi(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])


def pb_rabi2_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})


def pb_rabi2(self):
    self.add_inst(['mw2'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])

def pb_rabi_custom_params(self):
    self.params = self.default_params()
    self.params.update({'time_green': 3800e-9, 't_dark': 2000e-9, 'pulsewidth': 100e-6, 'mw_delay': 0, 'aom_delay': 800e-9,
                        'time_det': 300e-9, 'time_sep': 3000e-9, 'reps': 100000})
    self.custom_readout = True


def pb_rabi_custom(self):
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['time_green'])
    loop_start = self.add_inst([''], self.inst_set.LOOP, self.params['reps'], self.params['t_dark'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['mw_delay'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['aom_delay'])
    self.add_inst(['green', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['time_det'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['time_sep'])
    self.add_inst(['green', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['time_det'])
    self.add_inst(['green'], self.inst_set.END_LOOP, loop_start, self.params['time_green'] - self.params['aom_delay']
                  - 2 * self.params['time_det'] - self.params['time_sep'])
    self.add_inst([''], self.inst_set.STOP, 0, 1e-6)