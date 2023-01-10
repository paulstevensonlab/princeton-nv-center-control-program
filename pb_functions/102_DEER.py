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
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'],
                          customflags=flags)
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
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


# allow sweeping of the deer pulse, assuming all time durations are mod(10 ns)
# **tau and pulsewidth_pi and deerpulsewidth has to be mod(20)
def pb_deer_mamin_params(self):
    self.params = self.default_params()
    self.params.update({'pulsewidth_pi': 200e-9, 'pulsewidth_pi2': 100e-9, 'pulsewidth_pi32': 100e-9, 'deerpulsewidth': 200e-9,
                        'tau': 2e-6, 'dt': 0.0, 'inv': 0})


def pb_deer_mamin(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])  # NV pi/2

    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi']/2)
    self.add_inst(['mw2'], self.inst_set.CONTINUE, 0, self.params['deerpulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi']/2 - self.params['deerpulsewidth'])

    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi'])

    self.add_inst(['mw2'], self.inst_set.CONTINUE, 0, self.params['deerpulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau']/2 - self.params['pulsewidth_pi2']/2 - self.params['deerpulsewidth'])

    if np.uint32(self.params['inv']) == 0:  # determine whether to apply pi/2 or 3pi/2 pulse
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi2'])
    else:
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_pi32'])
