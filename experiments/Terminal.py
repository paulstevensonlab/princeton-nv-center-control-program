from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal

from . import ExpThread
from instruments import remotecontrol
import rpyc
from rpyc.utils.server import ThreadedServer
import threading


class Terminal(ExpThread.ExpThread):
    '''
    this class will utilize the list of nvs as collected in the gui
    and run a bunch of experiments on them
    '''

    signal_terminal_wait_for_mainexp = pyqtSignal()

    def __init__(self, mainexp, wait_condition):
        super().__init__(mainexp, wait_condition)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.flush_cmdqueue)

        # Build a dictionary of functions that can be called from scripts
        method_list = [func for func in dir(self.mainexp.task_handler)
                       if callable(getattr(self.mainexp.task_handler, func)) and
                       not func.startswith("__")]
        self.method_dict = {'mainexp': self.mainexp, 'pb': self.mainexp.pb}
        for m in method_list:
            self.method_dict[m] = getattr(self.mainexp.task_handler, m)

        self.method_dict['batch'] = self.batch


    def flush_cmdqueue(self):
        if self.mainexp.chkbx_terminal_thd.isChecked():
            if not self.isRunning() and self.mainexp.task_handler.everything_finished() and\
                    self.mainexp.list_terminal_cmdqueue.count():
                self.start()
        elif self.mainexp.list_terminal_cmdqueue.count():
            self.start()

    def run(self):
        cmd = self.mainexp.list_terminal_cmdqueue.takeItem(0).text()
        self.mainexp.label_terminal_cmdlog.append(cmd)
        self.mainexp.label_terminal_cmdlog.verticalScrollBar().setSliderPosition(
            self.mainexp.label_terminal_cmdlog.verticalScrollBar().maximum())

        try:
            exec(cmd, self.method_dict)
        except Exception as e:
            self.log(str(e))

    def stop(self):
        self.cancel = True
        self.mainexp.task_handler.cancel = True
        self.mainexp.thread_confocal.cancel = True
        self.mainexp.thread_sweep.cancel = True
        self.mainexp.thread_batch.cancel = True

    def batch(self, nvlist, scripts):
        if nvlist and scripts:
            self.mainexp.table_nvlist.clearSelection()
            # Select Multiple NVs and return to normal selection mode
            self.mainexp.table_nvlist.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
            for nvnum in nvlist:
                self.mainexp.table_nvlist.selectRow(nvnum-1)
            self.mainexp.table_nvlist.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.mainexp.nvlist_calscripts_clear()
            self.mainexp.nvlist_scripts_clear()
            for script in scripts:
                self.list_nvlist_scripts.addItem(script)

            if self.isRunning():
                self.wait_for_mainexp()

            self.mainexp.thread_batch.start()
            self.mainexp.thread_batch.wait()

    def submit_cmd(self):
        # Submit the cmd into the queue, which should get executed automatically by the timer
        cmd = self.mainexp.linein_terminal_cmd.text()
        self.mainexp.list_terminal_cmdqueue.addItem(cmd)
        self.mainexp.linein_terminal_cmd.clear()
