def pb_awg_rabi_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'vi': 0.0, 'vq': 0.0, 'reps': 1e5, 'tau': 0.0})


def pb_awg_rabi(self):
    self.add_inst_awg('awg1', [self.params['vi'], self.params['vq']], self.params['pulsewidth'])
    self.add_inst_awg([], [], self.params['tau'])


def pb_awg_twopulse_params(self):
    self.params = self.default_params()
    self.params.update({'r1pw': 20e-9, 'r1vi': 0.0, 'r1vq': 0.0, 'r2pw': 20e-9, 'r2vi': 0.0, 'r2vq': 0.0,
                        'reps': 1e5, 'dt': 100e-9})


def pb_awg_twopulse(self):
    self.add_inst_awg('awg1', [self.params['r1vi'], self.params['r1vq']], self.params['r1pw'])
    self.add_inst_awg([], [], self.params['dt'])
    self.add_inst_awg('awg1', [self.params['r2vi'], self.params['r2vq']], self.params['r2pw'])


def pb_awg_pulsed_ODMR_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 80e-9, 'pulsewidthvi': 24e-6})


def pb_awg_pulsed_ODMR(self):
    self.add_inst_awg('awg1', [self.params['pulsewidthvi']/self.params['pulsewidth'], 0], self.params['pulsewidth'])
