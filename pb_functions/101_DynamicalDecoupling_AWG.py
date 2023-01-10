def pb_awg_cpmg_params(self):
    self.params = self.default_params()
    self.params.update({'r90pw': 20e-9, 'r90vi': 0.0, 'r90vq': 0.0, 'r180pw': 20e-9, 'r180vi': 0.0, 'r180vq': 0.0,
                        'reps': 1e5, 'tau': 0.0, 'n': 1, 'inv': 0})


def pb_awg_cpmg(self):
    self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
    for i in range(np.uint32(self.params['n'])):
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
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
        start_xy8 = self.add_inst([], self.inst_set.LOOP, np.uint32(self.params['k']), self.params['tau']/2 - self.params['x180pw']/2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['x180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
        # Y
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['y180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
        # X
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['x180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['x180pw']/2)
        # Y
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['y180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['y180pw']/2)
        # Y
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['y180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
        # X
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['x180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
        # Y
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['y180pw'])
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['y180pw'] / 2)
        # X
        self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'] / 2 - self.params['x180pw'] / 2)
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['x180pw'])
        self.add_inst([], self.inst_set.END_LOOP, start_xy8, self.params['tau'] / 2 - self.params['x180pw'] / 2)
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


def pb_awg_xy8_interp_params(self):
    self.pb_awg_xy8_params(self)


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


def pb_awg_xy8_interp2_params(self):
    self.pb_awg_xy8_params(self)


def pb_awg_xy8_interp2(self):
    self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])

    # Quantum Interpolation: arXiv:1604.01677
    tau2_pi2_ns = round((self.params['tau']-self.params['x180pw'])/2*1e9) # assume pi pulsewidths for X and Y are the same
    t0 = round(4e-9 * int(tau2_pi2_ns/4), 9)  # building block U0
    t1 = round(4e-9 * int(tau2_pi2_ns/4 + 1), 9)  # building block U1

    m = 0
    sample = float(tau2_pi2_ns % 4)/4.0  # fraction of 4ns awg sampling time

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
            self.add_inst_awg([], [], t)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], t)
            # Y
            self.add_inst_awg([], [], t)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], t)
        else:
            # Y
            self.add_inst_awg([], [], t)
            self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'])
            self.add_inst_awg([], [], t)
            # X
            self.add_inst_awg([], [], t)
            self.add_inst_awg('awg1', [self.params['x180vi'], self.params['x180vq']], self.params['x180pw'])
            self.add_inst_awg([], [], t)

    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
