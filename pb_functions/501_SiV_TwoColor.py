def pb_onecolorAA_params(self):
    self.params = self.default_params()
    self.params.update(
        {'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timesep': 1e-6, 'timemw': 2e-7})
    self.custom_readout = True


def pb_onecolorAA(self):
    reps = self.params['reps']
    n_inner_loops = 100
    n_loops = math.floor(reps / n_inner_loops)
    print(n_loops)
    outer_loop = self.add_inst(['trig', 'orange'], self.inst_set.LOOP, n_loops, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    inner_loop = self.add_inst(['orange'], self.inst_set.LOOP, n_inner_loops - 1, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.END_LOOP, inner_loop, self.params['timemw'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.END_LOOP, outer_loop, self.params['aomdelay'] + self.params['timedark'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)


def pb_twocolorABAB_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timesep': 1e-6,
                        'readoutdelay': 5e-7, 'timemw': 2e-7})
    self.custom_readout = True


def pb_twocolorABAB(self):
    reps = self.params['reps']
    n_inner_loops = 100
    n_loops = math.floor(reps / n_inner_loops)
    print(n_loops)
    outer_loop = self.add_inst(['trig', 'orange'], self.inst_set.LOOP, n_loops, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    inner_loop = self.add_inst(['red'], self.inst_set.LOOP, n_inner_loops - 1, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.END_LOOP, inner_loop, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.END_LOOP, outer_loop, self.params['timedark'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)


def pb_twocolorABB2_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timesepAB': 1e-6,
                        'timesepBB': 1e-6,
                        'readoutdelay': 5e-7, 'timemw': 2e-7})
    self.custom_readout = True


def pb_twocolorABB2(self):
    reps = self.params['reps']

    # if not self.isInf:
    loop_start_inst = self.inst_set.LOOP
    loop_end_inst = self.inst_set.END_LOOP
    # else:
    #     loop_start_inst = self.inst_set.CONTINUE
    #     loop_end_inst = self.inst_set.BRANCH

    outer_loop = self.add_inst(['trig', 'orange'], loop_start_inst, reps, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesepAB'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['readoutdelay'] + self.params['timesepBB'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], loop_end_inst, outer_loop, self.params['timedark'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)


def pb_twocolorABB_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timesepAB': 1e-6,
                        'timesepBB': 1e-6,
                        'readoutdelay': 5e-7, 'timemw': 2e-7})
    self.custom_readout = True


def pb_twocolorABB(self):
    reps = self.params['reps']
    n_inner_loops = 100
    n_loops = math.floor(reps / n_inner_loops)
    print(n_loops)
    outer_loop = self.add_inst(['trig', 'orange'], self.inst_set.LOOP, n_loops, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesepAB'])
    inner_loop = self.add_inst(['red'], self.inst_set.LOOP, n_inner_loops - 1, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['readoutdelay'] + self.params['timesepBB'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.END_LOOP, inner_loop, self.params['aomdelay'] + self.params['timesepAB'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['readoutdelay'] + self.params['timesepBB'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.END_LOOP, outer_loop, self.params['timedark'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)


def pb_twocolor_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timesep': 1e-6,
                        'readoutdelay': 5e-7, 'timemw': 2e-7})
    self.custom_readout = True


def pb_twocolor(self):
    reps = self.params['reps']
    n_inner_loops = 100
    n_loops = math.floor(reps / n_inner_loops)
    print(n_loops)
    outer_loop = self.add_inst(['trig', 'orange'], self.inst_set.LOOP, n_loops, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['timemw'])
    inner_loop = self.add_inst(['red'], self.inst_set.LOOP, n_inner_loops - 1, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timedark'])
    self.add_inst(['trig', 'orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['aomdelay'] + self.params['timesep'])
    self.add_inst(['mw1'], self.inst_set.END_LOOP, inner_loop, self.params['timemw'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['readoutdelay'])
    self.add_inst(['red', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], self.inst_set.END_LOOP, outer_loop, self.params['timedark'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)

def pb_SiVt1_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 4e-7, 'timedet': 1e-6, 'timesep': 2e-6, 'timedark': 5e-6})
    self.custom_readout = True

def pb_SiVt1(self):
    loop_start = self.add_inst(['orange'], self.inst_set.LOOP, self.params['reps'], self.params['aomdelay'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedet'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timesep'])
    self.add_inst(['orange', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedet'])
    self.add_inst([''], self.inst_set.END_LOOP, loop_start, self.params['aomdelay'] + self.params['timedark'])
    self.add_inst([''], self.inst_set.STOP, 0, 1e-6)

def pb_SiVShelve_params(self):
    self.params = self.default_params()
    self.params.update({'aomdelay': 5.5e-7, 'timedetect': 5e-8, 'timedark': 5e-6, 'timeinit': 1e-6, 'timewait': 1e-6,
                        'timesep': 1e-6, 'readoutdelay': 5e-7})
    self.custom_readout = True

def pb_SiVShelve(self):
    reps = self.params['reps']

    loop_start_inst = self.inst_set.LOOP
    loop_end_inst = self.inst_set.END_LOOP

    outer_loop = self.add_inst(['orange'], loop_start_inst, reps, self.params['aomdelay']-self.params['readoutdelay'])
    self.add_inst(['orange', 'red'], self.inst_set.CONTINUE, 0, self.params['timeinit'])
    self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['aomdelay']-self.params['readoutdelay'])
    self.add_inst([], self.inst_set.CONTINUE, 0, self.params['timewait'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['aomdelay'])
    self.add_inst(['orange', 'ctr1'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst(['orange'], self.inst_set.CONTINUE, 0, self.params['timesep'])
    self.add_inst(['orange', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['timedetect'])
    self.add_inst([], loop_end_inst, outer_loop, self.params['timedark'] + self.params['aomdelay'])
    self.add_inst(['orange'], self.inst_set.STOP, 0, 1e-6)