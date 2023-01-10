def pb_newctr_rabi_params(self):
    self.newctr_ctrticks = [[0, 1], [2, 3]]
    self.newctr_sigref = [0, 1]
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0})


def pb_newctr_rabi(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])


def pb_newctr_rabi_chargestate_params(self):
    self.newctr_ctrticks = [[0, 1], [2, 3], [4, 5]]
    self.newctr_sigref = [1, 2]
    self.params = self.default_params()
    self.params.update({'pulsewidth': 20e-9, 'reps': 1e5, 'tau': 0.0, 't_orange': 1e-3, 't_orange_dark': 2e-6})
    self.custom_readout = True


def pb_newctr_rabi_chargestate(self):
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
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, time_green)
    self.add_inst(awglist, self.inst_set.CONTINUE, 0,
                  time_dark - (2 * time_det + time_sep - (time_green - aom_delay)))
    outer_loop = self.add_inst([], self.inst_set.LOOP, n_loops,
                               (2 * time_det + time_sep - (time_green - aom_delay)))
    if self.awg_enable:
        self.clear_inst_awg()
    # do charge state readout
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange'] - time_trig)
    self.add_inst(['ctr0'], self.inst_set.CONTINUE, 0, time_trig)
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_orange_dark'] - time_trig)
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])
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
    # do charge state readout
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, time_trig)
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange'] - time_trig)
    self.add_inst(['ctr0'], self.inst_set.CONTINUE, 0, time_trig)
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_orange_dark'] - time_trig)
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])
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


def pb_newctr_awg_deer_cpmg_params(self):
    self.newctr_ctrticks = [[0, 1], [2, 3], [4, 5], [6, 7]]
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
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
        self.add_inst_awg('awg1', [self.params['r180vi'], self.params['r180vq']], self.params['r180pw'],
                          customflags=flags)
        self.add_inst_awg([], [], self.params['tau'] / 2 - self.params['r180pw'] / 2)
    if np.uint32(self.params['inv']) == 0:  # determine whether to invert the phase of the last r90
        self.add_inst_awg('awg1', [-self.params['r90vi'], -self.params['r90vq']], self.params['r90pw'])
    else:
        self.add_inst_awg('awg1', [self.params['r90vi'], self.params['r90vq']], self.params['r90pw'])
