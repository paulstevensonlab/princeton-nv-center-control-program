def pb_cpmg_params(self):
    self.params = self.default_params()
    self.params.update(
        {'pulsewidth_pi': 56e-9, 'pulsewidth_pi2': 28e-9, 'pulsewidth_pi32': 84e-9, 'tau': 100e-9, 'n': 1.0, 'dt': 0,
         'inv': 0})


def pb_cpmg(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
    for i in range(np.uint32(self.params['n'])):
        self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['pulsewidth_pi'] / 2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi'])
        self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['pulsewidth_pi'] / 2
                      + self.params['dt'])
    if np.uint32(self.params['inv']) == 0:  # determine whether to apply pi/2 or 3pi/2 pulse
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
    else:
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi32'])

def pb_ramsey_params(self):
    self.params = self.default_params()
    self.params.update(
        {'pulsewidth_pi2': 28e-9, 'pulsewidth_pi32': 84e-9, 'tau': 100e-9,
         'inv': 0})


def pb_ramsey(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])

    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])

    if np.uint32(self.params['inv']) == 0:  # determine whether to apply pi/2 or 3pi/2 pulse
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
    else:
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi32'])
