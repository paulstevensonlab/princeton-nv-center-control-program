def pb_awg_qurep2_init_params(self):
    self.pb_awg_qurep_init_params(self)
    self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0})


def pb_awg_qurep2_init(self):
    # X90
    self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
    # Y, pi pulse on DEER spin should be same time as on NV
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                         [self.params['deer_y180vi'], self.params['deer_y180vq']]],
                      self.params['y180pw'])
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    # Y90
    self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    # wait for mw1 to turn off
    self.add_inst_awg([], [], self.params['dt'])


def pb_awg_qurep2_readout_params(self):
    self.pb_awg_qurep_readout_params(self)
    self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0})


def pb_awg_qurep2_readout(self):
    # wait for mw1 to turn on
    self.add_inst_awg([], [], self.params['dt'])

    # X90
    self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
    # Y, pi pulse on DEER spin should be same time as on NV
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                         [self.params['deer_y180vi'], self.params['deer_y180vq']]],
                      self.params['y180pw'])
    self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    # -Y90
    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])


def pb_awg_qurep2_cpmg_init_params(self):
    self.pb_awg_qurep_init_params(self)
    self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0, 'n': 1})


def pb_awg_qurep2_cpmg_init(self):
    # X90
    self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
    # Y, pi pulse on DEER spin should be same time as on NV
    for _ in range(np.uint32(self.params['n'])):
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                             [self.params['deer_y180vi'], self.params['deer_y180vq']]],
                          self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    # Y90
    self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])

    # wait for mw1 to turn off
    self.add_inst_awg([], [], self.params['dt'])


def pb_awg_qurep2_cpmg_readout_params(self):
    self.pb_awg_qurep_readout_params(self)
    self.params.update({'deer_y180vi': 0.0, 'deer_y180vq': 300.0, 'n': 1})


def pb_awg_qurep2_cpmg_readout(self):
    # wait for mw1 to turn on
    self.add_inst_awg([], [], self.params['dt'])

    # X90
    self.add_inst_awg('awg1', [self.params['x90vi'], self.params['x90vq']], self.params['x90pw'])
    # Y, pi pulse on DEER spin should be same time as on NV
    for _ in range(np.uint32(self.params['n'])):
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
        self.add_inst_awg(['awg1', 'awg2'], [[self.params['y180vi'], self.params['y180vq']],
                                             [self.params['deer_y180vi'], self.params['deer_y180vq']]],
                          self.params['y180pw'])
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)
    # -Y90
    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])


def pb_awg_qurep2_deer_params(self):
    self.pb_awg_qurep_readout_params(self)
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
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2 - self.params['deerpw'])
    else:
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['y180pw'] / 2)

    # -Y90
    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])


def pb_awg_qurep2_rabi_params(self):
    self.pb_awg_qurep2_init_params(self)
    self.pb_awg_qurep2_readout_params(self)  # this overwrites the awg_qurep2_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9, 'deerpulsewidth': 36e-9, 'deer_vi': 0.0, 'deer_vq': 0.0})


def pb_awg_qurep2_rabi(self):
    self.pb_awg_qurep2_init(self)

    # pulse on DEER
    self.add_inst_awg('awg2', [self.params['deer_vi'], self.params['deer_vq']], self.params['deerpulsewidth'],
                      customflags=['mw2'])
    # wait for tau_p
    self.add_inst_awg([], [], self.params['tau_p'])

    self.pb_awg_qurep2_readout(self)


def pb_awg_qurep2_cpmg_rabi_params(self):
    self.pb_awg_qurep2_cpmg_init_params(self)
    self.pb_awg_qurep2_cpmg_readout_params(self)  # this overwrites the awg_qurep2_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9, 'deerpulsewidth': 36e-9, 'deer_vi': 0.0, 'deer_vq': 0.0})


def pb_awg_qurep2_cpmg_rabi(self):
    self.pb_awg_qurep2_cpmg_init(self)

    # pulse on DEER
    self.add_inst_awg('awg2', [self.params['deer_vi'], self.params['deer_vq']], self.params['deerpulsewidth'],
                      customflags=['mw2'])
    # wait for tau_p
    self.add_inst_awg([], [], self.params['tau_p'])

    self.pb_awg_qurep2_cpmg_readout(self)


def pb_awg_qurep2_ramsey_params(self):
    self.pb_awg_qurep2_init_params(self)
    self.pb_awg_qurep2_readout_params(self)  # this overwrites the awg_qurep2_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9,
                        'deer_x90pw': 48e-9, 'deer_x90vi': 300.0, 'deer_x90vq': 0.0,
                        'deer_y90pw': 48e-9, 'deer_y90vi': 300.0, 'deer_y90vq': 0.0})


def pb_awg_qurep2_ramsey(self):
    self.pb_awg_qurep2_init(self)

    # pulse on DEER
    self.add_inst_awg('awg2', [self.params['deer_x90vi'], self.params['deer_x90vq']], self.params['deer_x90pw'])
    # wait for tau_p
    self.add_inst_awg([], [], self.params['tau_p'])
    self.add_inst_awg('awg2', [self.params['deer_y90vi'], self.params['deer_x90vq']], self.params['deer_y90pw'])

    self.pb_awg_qurep2_readout()


def pb_awg_qurep2_echo_params(self):
    self.pb_awg_qurep2_init_params(self)
    self.pb_awg_qurep2_readout_params(self)  # this overwrites the awg_qurep2_init_params() but makes logical flow
    self.params.update({'tau_p': 1500e-9,
                        'deer_x90pw': 48e-9, 'deer_x90vi': 300.0, 'deer_x90vq': 0.0,
                        'deer_y90pw': 48e-9, 'deer_y90vi': 300.0, 'deer_y90vq': 0.0})


def pb_awg_qurep2_echo(self):
    self.pb_awg_qurep2_init(self)

    # pulse on DEER
    self.add_inst_awg('awg2', [self.params['deer_x90vi'], self.params['deer_x90vq']], self.params['deer_x90pw'])
    self.add_inst_awg([], [], self.params['tau_p'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg('awg2', [self.params['deer_y180vi'], self.params['deer_y180vq']], self.params['y180pw'])
    self.add_inst_awg([], [], self.params['tau_p'] / 2 - self.params['y180pw'] / 2)
    self.add_inst_awg('awg2', [self.params['deer_y90vi'], self.params['deer_x90vq']], self.params['deer_y90pw'])

    self.pb_awg_qurep2_readout(self)


def pb_awg_qurep2_hh_params(self):
    self.params = self.default_params(self)
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
                      self.params['pulsewidth'] - self.params['deerpulsewidth'] - self.params['dt'] - self.params[
                          'y90pw'])

    self.add_inst_awg([], [], self.params['dt'])

    if np.uint32(self.params['inv']) == 0:  # determine whether the final state should be 0 or 1
        self.add_inst_awg('awg1', [-self.params['y90vi'], -self.params['y90vq']], self.params['y90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['y90vi'], self.params['y90vq']], self.params['y90pw'])
