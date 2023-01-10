def pb_DQ_t1_params(self):
    self.pb_rabi_params(self)
    self.params.update({'inv': 0})


def pb_DQ_t1(self):
    self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])

    if np.uint32(self.params['inv']) == 0:
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    else:
        self.add_inst(['mw2'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])


def pb_SQ_t1_params(self):
    self.pb_rabi_params(self)
    self.params.update({'inv': 0})


def pb_SQ_t1(self):
    self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['tau'])
    if np.uint32(self.params['inv']) == 0:
        self.add_inst([''], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
    else:
        self.add_inst(['mw1'], self.inst_set.CONTINUE, 0, self.params['pulsewidth'])
