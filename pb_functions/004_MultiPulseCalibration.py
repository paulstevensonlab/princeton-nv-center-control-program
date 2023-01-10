def pb_cal_xx_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 20e-9, 'n': 1, 'inv': 0})


def pb_cal_xx(self):
    numpulses = np.uint32(self.params['n']) + np.uint32(self.params['inv'])

    for i in range(numpulses):
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
        if i != numpulses - 1:
            self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])


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
        if not i % 2:  # X
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
