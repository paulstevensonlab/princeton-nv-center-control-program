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
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'],
                      customflags=['mw1', 'mw2'])
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    # Y90
    self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
    self.add_inst_awg([], [], self.params['dt'])


def pb_awg_qurep_readout_params(self):
    self.pb_awg_qurep_init_params(self)
    self.params.update({'inv': 0})


def pb_awg_qurep_readout(self):
    # wait for mw1 to turn on
    self.add_inst_awg([], [], self.params['dt'])

    # X90
    self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
    # Y, pi pulse on DEER spin should be same time as on NV
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg('awg1', [self.params['y180vi'], self.params['y180vq']], self.params['y180pw'],
                      customflags=['mw1', 'mw2'])
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)

    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])


def pb_awg_qurep_rabi_params(self):
    self.pb_awg_qurep_init_params(self)
    self.pb_awg_qurep_readout_params(self)  # this overwrites the awg_qurep_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9, 'deerpulsewidth': 36e-9})


def pb_awg_qurep_rabi(self):
    self.pb_awg_qurep_init()

    # pulse on DEER
    self.add_inst_awg([], [], self.params['deerpulsewidth'], customflags=['mw2'])
    # wait for tau_p
    self.add_inst_awg([], [], self.params['tau_p'])

    self.pb_awg_qurep_readout()


def pb_awg_qurep_ramsey_params(self):
    self.pb_awg_qurep_init_params(self)
    self.pb_awg_qurep_readout_params(self)  # this overwrites the awg_qurep_init_params() but makes logical flow
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
    self.pb_awg_qurep_init_params(self)
    self.pb_awg_qurep_readout_params(self)  # this overwrites the awg_qurep_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9})


def pb_awg_qurep_echo(self):
    pb_awg_qurep_init(self)

    # DEER pi/2
    self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])
    # DEER free evolution and pi
    self.add_inst_awg([], [], self.params['tau_p'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg([], [], self.params['y180pw'], customflags=['mw2'])
    self.add_inst_awg([], [], self.params['tau_p'] / 2 - self.params['y180pw'] / 2)
    # DEER pi/2
    self.add_inst_awg([], [], self.params['x90pw'], customflags=['mw2'])

    self.pb_awg_qurep_readout(self)


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
