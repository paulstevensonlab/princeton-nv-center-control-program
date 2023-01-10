def pb_PLE_pulsed_params(self):
    self.params = self.default_params()
    self.params.update({'reps': 500, 't_green': 1e-5, 't_green_dark': 1e-6, 'red_delay': 740e-9, 't_red': 1e-5, 't_red_dark': 1e-6, 'aom_delay2':700e-9})
    self.custom_readout = True


def pb_PLE_pulsed(self):
    # Emre Togan's repumping scheme
    #  pixel_start = self.add_inst(['green'], self.inst_set.LOOP, np.uint32(self.params['reps']), self.params['t_green'])  # todo: possible to add ctr1 detection
    #  self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_green_dark'])
    #  self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['t_red'])  # todo: add AOM delay for red laser
    #  self.add_inst([], self.inst_set.END_LOOP, pixel_start, self.params['t_red_dark'])

   pixel_start = self.add_inst(['green'], self.inst_set.LOOP, np.uint32(self.params['reps']), self.params['t_green'])  # todo: possible to add ctr1 detection
   self.add_inst([], self.inst_set.CONTINUE, 0, self.params['t_green_dark'])
   self.add_inst(['red'], self.inst_set.CONTINUE, 0, self.params['red_delay'])
   self.add_inst(['red', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['t_red'] - self.params['red_delay'])  # todo: add AOM delay for red laser
   self.add_inst(['ctr0'], self.inst_set.CONTINUE, 0,self.params['red_delay'])  # todo: add AOM delay for red laser
   self.add_inst([], self.inst_set.END_LOOP, pixel_start, self.params['t_red_dark'] - self.params['red_delay'])


def pb_SiV_exp_params(self):
    self.params = self.repump_params()


def pb_SiV_exp(self):
    # this is now taken care of in the set_program
    pass
    # self.add_inst(['SiV_repumping'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_repumping'])
    # self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau_repump'])
    # self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['repumping_delay'])
    # self.add_inst(['SiV_readout'], self.inst_set.CONTINUE, 0, self.params['readout_delay'])
    # self.add_inst(['SiV_readout', 'ctr0'], self.inst_set.CONTINUE, 0, self.params['pulsewidth_readout'])
    # self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['repumping_delay'] + self.params['readout_delay'])
