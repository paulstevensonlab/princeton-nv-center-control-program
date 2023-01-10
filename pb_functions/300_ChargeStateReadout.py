def pb_timetrace_green_cali_params(self):
    self.params = self.default_params()
    self.params.update(
        {'t_init': 5e-3, 't_mw': 100e-9, 't_green': 700e-9, 't_end': 1e-6, 'reps': 1e3,
         'timetrace': 0.0})


def pb_timetrace_green_cali(self):
    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0, self.params['t_init'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['t_mw'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
    self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])

def pb_timetrace_orange_params(self):
    self.params = self.default_params()
    self.params.update(
        {'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_orange': 25e-3, 't_end': 1e-6, 'reps': 1e3,
         'timetrace': 0.0})


def pb_timetrace_orange(self):
    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0,
                  self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_wait'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange'])
    self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])

def pb_timetrace_red_params(self):
    self.params = self.default_params()
    self.params.update(
        {'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_red': 25e-3, 't_end': 1e-6, 'reps': 1e3,
         'timetrace': 0.0})


def pb_timetrace_red(self):
    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0,
                  self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_wait'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['t_red'])
    self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])

def pb_timetrace_redionization_params(self):
    self.params = self.default_params()
    self.params.update(
        {'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_orange': 25e-3, 't_end': 1e-6, 'reps': 1e3,
         'timetrace': 0.0})


def pb_timetrace_redionization(self):
    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0,
                  self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_wait'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange'])
    self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])

# def pb_timetrace_orangeonly_params(self):
#     self.params = self.default_params()
#     self.params.update(
#         {'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_orange': 25e-3, 't_end': 1e-6, 'reps': 1e3,
#          'timetrace': 0.0})
#
#
# def pb_timetrace_orangeonly(self):
#     self.add_inst([], self.inst_set.CONTINUE, 0,
#                   self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
#     self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
#     self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_wait'])
#     self.add_inst(['ctr1', 'orange'], self.inst_set.CONTINUE, 0, self.params['t_orange'])
#     self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])


def pb_timetrace_orangeorange_params(self):
    self.params = self.default_params()
    self.params.update({'t_init': 5e-3, 't_green': 700e-9, 't_wait': 1e-3, 't_orange1': 25e-3, 't_orange2': 25e-3, 'tau': 0.0, 't_end': 1e-6, 'reps': 1e3,
         'timetrace': 0.0})


def pb_timetrace_orangeorange(self):
    self.add_inst(['ctr1'], self.inst_set.CONTINUE, 0,
                  self.params['t_init'] - self.params['t_green'] - self.params['t_wait'])
    self.add_inst(['green'], self.inst_set.CONTINUE, 0, self.params['t_green'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_wait'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange1'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['tau'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['t_orange2'])
    self.add_inst([], self.inst_set.BRANCH, 0, self.params['t_end'])