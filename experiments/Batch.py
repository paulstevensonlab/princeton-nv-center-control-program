from PyQt5.QtCore import pyqtSignal

import os, time
from . import ExpThread


class Batch(ExpThread.ExpThread):
    '''
    this class will utilize the list of nvs as collected in the gui
    and run a bunch of experiments on them
    '''

    signal_batch_nvlist_update_offset = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)

        self.track_local_shift = False
        self.last_cal_time = -1.0
        self.cal_period = 0.0

        self.signal_batch_nvlist_update_offset.connect(mainexp.nvlist_update_offset)
        self.finished.connect(self.mainexp.task_handler.reset)

        # Build a dictionary of functions that can be called from scripts
        method_list = [func for func in dir(self.mainexp.task_handler)
                       if callable(getattr(self.mainexp.task_handler, func)) and
                       not func.startswith("__")]
        self.method_dict = {'mainexp': self.mainexp, 'pb': self.mainexp.pb}
        for m in method_list:
            self.method_dict[m] = getattr(self.mainexp.task_handler, m)

    def run(self):
        self.cancel = False  # For preventing next NV/scripts from running
        self.mainexp.btn_nvlist_start.setEnabled(False)
        self.mainexp.btn_nvlist_stop.setEnabled(True)
        # For stopping execution of anything inside the script that calls TaskHandler functions
        self.mainexp.task_handler.cancel = False

        self.track_local_shift = self.mainexp.chkbx_nvlist_localshift.isChecked()
        numrows = self.mainexp.table_nvlist.rowCount()

        if self.mainexp.list_nvlist_calscripts.count() or self.mainexp.list_nvlist_scripts.count():
            if numrows != 0 and self.mainexp.chkbx_nvlist_enable.isChecked():
                selectedrows = self.mainexp.table_nvlist.selectionModel().selectedRows()
                subindex = []

                if not selectedrows:
                    subindex = range(numrows)
                else:
                    for rowitem in selectedrows:
                        subindex.append(rowitem.row())

                for nvind in subindex:
                    if not self.cancel:
                        self.mainexp.task_handler.setval('nvnum', nvind+1)
                    if not self.cancel:
                        self.run_scripts()
                    if not self.cancel:
                        self.nvlist_update_offset()
                self.log('finished sweeping full nv list')
            else:
                # no NV in the list but there are scripts
                self.run_scripts()

    def stop(self):
        self.cancel = True
        self.mainexp.task_handler.cancel = True
        self.mainexp.thread_confocal.cancel = True
        self.mainexp.thread_sweep.cancel = True
        self.mainexp.thread_picoharp.cancel = True
        self.mainexp.thread_liveapd.cancel = True
        self.mainexp.thread_seqapd.cancel = True
        self.mainexp.thread_satcurve.cancel = True

    def run_scripts(self):
        cal_scripts = []
        for cal_index in range(self.mainexp.list_nvlist_calscripts.count()):
            cal_script_name = self.mainexp.list_nvlist_calscripts.item(cal_index).text()
            cal_scripts.append(cal_script_name)

        exp_scripts = []
        for script_index in range(self.mainexp.list_nvlist_scripts.count()):
            exp_script_name = self.mainexp.list_nvlist_scripts.item(script_index).text()
            exp_scripts.append(exp_script_name)

        for exp_script in exp_scripts:
            self.cal_period = self.mainexp.int_nvlist_caltime.value()
            self.last_cal_time = -1.0
            if not self.cancel:
                # Run calibration if needed
                if cal_scripts and (time.time() - self.last_cal_time > self.cal_period * 60):
                    for cal_script in cal_scripts:
                        try:
                            self.log('Running %s' % cal_script)
                            exec(open(os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts', cal_script))).read(),
                                 self.method_dict)
                            self.log('Finished: %s' % cal_script)
                            time.sleep(0.1)
                            self.last_cal_time = time.time()
                        except Exception as e:
                            self.log('Calibration script %s error!' % cal_script)
                            self.log(str(e))
                try:
                    print('Running %s' % exp_script)
                    self.log('Running %s' % exp_script)
                    exec(open(os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts', exp_script))).read(),
                         self.method_dict)
                    self.log('Finished: %s' % exp_script)
                    time.sleep(0.1)
                except Exception as e:
                    self.log('Experiment script %s error!' % exp_script)
                    self.log(str(e))

    def nvlist_update_offset(self):
        self.signal_batch_nvlist_update_offset.emit()
        if self.isRunning():
            self.wait_for_mainexp()

        time.sleep(0.1)
