from PyQt5.QtCore import QThread, pyqtSignal
import file_utils, os


class ExpThread(QThread):

    signal_wait_for_mainexp = pyqtSignal()
    signal_log = pyqtSignal(str)
    signal_log_clear = pyqtSignal()

    def __init__(self, mainexp, wait_condition=None):
        QThread.__init__(self)
        self.mainexp = mainexp
        self.wait_condition = wait_condition

        if wait_condition is not None:
            self.signal_wait_for_mainexp.connect(wait_condition.wakeAll)

        self.signal_log.connect(mainexp.log)
        self.signal_log_clear.connect(mainexp.log_clear)
        self.finished.connect(mainexp.set_gui_defaults)
        self.cancel = False

    def run(self):
        pass

    def log(self, s):
        self.signal_log.emit(s)

    def log_clear(self):
        self.signal_log_clear.emit()

    def save_data(self, filename, data_dict, graph=None, fig=None, sweep_params=None):
        wavenum = filename.split('_')[-1]
        if wavenum.isdigit():
            wavenum = int(wavenum)
        else:
            raise ValueError('filename is not compatible with the format dataname_#')

        # Default Sweep Params for the experiment
        if sweep_params is None:
            sweep_params = dict((k, v) for k, v in self.mainexp.exp_params.items())

            # Add laser power if it is defined
            if hasattr(self.mainexp, 'pm100d'):
                p532 = self.mainexp.pm100d.get_pow() * 1e3
                if 'readout_params' in sweep_params.keys():
                    sweep_params['readout_params']['p532'] = p532
                else:
                    sweep_params['readout_params'] = {'p532': p532}

        sweep_params['sample'] = self.mainexp.linein_sample_name.text()

        file_utils.save_data(filename, data_dict, graph=graph, fig=fig, sweep_params=sweep_params)

        # Increment wavenum if it has not been incremented already
        if self.mainexp.wavenum < wavenum:
            raise Warning('wavenum is messed up!')
        elif self.mainexp.wavenum == wavenum:
            self.mainexp.wavenum += 1
        else:
            # self.mainexp.wavenum has already been incremented
            pass

    # Emit a signal for the mainexp to unlock mutex, which should be the last thing mainexp get to execute.
    # This ensures the previous signals get executed
    def wait_for_mainexp(self):
        self.signal_wait_for_mainexp.emit()
        self.mainexp.mutex.lock()
        try:
            self.wait_condition.wait(self.mainexp.mutex)
        finally:
            self.mainexp.mutex.unlock()

    def run_script(self, filename):
        # Build a dictionary of functions that can be called from scripts
        method_list = [func for func in dir(self.mainexp.task_handler)
                       if callable(getattr(self.mainexp.task_handler, func)) and
                       not func.startswith("__")]

        method_dict = {'self': self, 'mainexp': self.mainexp, 'pb': self.mainexp.pb}
        for m in method_list:
            method_dict[m] = getattr(self.mainexp.task_handler, m)

        script = os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts', filename))
        if os.path.isfile(script):
            self.log('Executing %s' % os.path.basename(script))
            try:
                exec(open(script).read(), method_dict)
            except:
                self.log('YOUR SCRIPT HAS AN ERROR! %s' % os.path.basename(script))
            self.log('Finished executing %s' % os.path.basename(script))
