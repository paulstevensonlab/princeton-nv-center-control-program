from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QThread
import time, sys, os
from inspect import signature

import test_threading as mainwindow
import warnings

def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook


def defaultfunc(thd):
    print('default')


class Thread_Main(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.task_handler = TaskHandler(self)
        self.confocal = Thread_Confocal(self)
        self.esr = Thread_ESR(self)

        # self.btn_test.clicked.connect(self.task_handler.run_program)
        # self.btn_start_script.clicked.connect(self.task_handler.start)
        # self.btn_cancel.clicked.connect(self.task_handler.import_functions)

        self.btn_import.clicked.connect(self.task_handler.import_functions)
        self.cbox_pb.currentIndexChanged[str].connect(self.task_handler.set_pulse)
        self.btn_run.clicked.connect(self.task_handler.pb_start)
        self.threadnum = 1

    def test(self):
        print('test button-----------------------------')

    def run_something(self):
        print('something')

    def cmd1(self):
        print('cmd1 start')
        time.sleep(2)
        print('cmd1 finish')

    def cmd2(self):
        print('cmd2')
        time.sleep(2)
        print('cmd2 finish')

    def cmd3(self):
        print('cmd3')
        time.sleep(2)
        print('cmd3 finish')


# todo: use this to test pulseblaster imports

class TaskHandler(QThread):
    def __init__(self, mainexp):
        QThread.__init__(self)
        self.mainexp = mainexp
        self.threadnum = 1

        self.func = defaultfunc
        self.exp_list = []
        # print('GLOBALS')
        # print(globals())
        # print('LOCALS')
        # print(locals())
        self.import_functions()

    def import_functions(self):
        self.exp_list = ['']
        pb_func_dir = os.path.join(os.getcwd(), 'pb_functions')

        python_files = sorted([f for f in os.listdir(pb_func_dir)
                        if os.path.isfile(os.path.join(pb_func_dir, f)) and f.endswith('.py')])

        print('Executing Files except for import_pb_functions')
        python_files.remove('import_pb_functions.py')  #  This automatically throws an error if import_pb_functions is not defined
        import_pb_functions = open(os.path.join(pb_func_dir, 'import_pb_functions.py')).read()
        print(python_files)
        for f in python_files:
            try:
                exec(open(os.path.join(pb_func_dir, f)).read() + import_pb_functions)
            except Exception:
                print('File Error: ' + f)
        # print(self.list_functions())
        self.mainexp.cbox_pb.clear()
        self.mainexp.cbox_pb.addItems(self.exp_list)

    def set_pulse(self, name):
        if name:
            self.func = getattr(self, 'pb_' + name)

    def pb_start(self):
        self.func(self)

    def run(self):
        method_list = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("__")]
        method_dict = locals()
        for m in method_list:
            method_dict[m] = getattr(self, m)
        exec(open('testscript.py').read(), globals(), method_dict)

    def run_program(self):
        print('running program')
        if len(signature(self.func).parameters) == 0:
            print('len=0')
            self.func()
        elif len(signature(self.func).parameters) == 1:
            print('len=1')
            self.func(self)
        else:
            print('error')

    def default_func(self):
        print('default')

    def confocal_start(self):
        if not self.mainexp.confocal.isRunning():
            threadnum = self.threadnum
            print('starting confocal #%d' % threadnum)
            self.threadnum += 1
            self.mainexp.confocal.start()
            self.mainexp.confocal.wait()
            print('finished calling confocal.start() #%d' % threadnum)
            self.confocal_stop()
        else:
            print('Cannot start: confocal is running')

    def confocal_cancel(self):
        self.mainexp.confocal.cancel = True

    def confocal_stop(self):
        print('mainexp realize confocal finish')

    def esr_start(self):
        if not self.mainexp.esr.isRunning():
            threadnum = self.threadnum
            print('starting esr #%d' % threadnum)
            self.mainexp.esr.start()
            self.mainexp.esr.wait()
            print('finished calling esr.start() #%d' % threadnum)
            self.esr_stop()
        else:
            print('Cannot start: esr is running')

    def esr_stop(self):
        print('mainexp realize esr finish')


class Thread_Confocal(QThread):

    def __init__(self, mainexp):
        QThread.__init__(self)
        self.mainexp = mainexp
        # self.finished.connect(self.mainexp.confocal_stop)
        self.cancel = False

    def run(self):
        self.cancel = False

        for _ in range(10):
            if not self.cancel:
                print('confocal is running')
                time.sleep(1)
        print('confocal is finished')


class Thread_ESR(QThread):

    def __init__(self, mainexp):
        QThread.__init__(self)
        self.mainexp = mainexp
        # self.finished.connect(self.mainexp.esr_stop)

    def run(self):
        print('esr is running for 2 seconds')
        time.sleep(2)
        print('esr is finished')


def main():
    """Packaged main function that launches GUI"""
    app = QtWidgets.QApplication(sys.argv)
    form = Thread_Main()
    form.show()

    # form.chkbox_tracktime.setChecked(False)
    # form.chkboxsave.setChecked(False)
    app.exec_()


if __name__ == '__main__':
    main()
