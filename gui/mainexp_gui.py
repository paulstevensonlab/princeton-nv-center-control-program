from PyQt5 import QtGui, QtCore, QtWidgets

# system imports
import sys, os, struct, scipy.io, warnings, functools, time, datetime
import pyqtgraph as pg
import PyDAQmx
import pdb
import numpy as np
import csv
import traceback
from skimage.feature import blob_log

# user-defined imports
import file_utils
import instruments as instr
import experiments as exp
from instruments import remotecontrol
import rpyc
from rpyc.utils.server import ThreadedServer
import threading

# import UI files
import mainexp as mainwindow
import mainexp_widgets


def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook


class MainExp_GUI(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, galvo2=False):
        # constructor from QMainWindow parent class
        super(self.__class__,self).__init__()

        # configure PyQTgraph to use white background
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # setupUi sits in exptdesign, as defined by Qt Designer
        self.setupUi(self)

        self.setFixedSize(self.size())

        # this will ensure that the application quits at the right time,
        # and that Qt has a chance to automatically delete all the children of the top-level window
        # before the python garbage-collector gets to work.
        # http://stackoverflow.com/questions/27131294/error-qobjectstarttimer-qtimer-can-only-be-used-with-threads-started-with-qt
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create GUI for widgets
        self.widget_tracker = mainexp_widgets.TrackerControl(self)
        self.import_gui_control(self.widget_tracker)
        self.btn_widget_tracker.clicked.connect(self.widget_tracker.display)

        self.widget_liveapd = mainexp_widgets.LiveAPD(self)
        self.import_gui_control(self.widget_liveapd)
        self.btn_widget_liveapd.clicked.connect(self.widget_liveapd.display)
        self.shortcut_widget_liveapd = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+L'), self)
        self.shortcut_widget_liveapd.activated.connect(self.btn_widget_liveapd.toggle)

        self.widget_seqapd = mainexp_widgets.SeqAPD(self)
        self.import_gui_control(self.widget_seqapd)
        self.btn_widget_seqapd.clicked.connect(self.widget_seqapd.display)

        self.widget_satcurve = mainexp_widgets.SatCurve(self)
        self.import_gui_control(self.widget_satcurve)
        self.btn_widget_satcurve.clicked.connect(self.widget_satcurve.display)

        self.widget_histogram = mainexp_widgets.Histogram(self)
        self.import_gui_control(self.widget_histogram)
        self.btn_widget_histogram.clicked.connect(self.widget_histogram.display)

        self.widget_picoharp = mainexp_widgets.Picoharp(self)
        self.import_gui_control(self.widget_picoharp)
        self.btn_widget_picoharp.clicked.connect(self.widget_picoharp.display)

        self.widget_calculator = mainexp_widgets.Calculator(self)
        self.import_gui_control(self.widget_calculator)
        self.btn_widget_calculator.clicked.connect(self.widget_calculator.display)

        self.widget_batch = mainexp_widgets.Batch(self)
        self.import_gui_control(self.widget_batch)
        self.btn_widget_batch.clicked.connect(self.widget_batch.display)

        self.widget_terminal = mainexp_widgets.Terminal(self)
        self.import_gui_control(self.widget_terminal)
        self.btn_widget_terminal.clicked.connect(self.widget_terminal.display)
        self.shortcut_widget_terminal = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+J'), self)
        self.shortcut_widget_terminal.activated.connect(self.widget_terminal.bringToFront)

        self.widget_shortcuts = mainexp_widgets.Shortcuts(self)
        self.import_gui_control(self.widget_shortcuts)
        self.btn_widget_shortcuts.clicked.connect(self.widget_shortcuts.display)

        '''INSTRUMENT INITIALIZATION'''
        instpath = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'inst_params.yaml'))
        if os.path.isfile(instpath):
            self.inst_params = file_utils.yaml2dict(instpath)
        else:
            print('inst_params.yaml not found!')

        if galvo2:
            if 'galpie2' in self.inst_params['instruments'].keys():
                self.inst_params['instruments']['galpie'] = self.inst_params['instruments']['galpie2']
                self.inst_params['instruments'].pop('galpie2')
                # No need for other instruments on the second scanner.
                # for ins in self.inst_params['instruments'].keys():
                #     if 'galpie' not in ins and 'ctr' not in ins:
                #         self.inst_params['instuments'].pop(ins)
                self.label_pb_disp.setText('galpie2')
            else:
                raise RuntimeError('Running in dual galvo mode: galpie2 not defined!')

        for ins in self.inst_params['instruments'].keys():
            try:
                # create object for instrument using mfg, and model
                # assumes driver sits at instr.[mfg].[model]
                ins_dict = self.inst_params['instruments'][ins]
                ins_class = getattr(getattr(instr, ins_dict['mfg']), ins_dict['model'])

                # Check if addr is a dictionary (e.g. NI Galvo Piezo has multiple key-value pair for constructor)
                # initialize instrument here
                if type(ins_dict['addr']) is dict:
                    setattr(self, ins, ins_class(**ins_dict['addr']))
                else:
                    setattr(self, ins, ins_class(ins_dict['addr']))

                # instr property in class follows name from exp_params.yaml file
                instrobj = getattr(self, ins)

                # any properties with 'set' in exp_params.yaml will get set here
                for settings in ins_dict.keys():
                    if 'set' in settings:
                        if type(ins_dict[settings]) is dict:
                            getattr(instrobj, settings)(**ins_dict[settings])
                        else:
                            getattr(instrobj, settings)(ins_dict[settings])

                # make custom buttons for instruments
                btnlist = [item for item in instrobj.__dir__() if 'btn_' in item]

                if btnlist:
                    nextrow = self.grid_inst_btn.rowCount()
                    self.grid_inst_btn.addWidget(QtGui.QLabel(ins), nextrow, 0)
                    i = 1
                    for btn in btnlist:
                        btn_text = btn[4:]
                        btn_obj = QtGui.QPushButton(btn_text)
                        setattr(self, 'inst_%s_%s' % (ins, btn),btn_obj)
                        btn_obj.clicked.connect(getattr(instrobj, btn))
                        self.grid_inst_btn.addWidget(btn_obj, nextrow, i)
                        i += 1
            except Exception as e:
                print('Instrument %s initilization error!' % ins)
                raise Exception(e)

        # set a flag for remote processes. Only updated if a remote "instrument" is in the config file
        self.remote_flag = False

        # Create a timer for updating wavemeter reading
        self.wavemeter_timer = QtCore.QTimer()
        self.wavemeter_timer.timeout.connect(self.wavemeter_update_freq)
        self.wavemeter_timer_update = 5  #s
        self.label_wavemeter_freq.setText('')
        if hasattr(self, 'wavemeter'):
            if self.wavemeter.isconnected:
                self.wavemeter_timer.start(self.wavemeter_timer_update * 1000)

        '''EXPERIMENT PARAMETERS'''
        self.exp_params = {'Instrument': {},
                           'Confocal': {'nvnum': 0,
                                        'xpos': float(self.dbl_tracker_xpos.value()),
                                        'ypos': float(self.dbl_tracker_ypos.value()),
                                        'zpos': float(self.dbl_tracker_zpos.value())},
                           'Pulse': {},
                           'Manual': {'Br': 2.5, 'Btheta': 0.0, 'Bphi': 0.0, 'stage_x': 0.0, 'stage_y': 0.0}}

        manual_params_file = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'sweep_params','manual.yaml'))
        if os.path.isfile(manual_params_file):
            manual_params = file_utils.yaml2dict(manual_params_file)
            for name in manual_params.keys():
                if name in self.exp_params['Manual'].keys():
                    self.exp_params['Manual'][name] = float(manual_params[name])

        self.setval = {}
        self.getval = {}
        self.sweep_var_defaults = {}
        self.awglist = []
        self.get_inst_stat = {}
        self.set_inst_stat = {}

        # Variable Dictionary
        if os.path.isfile(os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'variable_dict.csv'))):
            var_table = list(zip(*list(csv.reader(open(os.path.expanduser(os.path.join('~','Documents', 'exp_config', 'variable_dict.csv')))))))
        elif os.path.isfile(os.path.join(os.getcwd(), 'notebook_utils', 'variable_dict.csv')):
            var_table = list(zip(*list(csv.reader(open(os.path.join(os.getcwd(), 'notebook_utils', 'variable_dict.csv'))))))
        else:
            var_table = [[], [], []]

        self.dict_var_id = var_table[0]
        self.dict_var_name = var_table[1]
        self.dict_var_unit = var_table[2]

        self.tlblist = []

        '''LINK INSTRUMENT FUNCTIONS'''
        self.setval['xpos'] = self.galpie.set_X
        self.setval['ypos'] = self.galpie.set_Y
        self.setval['zpos'] = self.galpie.set_Z
        self.setval['nvnum'] = self.set_label_nvnum

        # todo: check which one is not in-use/functional in the existing code
        #  also try to make it generic and incorporate into instrument initialization?
        #  e.g. force user to define setval, getval in the instrument class

        for ins in sorted(self.inst_params['instruments'].keys()):
            if ins == 'galpie2':  # Second galvo inside the first confocal
                self.setval['xpos2'] = self.galpie2.set_X
                self.setval['ypos2'] = self.galpie2.set_Y
                self.exp_params['Confocal']['xpos2'] = 0.0
                self.exp_params['Confocal']['ypos2'] = 0.0
            if 'mw' in ins:
                # look for microwave generators
                keypow = ins + 'pow'
                keyfreq = ins + 'freq'
                self.setval[keypow] = getattr(getattr(self, ins), 'set_pow')
                self.setval[keyfreq] = getattr(getattr(self, ins), 'set_freq')
                self.getval[keypow] = getattr(getattr(self, ins), 'get_pow')
                self.getval[keyfreq] = getattr(getattr(self, ins), 'get_freq')
                self.exp_params['Instrument'][keypow] = self.getval[keypow]()
                self.exp_params['Instrument'][keyfreq] = self.getval[keyfreq]()

                # this part only supports mw1 and mw2 for now
                if ins in ['mw1', 'mw2']:
                    self.set_inst_stat['%s_onoff' % ins] = getattr(getattr(self, ins),
                                                                   'set_%s' % self.inst_params['instruments'][ins]['func_onoff'])
                    self.get_inst_stat['%s_onoff' % ins] = getattr(getattr(self, ins),
                                                                   'get_%s' % self.inst_params['instruments'][ins]['func_onoff'])
                    self.set_inst_stat['%s_iq' % ins] = getattr(getattr(self, ins),
                                                                'set_%s' % self.inst_params['instruments'][ins]['func_iq'])
                    self.get_inst_stat['%s_iq' % ins] = getattr(getattr(self, ins),
                                                                'get_%s' % self.inst_params['instruments'][ins]['func_iq'])

                    getattr(self, 'inst_btn_%s_onoff' % ins).clicked.connect(
                        functools.partial(self.set_inst_func, ins, 'onoff'))
                    getattr(self, 'inst_btn_%s_iq' % ins).clicked.connect(functools.partial(self.set_inst_func, ins, 'iq'))
                    getattr(self, 'inst_label_%s' % ins).setText('%s (%s)' % (ins, self.inst_params['instruments'][ins]['model']))
            # elif 'ctrapd' in ins:
            #     self.ctrapd.set_source(self.inst_params['instruments']['ctrapd']['addr_src'])
            elif 'awg' in ins:
                self.awglist.append(getattr(self, ins))
            elif 'voa' in ins:  # voltage-controlled optical attenuator
                # TODO: consider saving and loading these from guisettings.config
                ins_dev = getattr(self, ins)
                self.setval[ins] = getattr(ins_dev, 'set_voltage')
                self.getval[ins] = getattr(ins_dev, 'get_voltage')
                self.exp_params['Instrument'][ins] = ins_dev.get_voltage()
            elif 'flip' in ins:
                keyflipstate = ins + 'Flip'
                self.exp_params['Instrument'][keyflipstate] = 0  # this matches the initialization of the instrument class DAQmxDigitalOutput
                self.setval[keyflipstate] = getattr(getattr(self, ins), 'writeFromField')
                self.getval[keyflipstate] = getattr(getattr(self, ins), 'read')
                getattr(getattr(self, ins), 'setTrackState')(
                    self.inst_params['instruments'][ins]['track_state'])  # initialize track state from exp_params
            elif 'tlb' in ins:
                keypiezo = ins + 'piezo'
                self.exp_params['Instrument'][keypiezo] = getattr(getattr(self, ins), 'get_piezo')()
                setattr(self, '%s_ai' % ins,
                        instr.DAQmxAnalogInput.DAQmxAnalogInput(self.inst_params['instruments'][ins]['ai']))
                setattr(self, '%s_ao' % ins,
                        instr.DAQmxAnalogOutput.DAQmxAnalogOutput(self.inst_params['instruments'][ins]['ao']))
                self.setval[keypiezo] = getattr(getattr(self, '%s_ao' % ins), 'set_voltage')
                self.getval[keypiezo] = getattr(getattr(self, '%s_ao' % ins), 'get_voltage')

                self.tlblist.append(ins)
            elif 'ctlfreq' in ins:
                if hasattr(self, 'wavemeter') and self.wavemeter.isconnected:
                    getattr(self, ins).mainexp = self
                    keypiezo = ins + 'piezo'
                    keywm = ins + 'wm'
                    self.exp_params['Instrument'][keypiezo] = getattr(getattr(self, ins), 'get_piezo')()
                    self.exp_params['Instrument'][keywm] = getattr(getattr(self, ins), 'get_freq')()
                    self.ctlfreq.set_coarse_input(self.inst_params['instruments'][ins]['ai'])
                    self.ctlfreq.set_piezo_output(self.inst_params['instruments'][ins]['ao'])
                    self.setval[keypiezo] = getattr(getattr(self, ins), 'set_piezo')
                    self.getval[keypiezo] = getattr(getattr(self, ins), 'get_piezo')
                    self.setval[keywm] = getattr(getattr(self, ins), 'set_freq')
                    self.getval[keywm] = getattr(getattr(self, ins), 'get_freq')
            elif 'coil' in ins:
                keycoilcur = ins + 'Current'
                keycoilvol = ins + 'Volt'
                # keycoilMaxvol = ins + 'VoltOP'

                self.exp_params['Instrument'][keycoilcur] = 0
                self.exp_params['Instrument'][keycoilvol] = 0
                # self.exp_params['Instrument'][keycoilMaxvol] = 1

                self.setval[keycoilcur] = getattr(getattr(self, ins), 'set_current')
                self.getval[keycoilcur] = getattr(getattr(self, ins), 'get_current')
                self.setval[keycoilvol] = getattr(getattr(self, ins), 'set_voltage')
                self.getval[keycoilvol] = getattr(getattr(self, ins), 'get_voltage')
                # self.setval[keycoilMaxvol] = getattr(getattr(self, ins), 'set_voltageOP')
                # self.getval[keycoilMaxvol] = getattr(getattr(self, ins), 'get_voltageOP')
            elif 'tisapp' in ins:
                keytisapplamb = ins + 'Wavelength'
                keytisappave = ins + 'Averages'
                keytisapplambtol = ins + 'WavelengthTol'
                keytisappetalonp = ins + 'EtalonPercent'
                keytisappresp = ins + 'ResonatorPercent'
                keytisappetalonlock = ins + 'EtalonLock'
                # add etalon lock... what about status return?
                # pollTableTuneNoStatus

                if self.tisapp.isconnected:
                    self.exp_params['Instrument'][keytisapplamb] = getattr(getattr(self, ins), 'getWavelength')()
                    self.exp_params['Instrument'][keytisapplambtol] = 0.01
                    self.exp_params['Instrument'][keytisappetalonp] = 50
                    self.exp_params['Instrument'][keytisappresp] = 50
                    self.exp_params['Instrument'][keytisappetalonlock] = 0
                    self.exp_params['Instrument'][keytisappave] = 1

                    self.setval[keytisapplamb] = getattr(getattr(self, ins), 'setWavelengthScan')
                    self.getval[keytisapplamb] = getattr(getattr(self, ins), 'getWavelength')
                    self.setval[keytisapplambtol] = getattr(getattr(self, ins), 'setWavelengthTolerance')
                    self.getval[keytisapplambtol] = getattr(getattr(self, ins), 'getWavelengthTolerance')
                    self.setval[keytisappave] = getattr(getattr(self, ins), 'setNAvePLESlow')
                    self.getval[keytisappave] = getattr(getattr(self, ins), 'getNAvePLESlow')
                    self.setval[keytisappetalonp] = getattr(getattr(self, ins), 'tuneEtalon')  # was tuneEtalon
                    self.getval[keytisappetalonp] = getattr(getattr(self, ins), 'getEtalonFromField')
                    self.setval[keytisappresp] = getattr(getattr(self, ins), 'tuneResonator')
                    self.getval[keytisappresp] = getattr(getattr(self, ins), 'getResonatorFromField')
                    self.setval[keytisappetalonlock] = getattr(getattr(self, ins), 'setEtalonLockFromField')
                    self.getval[keytisappetalonlock] = getattr(getattr(self, ins), 'etalonLockStatusFromField')
            elif 'ctllaser' in ins:
                self.setval['ctl_lambda'] = getattr(getattr(self, ins), 'SetWavelength')
                self.getval['ctl_lambda'] = getattr(getattr(self, ins), 'GetWavelength')
                setattr(self, '%s_ai' % ins, instr.DAQmxAnalogInput.DAQmxAnalogInput(self.inst_params['instruments'][ins]['ai']))
                self.exp_params['Instrument']['ctl_lambda'] = 950
                self.setval['ctl_pz'] = getattr(getattr(self, ins), 'SetPiezo')
                self.getval['ctl_pz'] = getattr(getattr(self, ins), 'GetPiezo')
                self.exp_params['Instrument']['ctl_pz'] = 70
            elif 'motor' in ins:
                if getattr(self, ins).connected:
                    self.setval[ins] = getattr(getattr(self, ins), 'move_to')
                    self.getval[ins] = getattr(getattr(self, ins), 'get_position')
                    self.exp_params['Instrument'][ins] = self.getval[ins]()
            elif 'shutter' in ins:
                self.setval[ins] = getattr(getattr(self, ins), 'set_shutter')
                self.getval[ins] = getattr(getattr(self, ins), 'get_shutter')
                self.exp_params['Instrument'][ins] = self.getval[ins]()
            elif 'remote' in ins:
                self.remote_flag = True

        '''PULSEBLASTER'''
        # check if pb_dict.csv exists for customizing PB ports.
        file_pb_params = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'pb_dict.csv'))
        self.chkbx_readoutcal.setChecked(not os.path.isfile(file_pb_params))
        if not os.path.isfile(file_pb_params):
            pb_dict = {}
        else:
            try:
                _table = list(zip(*list(csv.reader(open(file_pb_params)))))
                _pbnum = [int(x) for x in _table[0]]
                _key = list(_table[1])
                _inv = [int(x) for x in _table[2]]
                pb_dict = {'pbnum': _pbnum, 'key': _key, 'inv': _inv}
                print('Using custom pb_dict.csv')
                # clear labels
                numchan = 12
                for ch in range(numchan):
                    getattr(self, 'chkbx_pb%d' % ch).setText('PB%d' % ch)

                # redo the labels
                _pbnum = pb_dict['pbnum']
                _key = pb_dict['key']
                _inv = pb_dict['inv']

                for i, v in enumerate(_pbnum):
                    if not _inv[i]:
                        getattr(self, 'chkbx_pb%d' % v).setText('PB%d (%s)' % (v, _key[i]))
                    else:
                        getattr(self, 'chkbx_pb%d' % v).setText('PB%d (blank %s)' % (v, _key[i]))
            except IndexError:
                print('Invalid pb_dict.csv file.')
                pb_dict = {}

        self.pb = instr.PulseMaster.PulseMaster(self.awglist, pb_dict)
        self.btn_pb_cw.clicked.connect(self.pb.set_cw)
        self.btn_pb_run.clicked.connect(functools.partial(self.pb.set_program, autostart=True, infinite=True))
        self.btn_pb_stop.clicked.connect(self.pb.stop)
        self.btn_pb_static.clicked.connect(self.pb_set_static)
        self.btn_pb_update_dict.clicked.connect(self.pb_update_dict)
        self.btn_pb_update_pulse_list.clicked.connect(self.pb_update_pulse_list)
        self.btn_pb_load_params.clicked.connect(self.pb_load_params)
        self.linein_trackinglaser.editingFinished.connect(self.pb_set_tracker_laser)

        # Custom PB Programming
        self.table_pbcustom.setColumnCount(4)
        self.table_pbcustom.setHorizontalHeaderLabels(['flags', 'op code', 'inst data', 'time'])
        self.table_pbcustom.setColumnWidth(0, 160)
        self.table_pbcustom.setColumnWidth(1, 70)
        self.table_pbcustom.setColumnWidth(2, 60)
        self.table_pbcustom.setColumnWidth(3, 40)
        self.btn_pbcustom_add.clicked.connect(self.pbcustom_add)
        self.btn_pbcustom_del.clicked.connect(self.pbcustom_del)
        self.btn_pbcustom_run.clicked.connect(self.pbcustom_run)
        self.btn_pbcustom_load.clicked.connect(self.pbcustom_load)
        self.btn_pbcustom_save.clicked.connect(self.pbcustom_save)

        # Load readout_params from file
        file_readout_params = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'readout_params.yaml'))
        self.chkbx_readoutcal.setChecked(not os.path.isfile(file_readout_params))
        if not self.chkbx_readoutcal.isChecked():
            self.pb.readout_params = file_utils.yaml2dict(file_readout_params)
            print('Readout Timing loaded from %s' % file_readout_params)
            # convert all the dictionary values into floats
            for key in self.pb.readout_params.keys():
                self.pb.readout_params[key] = float(self.pb.readout_params[key])

        self.chkbx_readoutcal.stateChanged.connect(self.sweep_set_readoutcal)

        '''MUTEX FOR MANUAL SETVAL PROMPTS'''
        self.mutex = QtCore.QMutex()
        self.wait_manual_setval = QtCore.QWaitCondition()
        self.wait_sweep = QtCore.QWaitCondition()
        self.wait_confocal = QtCore.QWaitCondition()
        self.wait_spectrometer = QtCore.QWaitCondition()
        self.wait_batch = QtCore.QWaitCondition()
        self.wait_terminal = QtCore.QWaitCondition()
        self.wait_taskhandler = QtCore.QWaitCondition()
        self.wait_picoharp = QtCore.QWaitCondition()
        self.wait_liveapd = QtCore.QWaitCondition()
        self.wait_seqapd = QtCore.QWaitCondition()
        self.wait_satcurve = QtCore.QWaitCondition()

        # todo: organize
        self.plt_esr_update_timer = QtCore.QTimer()
        self.plt_esr_update_timer.timeout.connect(self.sweep_esr_updateplots)
        self.plt_ple_update_timer = QtCore.QTimer()
        self.plt_ple_update_timer.timeout.connect(self.sweep_ple_updateplots)

        '''WORKER THREADS INITIALIZATION'''
        self.task_handler = exp.TaskHandler.TaskHandler(self, self.wait_taskhandler)
        self.thread_confocal = exp.Confocal.Confocal(self, self.wait_confocal)
        self.thread_sweep = exp.Sweep.Sweep(self, self.wait_sweep)
        self.thread_spectrometer = exp.Spectrometer.Spectrometer(self, self.wait_spectrometer)
        self.thread_spectrometer_init = exp.Spectrometer.SpecInitializer(self)
        self.thread_tracker = exp.Tracker.Tracker(self)
        self.thread_batch = exp.Batch.Batch(self, self.wait_batch)
        self.thread_terminal = exp.Terminal.Terminal(self, self.wait_terminal)
        self.thread_liveapd = exp.APD.LiveAPD(self, self.wait_liveapd)
        self.thread_seqapd = exp.APD.SeqAPD(self, self.wait_seqapd)
        self.thread_satcurve = exp.SatCurve.SatCurve(self, self.wait_satcurve)
        self.thread_picoharp = exp.PicoHarp.PicoHarp(self, self.wait_picoharp)

        '''GUI CONTROLS'''
        # Define yellow-hot colormap
        # colors = np.array([[0, 0, 0, 1], [1, 0, 0, 1], [1, 1, 0, 1.0]])
        colors = np.array([[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255]])
        cm = pg.ColorMap([0, 0.5, 1], colors)

        '''CONFOCAL'''
        self.btn_confocal_mode_xy.setChecked(True)
        self.btn_confocal_mode = QtGui.QButtonGroup()
        self.btn_confocal_mode.addButton(self.btn_confocal_mode_xy, 0)
        self.btn_confocal_mode.addButton(self.btn_confocal_mode_xz, 1)
        self.btn_confocal_mode.addButton(self.btn_confocal_mode_yz, 2)
        self.btn_confocal_mode.buttonClicked[int].connect(self.confocal_mode_select)
        self.btn_confocal_start.clicked.connect(self.confocal_start)
        self.btn_confocal_live.toggled[bool].connect(self.confocal_live)
        self.int_confocal_live_avg.valueChanged.connect(self.confocal_live_set_avg)
        self.btn_confocal_stop.clicked.connect(self.confocal_stop)
        self.btn_confocal_save.clicked.connect(functools.partial(self.thread_confocal.save, ext=True))
        self.chkbx_confocal_autolevel.setChecked(True)
        self.chkbx_confocal_autolevel.stateChanged.connect(self.confocal_set_autolevel)

        self.table_confocalZ.setColumnCount(3)
        self.table_confocalZ.setHorizontalHeaderLabels(['x', 'y', 'z'])
        self.btn_confocalZ_add.clicked.connect(self.confocal_confocalZ_add)
        self.btn_confocalZ_del.clicked.connect(self.confocal_confocalZ_del)
        self.btn_confocalZ_calc.clicked.connect(self.thread_confocal.plane_fit)

        self.confocal_mode = 0
        self.confocal_rngx = []
        self.confocal_rngy = []
        self.confocal_rngz = []
        self.confocal_pl = np.array([])

        # Create PyQtGraph plots and histogram for confocal scans
        for name in ['confocal', 'map']:
            setattr(self, 'vb_%s' % name, pg.ViewBox())
            setattr(self, 'plt_%s' % name, pg.PlotItem(viewBox=getattr(self, 'vb_%s' % name)))
            setattr(self, 'qtimg_%s' % name, pg.ImageItem())
            getattr(self, 'vb_%s' % name).addItem(getattr(self, 'qtimg_%s' % name))

        '''CONFOCAL PLOTS'''
        self.glw_confocal = pg.GraphicsLayoutWidget()
        self.glw_confocal.addItem(self.plt_confocal, 0, 0)
        self.hlw_confocal = mainexp_widgets.CustomLUTWidget(image=self.qtimg_confocal)
        self.hlw_confocal.gradient.setColorMap(cm)

        self.grid_confocal.addWidget(self.glw_confocal, 0, 0)
        self.grid_confocal.addWidget(self.hlw_confocal, 0, 1)

        self.int_confocal_z_numdivs.valueChanged.connect(self.confocal_zstack_enable)
        self.confocal_zstack_enable(self.int_confocal_z_numdivs.value())

        '''MAP PLOTS'''
        self.glw_map = pg.GraphicsLayoutWidget()
        self.glw_map.addItem(self.plt_map, 0, 0)
        self.hlw_map = mainexp_widgets.CustomLUTWidget(image=self.qtimg_map)
        self.hlw_map.gradient.setColorMap(cm)

        self.grid_map.addWidget(self.glw_map, 0, 0)
        self.grid_map.addWidget(self.hlw_map, 0, 1)

        self.map_vLine = pg.InfiniteLine(angle=90, movable=False, pen=(0, 150, 100))
        self.map_hLine = pg.InfiniteLine(angle=0, movable=False, pen=(0, 150, 100))
        self.map_vLine.hide()
        self.map_hLine.hide()

        self.map_cursor = pg.ScatterPlotItem(pen=pg.mkPen('w', width=2), brush=None, symbol='o', size=7)
        self.map_cursor.setData([0], [0])
        self.map_nvlist = pg.ScatterPlotItem(pen=pg.mkPen((0, 150, 100), width=2), brush=None, symbol='o', size=7)
        self.map_nvlist.setData([], [])
        self.map_nvlabels = [] # for storing NV numbers

        self.plt_map.addItem(self.map_nvlist)
        self.plt_map.addItem(self.map_cursor)
        self.plt_map.addItem(self.map_vLine, ignoreBounds=True)
        self.plt_map.addItem(self.map_hLine, ignoreBounds=True)

        self.btn_map_load.clicked.connect(self.map_load)
        self.btn_map_copy.clicked.connect(self.map_copy)
        self.btn_map_select.clicked.connect(self.map_select)

        self.map_data = np.array([])
        self.map_ax_xmin = 0
        self.map_ax_xmax = 0
        self.map_ax_ymin = 0
        self.map_ax_ymax = 0

        '''TRACKER CONTROL'''
        self.btn_tracker_run.clicked.connect(functools.partial(self.tracker_start,
                                                               numtrack=1, finished_func=None))
        self.btn_tracker_drive.clicked.connect(self.tracker_drive)
        self.btn_tracker_home.clicked.connect(self.tracker_home)
        self.btn_tracker_clear.clicked.connect(self.tracker_clear)
        self.btn_tracker_driveup.clicked.connect(self.tracker_step)
        self.btn_tracker_drivedown.clicked.connect(self.tracker_step)
        self.btn_tracker_driveleft.clicked.connect(self.tracker_step)
        self.btn_tracker_driveright.clicked.connect(self.tracker_step)
        self.btn_tracker_drivezdown.clicked.connect(self.tracker_step)
        self.btn_tracker_drivezup.clicked.connect(self.tracker_step)

        self.btn_tracker_auto.clicked.connect(self.tracker_auto_enable)
        self.tracker_timer = QtCore.QTimer()
        self.tracker_timer.timeout.connect(self.tracker_auto_start)

        self.plt_tracker_x = self.glw_tracker.addPlot(0, 0)
        self.plt_tracker_x.setLabels(left='PL (kcps)', bottom='x (&mu;m)')
        self.plt_tracker_y = self.glw_tracker.addPlot(0, 1)
        self.plt_tracker_y.setLabels(left='PL (kcps)', bottom='y (&mu;m)')
        self.plt_tracker_z = self.glw_tracker.addPlot(0, 2)
        self.plt_tracker_z.setLabels(left='PL (kcps)', bottom='z (&mu;m)')

        nextrow = 1
        nextcol = 0

        self.tracker_laser_list = self.tlblist.copy()
        if hasattr(self, 'wavemeter') and hasattr(self, 'ctlfreq'):
            if self.wavemeter.isconnected:
                self.tracker_laser_list.append('ctlfreq')

        for laser_name in self.tracker_laser_list:
            setattr(self, 'plt_tracker_%s' % laser_name, self.glw_tracker.addPlot(nextrow, nextcol))
            plt = getattr(self, 'plt_tracker_%s' % laser_name)
            if laser_name != 'ctlfreq':
                plt.setLabels(left='PL (kcps)', bottom=laser_name + ' (V)')
            else:
                plt.setLabels(left='PL (kcps)', bottom=laser_name + ' (GHz)')
            setattr(self, 'trace_tracker_%s_xvals' % laser_name, [])
            setattr(self, 'trace_tracker_%s_yvals' % laser_name, [])
            setattr(self, 'trace_tracker_%s_yfit' % laser_name, [])
            setattr(self, 'curve_tracker_%s' % laser_name, plt.plot([], [], pen='r'))
            setattr(self, 'curve_tracker_%s_fit' % laser_name, plt.plot([], [], pen='b'))
            setattr(self, 'tracker_%s' % laser_name, [])
            label = QtWidgets.QLabel(laser_name + ' range (GHz)')
            dbl = QtWidgets.QDoubleSpinBox()
            dbl.setRange(0.0, 50.0)
            dbl.setSingleStep(0.1)
            setattr(self, 'label_tracker_%s_rng' % laser_name, label)
            setattr(self, 'dbl_tracker_%s_rng' % laser_name, dbl)
            ctrl_row = self.widget_tracker.grid_tracker_freq.rowCount()
            self.widget_tracker.grid_tracker_freq.addWidget(label, ctrl_row, 0)
            self.widget_tracker.grid_tracker_freq.addWidget(dbl, ctrl_row, 1)

            nextcol += 1
            if nextcol > 2:
                nextrow += 1
                nextcol = 0

        # Hide the right panel if not in use
        if not self.widget_tracker.grid_tracker_freq.count():
            self.widget_tracker.setFixedWidth(200)
            self.widget_tracker.setFixedHeight(310)

        self.plt_tracker_xpos = self.glw_tracker.addPlot(nextrow + 1, 0, colspan=3,
                                                         axisItems={'bottom': mainexp_widgets.TimeAxisItem(orientation='bottom')})
        self.plt_tracker_xpos.setLabels(left='x (&mu;m)')
        self.plt_tracker_ypos = self.glw_tracker.addPlot(nextrow + 2, 0, colspan=3,
                                                         axisItems={'bottom': mainexp_widgets.TimeAxisItem(orientation='bottom')})
        self.plt_tracker_ypos.setLabels(left='y (&mu;m)')
        self.plt_tracker_zpos = self.glw_tracker.addPlot(nextrow + 3, 0, colspan=3,
                                                         axisItems={'bottom': mainexp_widgets.TimeAxisItem(orientation='bottom')})
        self.plt_tracker_zpos.setLabels(left='z (&mu;m)')

        self.plt_tracker_p532 = self.glw_tracker.addPlot(nextrow + 4, 0, colspan=3,
                                                         axisItems={'bottom': mainexp_widgets.TimeAxisItem(orientation='bottom')})
        self.plt_tracker_p532.setLabels(left='Laser Power (mW)')
        self.plt_tracker_pl = self.glw_tracker.addPlot(nextrow + 5, 0, colspan=3,
                                                       axisItems={'bottom': mainexp_widgets.TimeAxisItem(orientation='bottom')})
        self.plt_tracker_pl.setLabels(left='PL (kcps)', bottom='time')

        self.curve_tracker_data = [self.plt_tracker_x.plot([], [], pen='r'),
                                   self.plt_tracker_y.plot([], [], pen='r'),
                                   self.plt_tracker_z.plot([], [], pen='r')]
        self.curve_tracker_fit = [self.plt_tracker_x.plot([], [], pen='b'),
                                  self.plt_tracker_y.plot([], [], pen='b'),
                                  self.plt_tracker_z.plot([], [], pen='b')]

        self.trace_tracker_xvals = [[], [], []]
        self.trace_tracker_yvals = [[], [], []]
        self.trace_tracker_yfit = [[], [], []]

        self.curve_tracker_xpos = self.plt_tracker_xpos.plot([], [], pen='r')
        self.curve_tracker_ypos = self.plt_tracker_ypos.plot([], [], pen='r')
        self.curve_tracker_zpos = self.plt_tracker_zpos.plot([], [], pen='r')
        self.curve_tracker_p532 = self.plt_tracker_p532.plot([], [], pen='r')
        self.curve_tracker_pl = self.plt_tracker_pl.plot([], [], pen='r')

        self.tracker_xpos = []
        self.tracker_ypos = []
        self.tracker_zpos = []
        self.tracker_p532 = []
        self.tracker_pl = []
        self.tracker_t = []

        '''EXPERIMENT PARAMETERS'''
        # Tree view
        self.tree_exp_params.setModel(QtGui.QStandardItemModel())
        self.tree_exp_params.setAlternatingRowColors(True)
        self.tree_exp_params.setSortingEnabled(True)
        self.tree_exp_params.setHeaderHidden(False)
        self.tree_exp_params.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.tree_exp_params.model().itemChanged.connect(self.exp_params_paramsChanged)
        self.label_exp_params.setText('')
        self.label_exp_params.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        '''SWEEP CONTROL'''
        self.btn_exp_start.clicked.connect(self.sweep_start)
        self.btn_exp_stop.clicked.connect(self.sweep_stop)
        self.btn_exp_save.clicked.connect(functools.partial(self.thread_sweep.save_exp, ext=True))

        self.var1_name.currentIndexChanged.connect(self.sweep_set_var1)
        self.var1_start_unit.addItems(['G', 'M', 'k', '-', 'm', 'u', 'n'])
        self.var1_start_unit.setCurrentIndex(self.var1_start_unit.findText('-'))
        self.var1_stop_unit.addItems(['G', 'M', 'k', '-', 'm', 'u', 'n'])
        self.var1_stop_unit.setCurrentIndex(self.var1_stop_unit.findText('-'))

        self.var2_name.currentIndexChanged.connect(self.sweep_set_var2)
        self.var2_start_unit.addItems(['G', 'M', 'k', '-', 'm', 'u', 'n'])
        self.var2_start_unit.setCurrentIndex(self.var1_start_unit.findText('-'))
        self.var2_stop_unit.addItems(['G', 'M', 'k', '-', 'm', 'u', 'n'])
        self.var2_stop_unit.setCurrentIndex(self.var1_stop_unit.findText('-'))

        self.btn_swap_var.clicked.connect(self.sweep_swap_var)
        self.chkbx_2dexp.stateChanged.connect(self.chkbx_2dexp_meander.setVisible)

        # For pausing sweep while setting manual variable
        self.label_exp_pause.setVisible(False)
        self.btn_exp_pause.setVisible(False)
        self.btn_exp_pause.clicked.connect(self.exp_params_setval_manual_clicked)

        # initialize empty array for storing counter data
        self.wmFreq = []
        self.esrtrace_pl = []
        self.esrtrace_sig = []
        self.esrtrace_ref = []
        self.esr_rngx = []
        self.esr_rngy = []
        self.esr_fitx = []
        self.esr_fity = []

        self.esrtrace_pl2 = []
        self.esrtrace_sig2 = []
        self.esrtrace_ref2 = []

        self.esrtrace_newctr = []

        # Initialize canvas for plots and figures
        self.glw_main = pg.GraphicsLayoutWidget()
        self.hlw_main = mainexp_widgets.CustomLUTWidget()
        self.glw_inv = pg.GraphicsLayoutWidget()
        self.hlw_inv = mainexp_widgets.CustomLUTWidget()
        self.glw_raw = pg.GraphicsLayoutWidget()
        self.hlw_raw = mainexp_widgets.CustomLUTWidget()

        self.hlw_main.gradient.setColorMap(cm)
        self.hlw_inv.gradient.setColorMap(cm)
        self.hlw_raw.gradient.setColorMap(cm)

        # 1D plots
        self.plt1d_pl = pg.PlotItem()
        self.plt1d_raw = pg.PlotItem()

        self.curve_pl = self.plt1d_pl.plot([], [], pen='r')
        self.curve_pl_fit = self.plt1d_pl.plot([], [], pen='b')
        self.curve_ref = self.plt1d_raw.plot([], [])
        self.curve_sig = self.plt1d_raw.plot([], [], pen='r')

        self.curve_pl2 = self.plt1d_pl.plot([], [], pen=pg.mkPen(color=(255, 196, 196)))
        self.curve_sig2 = self.plt1d_raw.plot([], [], pen=pg.mkPen(color=(255, 196, 196)))
        self.curve_ref2 = self.plt1d_raw.plot([], [], pen=pg.mkPen(color=(196, 196, 255)))

        colors = ['r', 'b', 'k', 'g', 'c', 'm', 'y']
        for ch in range(7):
            setattr(self, 'curve_ple_ref_%d' % ch, self.plt1d_raw.plot([], [], pen=colors[ch]))
            setattr(self, 'curve_newctr_%d' % ch, self.plt1d_raw.plot([], [], pen=colors[ch]))

        # 2D plots
        self.plt2d_pl = None
        self.plt2d_sig = None
        self.plt2d_ref = None
        self.plt2d_pl2 = None
        self.plt2d_sig2 = None
        self.plt2d_ref2 = None
        
        for name in ['pl', 'sig', 'ref', 'pl2', 'sig2', 'ref2']:
            setattr(self, 'vb_%s' % name, pg.ViewBox())
            setattr(self, 'plt2d_%s' % name, pg.PlotItem(viewBox=getattr(self, 'vb_%s' % name)))
            setattr(self, 'qtimg_%s' % name, pg.ImageItem())
            getattr(self, 'vb_%s' % name).addItem(getattr(self, 'qtimg_%s' % name))
            getattr(self, 'vb_%s' % name).setContentsMargins(0.01, 0.01, 0.01, 0.01)

        '''SPECTROMETER'''
        self.btn_spectrometer_acquire.clicked.connect(self.spectrometer_start)
        self.btn_spectrometer_connect.toggled.connect(self.spectrometer_connect)
        self.btn_spectrometer_live.toggled.connect(self.spectrometer_live)
        self.btn_spectrometer_save.clicked.connect(functools.partial(self.thread_spectrometer.save, ext=True))
        self.dbl_spectrometer_centerwavelength.valueChanged.connect(self.thread_spectrometer.gotolambda)
        self.chkbx_spectrometer_xbin.setChecked(False)
        self.chkbx_spectrometer_ybin.setChecked(True)

        self.glw_spectrometer = pg.GraphicsLayoutWidget()
        self.plt_spectrometer = self.glw_spectrometer.addPlot()
        self.plt_spectrometer.setLabels(title=None, left='Intensity (a.u.)', bottom='Wavelength (nm)')
        self.curve_spectrometer = self.plt_spectrometer.plot([], [], pen='k')
        self.grid_spectrometer.addWidget(self.glw_spectrometer, 0, 0)
        self.trace_spectrometer = np.array([])
        self.spectrometer_initialized = False

        '''TERMINAL CONTROL'''
        self.linein_terminal_cmd.clear()
        self.linein_terminal_cmd.returnPressed.connect(self.thread_terminal.submit_cmd)
        self.btn_terminal_cmdlog_clear.clicked.connect(self.terminal_clear_cmdlog)
        self.btn_terminal_cmdqueue_clear.clicked.connect(self.terminal_clear_cmdqueue)
        self.btn_terminal_cmdqueue_del.clicked.connect(self.terminal_del_cmdqueue)
        self.chkbx_terminal_cmdqueue.stateChanged.connect(self.terminal_enable_cmdqueue)
        self.chkbx_terminal_cmdqueue.setChecked(True)
        self.chkbx_terminal_thd.setChecked(True)

        '''LIVE APD'''
        self.btn_liveapd_clear.clicked.connect(self.liveapd_clear)
        self.btn_liveapd_start.clicked.connect(self.liveapd_start)
        self.btn_liveapd_stop.clicked.connect(self.liveapd_stop)
        self.btn_liveapd_stop.setEnabled(False)
        self.btn_liveapd_save.clicked.connect(self.thread_liveapd.save)
        self.btn_liveapd_single.clicked.connect(self.thread_liveapd.update)

        self.plt_liveapd = self.glw_liveapd.addPlot()
        self.plt_liveapd.setLabels(title='Live APD', left='PL (Hz)', bottom='Time (s)')
        self.curve_liveapd = self.plt_liveapd.plot(pen='r')
        self.liveapd_pl = np.array([])
        self.liveapd_t = np.array([])

        '''SEQ APD'''
        self.btn_seqapd_start.clicked.connect(self.seqapd_start)
        self.btn_seqapd_clear.clicked.connect(self.seqapd_clear)
        self.btn_seqapd_stop.clicked.connect(self.seqapd_stop)
        self.btn_seqapd_stop.setEnabled(False)
        self.btn_seqapd_save.clicked.connect(self.thread_seqapd.save)

        self.plt_seqapd = self.glw_seqapd.addPlot()
        self.plt_seqapd.setLabels(title='Seq APD', left='PL (counts per interval)', bottom='Time (s)')
        self.curve_seqapd = self.plt_seqapd.plot(pen='r')
        self.seqapd_pl = np.array([])
        self.seqapd_t = np.array([])

        '''SATURATION CURVE'''
        self.btn_satcurve_meas.clicked.connect(self.thread_satcurve.meas)
        self.btn_satcurve_clear.clicked.connect(self.thread_satcurve.clear)
        self.btn_satcurve_fit.clicked.connect(self.thread_satcurve.fit)
        self.btn_satcurve_save.clicked.connect(self.thread_satcurve.save)
        # Add VOA control for satcurve
        self.cbox_satcurve_voa.addItems([item for item in self.exp_params['Instrument'].keys() if 'voa' in item])
        # Add power meter selection
        self.cbox_satcurve_pm.addItems(sorted([item for item in self.__dict__.keys() if item.startswith('pm100d') and 'gui' not in item]))
        self.btn_satcurve_voa_start.clicked.connect(self.satcurve_start)
        self.btn_satcurve_voa_stop.clicked.connect(self.satcurve_stop)
        self.satcurve_voa_cancel = True

        # self.fit_satcurve = fit.fit_satcurve()
        self.plt_satcurve = self.glw_satcurve.addPlot()
        self.plt_satcurve.setLabels(title='Saturation Curve', left=('PL', 'cps'), bottom='Laser Power (mW)')
        self.satcurve_pl = np.array([])
        self.satcurve_p = np.array([])
        self.satcurve_pl_fit = np.array([])
        self.satcurve_p_fit = np.array([])
        self.curve_satcurve = self.plt_satcurve.plot(pen='r')
        self.curve_satcurve_fit = self.plt_satcurve.plot(pen='b')

        '''BATCH CONTROL'''
        self.table_nvlist.setColumnCount(4)
        self.table_nvlist.setHorizontalHeaderLabels(['x', 'y', 'z', 'notes'])
        self.label_nvlist_numtrack.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), 'gui', 'icons', 'target.png')))
        self.btn_nvlist_clear.clicked.connect(self.nvlist_clear)
        self.btn_nvlist_add.toggled.connect(self.nvlist_select)
        self.shortcut_nvlist_add = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+A'), self)
        self.shortcut_nvlist_add.activated.connect(functools.partial(self.btn_nvlist_add.setChecked, True))
        self.btn_nvlist_del.clicked.connect(self.nvlist_del)
        self.btn_nvlist_save.clicked.connect(self.nvlist_save)
        self.btn_nvlist_load.clicked.connect(self.nvlist_load)
        self.btn_nvlist_shift.toggled.connect(self.nvlist_shift)
        self.btn_nvlist_get_tracker_pos.clicked.connect(self.nvlist_shift_manual)
        self.btn_nvlist_drive.clicked.connect(self.nvlist_drive)
        self.btn_nvlist_start.clicked.connect(self.thread_batch.start)
        self.btn_nvlist_stop.clicked.connect(self.thread_batch.stop)
        self.btn_nvlist_scripts_add.clicked.connect(self.nvlist_scripts_add)
        self.btn_nvlist_scripts_del.clicked.connect(self.nvlist_scripts_del)
        self.btn_nvlist_scripts_clear.clicked.connect(self.nvlist_scripts_clear)
        self.btn_nvlist_calscripts_add.clicked.connect(self.nvlist_calscripts_add)
        self.btn_nvlist_calscripts_del.clicked.connect(self.nvlist_calscripts_del)
        self.btn_nvlist_calscripts_clear.clicked.connect(self.nvlist_calscripts_clear)
        self.list_nvlist_scripts.itemDoubleClicked[QtWidgets.QListWidgetItem].connect(self.nvlist_script_open)
        self.list_nvlist_calscripts.itemDoubleClicked[QtWidgets.QListWidgetItem].connect(self.nvlist_script_open)
        self.nvlist_number = 0 # used to save nvlist to a new file after clearing and loading the whole list
        self.btn_nvlist_auto_make_batch.clicked.connect(self.nvlist_auto_make_batch)


        '''PICOHARP'''
        self.picoharp_xvals = np.array([])
        self.picoharp_yvals = np.array([])
        self.picoharp_xvals_disp = np.array([])  # Sub-sampled data of nicer display
        self.picoharp_yvals_disp = np.array([])  # Sub-sampled data of nicer display
        self.plt_picoharp = self.glw_picoharp.addPlot()
        self.plt_picoharp.setLabels(title='Picoharp Histogram', left=('Counts', 'cnts'), bottom=('Time', 's'))
        self.plt_picoharp.setMouseEnabled(x=False, y=True)
        self.plt_picoharp.enableAutoRange(x=False, y=True)
        self.chkbx_picoharp_disp_autoscale.toggled.connect(self.picoharp_disp_autoscale)
        self.chkbx_picoharp_disp_autoscale.setChecked(True)
        self.curve_picoharp = self.plt_picoharp.plot(self.picoharp_xvals, self.picoharp_yvals, pen='r')
        self.btn_picoharp_connect.toggled.connect(self.thread_picoharp.dev_connect)
        self.btn_picoharp_start.clicked.connect(self.picoharp_start)
        self.btn_picoharp_stop.clicked.connect(self.picoharp_stop)
        self.btn_picoharp_update_settings.clicked.connect(self.thread_picoharp.update_settings)
        self.btn_picoharp_save.clicked.connect(functools.partial(self.thread_picoharp.save, ext=True))
        self.cbox_picoharp_mode.addItems(['normal', 'pb_esr', 'pb_custom'])
        self.dbl_picoharp_disp_xmin.valueChanged.connect(self.picoharp_disp_scale)
        self.dbl_picoharp_disp_xmax.valueChanged.connect(self.picoharp_disp_scale)

        '''REMOTE TESTING'''
        self.remoteControl = remotecontrol.ControlService
        if self.remote_flag:
            print('I entered the correct region!')
            t = ThreadedServer(self.remoteControl(self), port=18861)
            th1 = threading.Thread(target=t.start)
            th1.start()
            # t.start()
            print('I finished with my server stuff')

        '''SHORTCUTS'''
        # Set up shortcut buttons
        for i in range(8):
            getattr(self, 'btn_shortcuts_%d' % (i+1)).clicked.connect(self.shortcut_run)
            getattr(self, 'linein_shortcuts_%d' % (i+1)).editingFinished.connect(self.shortcut_update)

        file_nvlist = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'table_nvlist.csv'))
        if os.path.isfile(file_nvlist):
            file_utils.csv2table(self.table_nvlist, file_nvlist)
            self.nvlist_update()

        # default list of parameters to display - todo: move this to some yaml file
        self.default_params_disp = {'CW': ['mw1freq', 'mw1pow', 'Br', 'Btheta', 'Bphi'],
                                    'CW2': ['mw2freq', 'mw2pow', 'Br', 'Btheta', 'Bphi'],
                                    'odmr': ['mw1freq', 'mw1pow', 'Br', 'Btheta', 'Bphi', 'coilMaxVolt', 'coilCurrent', 'coilVolt'],
                                    'odmr2': ['mw2freq', 'mw2pow', 'Br', 'Btheta', 'Bphi', 'coilMaxVolt', 'coilCurrent', 'coilVolt'],
                                    'rabi': ['mw1freq', 'mw1pow', 'pulsewidth'],
                                    'rabi2': ['mw2freq', 'mw2pow', 'pulsewidth'],
                                    't1': ['mw1freq', 'pulsewidth', 'tau'],
                                    'DQ_t1': ['mw1freq', 'mw2freq', 'pulsewidth', 'tau'],
                                    'SQ_t1': ['mw1freq', 'pulsewidth', 'tau'],
                                    'awg_rabi': ['mw1freq', 'mw1pow', 'pulsewidth', 'vi', 'vq'],
                                    'awg_cpmg': ['mw1freq', 'r180pw', 'r90pw', 'tau', 'n'],
                                    'awg_deer': ['mw1freq', 'mw1pow', 'mw2freq', 'mw2pow', 'deerpulsewidth', 'y90pw', 'tau'],
                                    'awg_deer_cpmg': ['mw1freq', 'mw1pow', 'mw2freq', 'mw2pow', 'r180pw', 'r90pw', 'tau', 'n'],
                                    'awg_deer_xy4': ['mw1freq', 'mw1pow', 'mw2freq', 'mw2pow', 'x180pw', 'r90pw', 'tau', 'k'],
                                    'awg_deer_xy8': ['mw1freq', 'mw1pow', 'mw2freq', 'mw2pow', 'x180pw', 'r90pw', 'tau', 'k'],
                                    'awg_xy4': ['mw1freq', 'k', 'r90pw', 'tau'],
                                    'awg_xy8': ['mw1freq', 'k', 'r90pw', 'tau'],
                                    'awg_xy8_interp': ['mw1freq', 'k', 'r90pw', 'tau']}

        self.btn_exp_fit.clicked.connect(functools.partial(self.thread_sweep.dofit, ext=True))

        '''SET UP ALL GUI'''
        # Set up ranges and step limits in the gui fields
        if os.path.isfile(os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'guifield_settings.yaml'))):
            gfspath = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'guifield_settings.yaml'))
        else:
            gfspath = 'guifield_settings.yaml'

        if os.path.isfile(gfspath):
            gfs = file_utils.yaml2dict(gfspath)
            self.esrguisettings = gfs.pop('esr', None) # return the esr key or None
            for field in gfs.keys():
                try:
                    target = getattr(self, field)
                    for setting in gfs[field].keys():
                        if type(gfs[field][setting]) is list:
                            getattr(target, setting)(*gfs[field][setting])
                        else:
                            getattr(target, setting)(gfs[field][setting])
                except AttributeError:
                    print('Field %s does not exist.' % field)
            print('loading guifield_settings.yaml')

        processEvents()

        # Load previous GUI settings
        if os.path.isfile(os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'guisettings.config'))):
            print('loading guisettings.config')
            gui_settings = file_utils.load_config(os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'guisettings.config')))
            self.import_gui_settings(gui_settings)
        elif os.path.isfile(os.path.join(os.getcwd(), 'guisettings.config')):
            warnings.warn('loading guisettings.config from exp_code. this may be bogus')
            gui_settings = file_utils.load_config(os.path.join(os.getcwd(), 'guisettings.config'))
            self.import_gui_settings(gui_settings)

        self.dbl_confocal_stage_x.setValue(self.exp_params['Manual']['stage_x'])
        self.dbl_confocal_stage_y.setValue(self.exp_params['Manual']['stage_y'])

        self.dbl_confocal_stage_x.valueChanged.connect(functools.partial(self.task_handler.setval, 'stage_x'))
        self.dbl_confocal_stage_y.valueChanged.connect(functools.partial(self.task_handler.setval, 'stage_y'))

        # Fill options for experiments
        self.cbox_exp_name.clear()
        self.cbox_exp_name.addItems(self.pb.list_functions())
        self.cbox_exp_name.currentIndexChanged.connect(self.sweep_exp_update)

        # Fill options for fit types
        self.cbox_fittype.addItem('')
        self.cbox_fittype.addItems(list(sorted(self.thread_sweep.fitter.fit_functions.keys())))

        self.update_params_table()
        self.update_inst_stat()

        self.pb_set_tracker_laser()

        '''MISCELLANEOUS'''
        self.btn_debug.clicked.connect(self.debug)
        self.wavenum = file_utils.getwavenum() + 1

        self.pixmap_sweep_graph = None
        self.pixmap_sweep_fig = None
        self.pixmap_confocal_graph = None
        self.pixmap_confocal_fig = None
        self.pixmap_spectrometer_graph = None
        self.pixmap_spectrometer_fig = None
        self.pixmap_picoharp_graph = None
        self.pixmap_liveapd_graph = None
        self.pixmap_seqapd_graph = None
        self.pixmap_satcurve_graph = None

        for i in range(8):
            text = getattr(self, 'linein_shortcuts_%d' % (i+1)).text()
            getattr(self, 'btn_shortcuts_%d' % (i+1)).setVisible(bool(text))
            if text:
                getattr(self, 'btn_shortcuts_%d' % (i+1)).setText(text)

        self.set_gui_defaults()
        processEvents()

        # Build a dictionary of functions that can be called from scripts
        method_list = [func for func in dir(self.task_handler)
                       if callable(getattr(self.task_handler, func)) and
                       not func.startswith("__")]

        method_dict = {'mainexp': self, 'pb': self.pb}
        for m in method_list:
            method_dict[m] = getattr(self.task_handler, m)

        script = os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts', 'mainexp_init.py'))
        if os.path.isfile(script):
            self.log('Executing mainexp_init.py')
            try:
                exec(open(script).read(), method_dict)
            except:
                self.log('YOUR SCRIPT HAS AN ERROR! mainexp_init.py')
            self.log('Finished executing mainexp_init.py')

    def shortcut_update(self):
        linein = self.sender()

        num = linein.objectName().split('shortcuts_')[-1]
        text = linein.text()
        getattr(self, 'btn_shortcuts_%s' % num).setVisible(bool(text))

        if text:
            getattr(self, 'btn_shortcuts_%s' % num).setText(text)

    def shortcut_run(self):
        num = self.sender().objectName().split('shortcuts_')[-1]

        cmd = getattr(self, 'linein_shortcuts_command_%s' % num).text()

        if cmd:
            self.linein_terminal_cmd.setText(cmd)
            self.thread_terminal.submit_cmd()

    def import_gui_settings(self, data):
        # refill the linein, double, and integer fields in the gui
        for attr in self.__dict__.keys():
            if 'linein' in attr:
                if attr in data['linein'].keys():
                    getattr(self, attr).setText(data['linein'][attr])
            if 'dbl_' in attr:
                if attr in data['dbl'].keys():
                    getattr(self, attr).setValue(data['dbl'][attr])
            if 'int_' in attr:
                if attr in data['int'].keys():
                    getattr(self, attr).setValue(data['int'][attr])
            if 'map_ax' in attr:
                if attr in data['map_ax'].keys():
                    setattr(self, attr, data['map_ax'][attr])

        if 'cmdlog' in data.keys():
            self.label_terminal_cmdlog.setPlainText(data['cmdlog'])

        try:
            self.map_data = data['map']
            self.map_updateplot()
        except KeyError:
            print('no confocal map loaded')
            pass

    def export_gui_settings(self):
        outdata = {'linein': {}, 'dbl': {}, 'int': {}, 'img': [], 'map': [], 'map_ax': {}}
        if len(self.confocal_pl) > 0:
            outdata['img'] = self.confocal_pl[:, :, 0]
        if len(self.map_data) > 0:
            outdata['map'] = self.map_data
        for attr in self.__dict__.keys():
            if 'linein' in attr:
                outdata['linein'][attr] = getattr(self, attr).text()
            elif 'dbl_' in attr:
                outdata['dbl'][attr] = getattr(self, attr).value()
            elif 'int_' in attr:
                outdata['int'][attr] = getattr(self, attr).value()
            elif 'map_ax_' in attr:
                outdata['map_ax'][attr] = getattr(self, attr)

        outdata['cmdlog'] = self.label_terminal_cmdlog.toPlainText()

        try:
            file_utils.save_config(outdata, path=os.path.expanduser(os.path.join('~', 'Documents', 'exp_config')))
        except PermissionError as err:
            # TODO: why does this intermittently fail on this line:
            #   pickle.dump(configsettings, open(fullpath, 'wb'))
            # with this error?
            # PermissionError: [Errno 13] Permission denied: 'C:\\Users\\NV Confocal\\Documents\\exp_config\\guisettings.config'
            print(err)
            print(traceback.format_exc())
            print('warning: skipping PermissionError when saving experiment config with file_utils.saveconfig()')

        try:
            self.export_sweep_settings(os.path.expanduser(os.path.join('~', 'Documents', 'exp_config',
                                                                       'sweep_params','manual.yaml')),
                                       manual=True)
        except PermissionError as err:
            # TODO: why does this intermittently fail on this line:
            #   file_utils.dict2yaml(sweep_params, filename)
            # with this error?
            # PermissionError: [Errno 13] Permission denied: 'C:\\Users\\NV Confocal\\Documents\\exp_config\\sweep_params\\manual.yaml'
            print(err)
            print(traceback.format_exc())
            print('warning: skipping PermissionError when saving experiment config with file_utils.dict2yaml()')

        file_utils.table2csv(self.table_nvlist, os.path.expanduser(os.path.join('~', 'Documents', 'exp_config',
                                                                                'table_nvlist.csv')))

    def import_sweep_settings(self):
        # check if sweep_params\pulsename.yaml exist. If it does, iterate through the items and call setval
        exp_name = self.cbox_exp_name.currentText()

        sweep_params_file = os.path.expanduser(
            os.path.join('~', 'Documents', 'exp_config', 'sweep_params', exp_name + '.yaml'))

        if os.path.isfile(sweep_params_file):
            sweep_params = file_utils.yaml2dict(sweep_params_file)
            for paramtype in sweep_params.keys():
                if paramtype in ['Pulse']:
                    for name in sweep_params[paramtype].keys():
                        val = sweep_params[paramtype][name]
                        if name in self.exp_params[paramtype].keys() and self.exp_params[paramtype][name] != val:
                            self.exp_params_setval(name, val, log=False)
                            # call pb function directly to avoid delays in each settings
                            self.pb.set_param(name, val)

            if 'sweep_var' in sweep_params.keys():
                self.sweep_var_defaults = sweep_params['sweep_var']
            else:
                self.sweep_var_defaults = {}
            return sweep_params
        else:
            self.sweep_var_defaults = {}
            return {}

    # Export sweep settings into a yaml file
    # - used for exporting metadata when filename is specified
    # - used for exporting default sweep_params otherwise
    def export_sweep_settings(self, filename=None, manual=False, sweep_var=False):
        # filename - for specifying location to save (e.g. for saving actual metadata)
        # manual - for saving manual variable
        # sweep_var - for saving default sweep variables for each experiments
        exp_name = self.cbox_exp_name.currentText()

        if filename is None:
            filename = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'sweep_params', exp_name + '.yaml'))

        if not manual:
            sweep_params = dict(
                (k, v) for k, v in self.exp_params.items())  # cannot just assign a new dict ref
            sweep_params['Sweep'] = {'var1_name': self.var1_name.currentText(),
                                     'var1_start': self.var1_start.value(),
                                     'var1_start_unit': self.var1_stop_unit.currentText(),
                                     'var1_stop': self.var1_stop.value(),
                                     'var1_stop_unit': self.var1_stop_unit.currentText(),
                                     'var1_numdivs': self.var1_numdivs.value(),
                                     'var1_delay': self.var1_delay.value(),
                                     'var2_name': self.var2_name.currentText(),
                                     'var2_start': self.var2_start.value(),
                                     'var2_start_unit': self.var2_start_unit.currentText(),
                                     'var2_stop': self.var2_stop.value(),
                                     'var2_stop_unit': self.var2_stop_unit.currentText(),
                                     'var2_numdivs': self.var2_numdivs.value(),
                                     'var2_delay': self.var2_delay.value(),
                                     'chxbx_2desr': self.chkbx_2dexp.isChecked()}

            if sweep_var:
                self.sweep_var_defaults[self.var1_name.currentText()] = {
                    'start': self.var1_start.value(),
                    'start_unit': self.var1_stop_unit.currentText(),
                    'stop': self.var1_stop.value(),
                    'stop_unit': self.var1_stop_unit.currentText(),
                    'numdivs': self.var1_numdivs.value(),
                    'delay': self.var1_delay.value()}
                self.sweep_var_defaults[self.var2_name.currentText()] = {
                    'start': self.var2_start.value(),
                    'start_unit': self.var2_stop_unit.currentText(),
                    'stop': self.var2_stop.value(),
                    'stop_unit': self.var2_stop_unit.currentText(),
                    'numdivs': self.var2_numdivs.value(),
                    'delay': self.var2_delay.value()}
                sweep_params['sweep_var'] = dict((k, v) for k, v in self.sweep_var_defaults.items())
        else:
            sweep_params = dict((k, v) for k, v in self.exp_params['Manual'].items())

        file_utils.dict2yaml(sweep_params, filename)

    def import_gui_control(self, widget):
        for attr in widget.__dict__.keys():
            if any(_type in attr for _type in ['btn_', 'dbl_', 'int_', 'linein_', 'chkbx_', 'list_', 'table_', 'glw_', 'label_', 'cbox_']):
                if not hasattr(self, attr):
                    setattr(self, attr, getattr(widget, attr))
                else:
                    if 'label_' not in attr:
                        print('%s already exist!' % attr)

    def set_gui_btn_enable(self, section, bool_set):
        if section in ['confocal', 'all']:
            self.btn_confocal_start.setEnabled(bool_set)
            self.btn_confocal_live.setEnabled(bool_set)
        if section in ['exp', 'all']:
            self.btn_exp_start.setEnabled(bool_set)
        if section in ['spectrometer', 'all']:
            self.btn_spectrometer_acquire.setEnabled(bool_set and self.spectrometer_initialized)
            self.btn_spectrometer_live.setEnabled(self.spectrometer_initialized)
            self.btn_spectrometer_stop.setEnabled(bool_set and self.spectrometer_initialized)
        if section in ['tracker', 'all']:
            self.btn_tracker_drive.setEnabled(bool_set)
            self.btn_tracker_home.setEnabled(bool_set)
            self.btn_tracker_run.setEnabled(bool_set)
        if section in ['liveapd', 'all']:
            self.btn_liveapd_start.setEnabled(bool_set)
            self.btn_liveapd_clear.setEnabled(bool_set)
            self.btn_liveapd_save.setEnabled(bool_set)
        if section in ['seqapd', 'all']:
            self.btn_seqapd_start.setEnabled(bool_set)
            self.btn_seqapd_clear.setEnabled(bool_set)
            self.btn_seqapd_save.setEnabled(bool_set)
        if section in ['nvlist', 'all']:
            self.btn_nvlist_start.setEnabled(bool_set)
            self.btn_nvlist_add.setEnabled(bool_set)
            self.btn_nvlist_clear.setEnabled(bool_set)
            self.btn_nvlist_del.setEnabled(bool_set)
            self.btn_nvlist_drive.setEnabled(bool_set)
            self.btn_nvlist_load.setEnabled(bool_set)
            self.btn_nvlist_shift.setEnabled(bool_set)
            self.btn_nvlist_save.setEnabled(bool_set)
            self.btn_nvlist_scripts_add.setEnabled(bool_set)
            self.btn_nvlist_scripts_del.setEnabled(bool_set)
            self.btn_nvlist_scripts_clear.setEnabled(bool_set)
            self.btn_nvlist_calscripts_add.setEnabled(bool_set)
            self.btn_nvlist_calscripts_del.setEnabled(bool_set)
            self.btn_nvlist_calscripts_clear.setEnabled(bool_set)
        if section in ['picoharp', 'all']:  # Picoharp doesn't care about other instruments
            self.btn_picoharp_update_settings.setEnabled(bool_set)

    def set_gui_input_enable(self, section, bool_set):
        if section in ['confocal', 'all']:
            self.dbl_confocal_x_start.setEnabled(bool_set)
            self.dbl_confocal_x_stop.setEnabled(bool_set)
            self.int_confocal_x_numdivs.setEnabled(bool_set)
            self.dbl_confocal_y_start.setEnabled(bool_set)
            self.dbl_confocal_y_stop.setEnabled(bool_set)
            self.int_confocal_y_numdivs.setEnabled(bool_set)
            self.dbl_confocal_z_start.setEnabled(bool_set)
            self.dbl_confocal_z_stop.setEnabled(bool_set)
            self.int_confocal_z_numdivs.setEnabled(bool_set)
            self.dbl_confocal_acqtime.setEnabled(bool_set)
            self.confocal_zstack_enable(bool(self.int_confocal_z_numdivs.value()) and bool_set)
        if section in ['exp', 'all']:
            self.cbox_exp_name.setEnabled(bool_set)
            self.var1_name.setEnabled(bool_set)
            self.var1_start.setEnabled(bool_set)
            self.var1_start_unit.setEnabled(bool_set)
            self.var1_stop.setEnabled(bool_set)
            self.var1_stop_unit.setEnabled(bool_set)
            self.var1_numdivs.setEnabled(bool_set)
            self.var1_delay.setEnabled(bool_set)
            self.var2_name.setEnabled(bool_set)
            self.var2_start.setEnabled(bool_set)
            self.var2_start_unit.setEnabled(bool_set)
            self.var2_stop.setEnabled(bool_set)
            self.var2_stop_unit.setEnabled(bool_set)
            self.var2_numdivs.setEnabled(bool_set)
            self.var2_delay.setEnabled(bool_set)
            self.chkbx_exp_logx.setEnabled(bool_set)
            self.btn_swap_var.setEnabled(bool_set)
            self.chkbx_readoutcal.setEnabled(bool_set)
            self.chkbx_2dexp.setEnabled(bool_set)
            self.chkbx_2dexp_meander.setEnabled(bool_set)
        if section in ['spectrometer', 'all']:
            self.chkbx_spectrometer_xbin.setEnabled(False)
            self.chkbx_spectrometer_ybin.setEnabled(False)
            self.dbl_spectrometer_centerwavelength.setEnabled(bool_set)
            self.dbl_spectrometer_exptime.setEnabled(bool_set)
            self.int_spectrometer_xbin_start.setEnabled(False)
            self.int_spectrometer_xbin_stop.setEnabled(False)
            self.int_spectrometer_ybin_start.setEnabled(bool_set)
            self.int_spectrometer_ybin_stop.setEnabled(bool_set)
        if section in ['tracker', 'all']:
            self.dbl_tracker_xystep.setEnabled(bool_set)
            self.dbl_tracker_zstep.setEnabled(bool_set)
            self.dbl_tracker_xrng.setEnabled(bool_set)
            self.dbl_tracker_yrng.setEnabled(bool_set)
            self.dbl_tracker_zrng.setEnabled(bool_set)
            self.int_tracker_numdivs.setEnabled(bool_set)
            self.dbl_tracker_acqtime.setEnabled(bool_set)
            self.dbl_tracker_pltime.setEnabled(bool_set)

    def set_gui_defaults(self):
        if self.task_handler.everything_finished() and not self.thread_terminal.isRunning():
            self.set_gui_btn_enable('all', True)
            self.set_gui_input_enable('all', True)
            self.btn_confocal_live.setChecked(False)
            # Disable the stop buttons
            self.btn_confocal_stop.setEnabled(self.thread_confocal.isRunning())
            self.btn_exp_stop.setEnabled(self.thread_sweep.isRunning())
            self.btn_nvlist_stop.setEnabled(self.thread_batch.isRunning())
            self.btn_liveapd_stop.setEnabled(self.thread_liveapd.isRunning())
            self.btn_seqapd_stop.setEnabled(self.thread_seqapd.isRunning())
            self.btn_picoharp_start.setEnabled(~self.thread_picoharp.isRunning())
            self.btn_picoharp_stop.setEnabled(self.thread_picoharp.isRunning())
            # todo: check why picoharp_start is necessary

    def exp_params_paramsChanged(self, item):
        paramtype = item.parent().text()
        parent = self.exp_params[paramtype]
        name = item.parent().child(item.row(), 0).text()

        if item.column() == 0:  # checkbox state changed
            self.update_params_label()
        if item.column() == 1:  # params value changed
            val = type(parent[name])(eval(item.text()))
            parent[name] = val
            self.exp_params_setval(name, val)

    def exp_params_setval(self, name, val, log=True):
        try:
            if log:
                self.label_terminal_cmdlog.append('setval(\'%s\', %s)' % (name, str(val)))

            if name in self.exp_params['Pulse'].keys():
                self.pb.set_param(name, float(val))
            elif name in self.exp_params['Instrument'].keys():
                self.setval[name](val)
                if 'ctlfreq' not in name:
                    self.exp_params['Instrument'][name] = self.getval[name]()  # query the instrument to make sure it's set
                else:
                    self.exp_params['Instrument']['ctlfreqpiezo'] = self.getval['ctlfreqpiezo']()
                    self.exp_params['Instrument']['ctlfreqwm'] = self.getval['ctlfreqwm']()
            elif name in self.exp_params['Confocal'].keys():
                self.setval[name](val)
                self.exp_params['Confocal'][name] = val
                if name in ['xpos', 'ypos', 'zpos']:
                    getattr(self, 'dbl_tracker_%s' % name).setValue(val)
                    self.exp_params['Confocal'][name] = float(val)
            elif name in self.exp_params['Manual'].keys():
                if name in ['stage_x', 'stage_y']:
                    spinbox = getattr(self, 'dbl_confocal_%s' % name)
                    spinbox.blockSignals(True)
                    spinbox.setValue(val)
                    spinbox.blockSignals(False)
                self.exp_params['Manual'][name] = float(val)
            elif 'itr' in name:
                pass  # for dummy variable itr, do nothing
            else:
                error_str = 'No variable named %s' % name
                self.log(error_str)
                raise ValueError()
        except Exception as e:
            self.log('exp_params_setval exception')
            self.log(str(e))
            time.sleep(0.1)

    def exp_params_getval(self, name):
        for paramtype in self.exp_params.keys():
            if name in self.exp_params[paramtype].keys():
                return self.exp_params[paramtype][name]
        else:
            error_str = 'No variable named %s' % name
            self.log(error_str)
            return np.nan

    def exp_params_setval_manual_prompt(self, name, val):
        self.label_exp_pause.setText('Set %s to %f' % (name, val))
        self.label_exp_pause.setVisible(True)
        self.btn_exp_pause.setVisible(True)
        self.btn_exp_pause.setEnabled(True)

    def exp_params_setval_manual_clicked(self):
        self.label_exp_pause.setVisible(False)
        self.btn_exp_pause.setVisible(False)
        self.wait_manual_setval.wakeAll()

    def exp_params_unit(self, var):
        if var in self.dict_var_id:
            return self.dict_var_unit[self.dict_var_id.index(var)]
        else:
            return None

    def update_params_table(self, refresh_params_inputs=False):
        # updates the parameter table
        # called when ESR Experiment changed
        # store checkbox states
        chkbox_state = {}

        for i in range(self.tree_exp_params.model().rowCount()):
            item_paramtype = self.tree_exp_params.model().item(i)
            for j in range(item_paramtype.rowCount()):
                item_param = item_paramtype.child(j, 0)
                chkbox_state.update({item_param.text(): item_param.checkState()})

        self.tree_exp_params.model().clear()
        self.tree_exp_params.model().setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.tree_exp_params.setColumnWidth(0, 150)

        params_list = []

        for x in self.exp_params:
            parent = QtGui.QStandardItem(x)
            parent.setFlags(QtCore.Qt.NoItemFlags)
            for y in self.exp_params[x]:
                params_list.append(y)
                value = self.exp_params[x][y]
                child0 = QtGui.QStandardItem(y)
                child0.setFlags(QtCore.Qt.NoItemFlags |
                                QtCore.Qt.ItemIsEnabled)
                child0.setCheckable(True)
                if refresh_params_inputs:
                    # default the checkboxes appropriately
                    exptype = self.cbox_exp_name.currentText()
                    if exptype in self.default_params_disp.keys():
                        if y in self.default_params_disp[exptype]:
                            child0.setCheckState(2)
                        else:
                            child0.setCheckState(0)
                    else:
                        child0.setCheckState(0)
                else:
                    if y in chkbox_state.keys():
                        child0.setCheckState(chkbox_state[y])

                child1 = QtGui.QStandardItem(str(value))
                child1.setFlags(QtCore.Qt.ItemIsEnabled |
                                QtCore.Qt.ItemIsEditable |
                                ~ QtCore.Qt.ItemIsSelectable)
                parent.appendRow([child0, child1])
            self.tree_exp_params.model().appendRow(parent)

        self.tree_exp_params.expandAll()
        self.tree_exp_params.sortByColumn(0, 0)  # sort by column 0, in ascending order

        self.update_params_label()

        # update the combobox for sweep variables
        if refresh_params_inputs:
            self.var1_name.clear()
            self.var1_name.addItems(sorted(params_list))
            self.var1_name.addItems(['nvnum', 'itr'])
            self.var2_name.clear()
            self.var2_name.addItems(sorted(params_list))
            self.var2_name.addItems(['nvnum', 'itr'])

        self.export_gui_settings()

        processEvents()

    def update_params_display(self, *args):
        for i in range(self.tree_exp_params.model().rowCount()):
            item_paramtype = self.tree_exp_params.model().item(i)
            paramtype = item_paramtype.text()
            for j in range(item_paramtype.rowCount()):
                item_param = item_paramtype.child(j, 0)
                param = item_param.text()

                if param in args:
                    item_param.setCheckState(2)
                else:
                    item_param.setCheckState(0)

        self.update_params_label()

    def update_params_label(self):
        label_str = ''
        for i in range(self.tree_exp_params.model().rowCount()):
            item_paramtype = self.tree_exp_params.model().item(i)
            paramtype = item_paramtype.text()
            for j in range(item_paramtype.rowCount()):
                item_param = item_paramtype.child(j, 0)
                param = item_param.text()
                sweep_var = [self.var1_name.currentText()]
                if self.chkbx_2dexp.isChecked():
                    sweep_var.append(self.var2_name.currentText())
                if item_param.checkState() and param not in sweep_var:
                    val = self.exp_params[paramtype][param]
                    if label_str:
                        label_str += '\n'
                    unit = self.exp_params_unit(param)
                    if unit is not None:
                        if 'freq' in param:
                            s = '%s: %.3f M%s' % (param, val/1e6, unit)
                        elif 'pw' in param or 'pulsewidth' in param:
                            s = '%s: %d n%s' % (param, val*1e9, unit)
                        elif 'reps' in param:
                            s = '%s: %dk' % (param, val/1e3)
                        else: # default to whatever formatting shown in the table for convenience
                            s = '%s: %s %s' % (param, item_paramtype.child(j, 1).text(), unit)
                    else:
                        s = '%s: %s' % (param, item_paramtype.child(j, 1).text())
                    label_str += s
                    # alternatively self.exp_params[paramtype][item_param.text()]

        self.label_exp_params.setText(label_str)

    def update_inst_stat(self):
        for key in self.get_inst_stat:
            stat = bool(self.get_inst_stat[key]())
            getattr(self, 'inst_btn_%s' % key).setChecked(stat)

    def set_inst_func(self, inst, func):
        is_btn_checked = getattr(self, 'inst_btn_%s_%s' % (inst, func)).isChecked()
        self.set_inst_stat['%s_%s' % (inst, func)](int(is_btn_checked))

    def confocal_mode_select(self, btn_id):
        isX = False; isY = False; isZ = False
        if btn_id == 0:
            isX = True
            isY = True
        if btn_id == 1:
            isX = True
            isZ = True
        if btn_id == 2:
            isY = True
            isZ = True

        if isX:
            if self.int_confocal_x_numdivs.value() == 0:
                self.int_confocal_x_numdivs.setValue(100)
        else:
            self.int_confocal_x_numdivs.setValue(0)
        if isY:
            if self.int_confocal_y_numdivs.value() == 0:
                self.int_confocal_y_numdivs.setValue(100)
        else:
            self.int_confocal_y_numdivs.setValue(0)
        if isZ:
            if self.int_confocal_z_numdivs.value() == 0:
                self.int_confocal_z_numdivs.setValue(100)
        else:
            self.int_confocal_z_numdivs.setValue(0)

    def confocal_zstack_enable(self, b):
        self.dbl_confocal_z_start.setEnabled(bool(b))
        self.dbl_confocal_z_stop.setEnabled(bool(b))

    def confocal_start(self):
        if self.task_handler.everything_finished():
            if not self.thread_terminal.isRunning():
                self.label_terminal_cmdlog.append('confocal(%.2f, %.2f, %d, %.2f, %.2f, %d, %.5f, avg=%d)' %
                                                  (self.dbl_confocal_x_start.value(),
                                                   self.dbl_confocal_x_stop.value(),
                                                   self.int_confocal_x_numdivs.value(),
                                                   self.dbl_confocal_y_start.value(),
                                                   self.dbl_confocal_y_stop.value(),
                                                   self.int_confocal_y_numdivs.value(),
                                                   self.dbl_confocal_acqtime.value(),
                                                   self.int_confocal_live_avg.value()))
            self.thread_confocal.start()

    def confocal_live(self, b):
        if b:
            if self.task_handler.everything_finished():
                self.thread_confocal.isLive = True
                self.thread_confocal.start()

    def confocal_live_set_avg(self, v):
        self.thread_confocal.confocal_live_avg = v

    def confocal_stop(self):
        self.thread_confocal.cancel = True

    def confocal_initplot(self):
        start_x = self.confocal_rngx[0]
        stop_x = self.confocal_rngx[-1]
        start_y = self.confocal_rngy[0]
        stop_y = self.confocal_rngy[-1]

        self.qtimg_confocal.setImage(self.confocal_pl[:, :, 0])
        # self.hlw_confocal.setImageItem(self.qtimg_confocal)

        for name in ['confocal']:
            qtimg = getattr(self, 'qtimg_%s' % name)
            qtimg.resetTransform()  # need to call this. otherwise pos and scale are relative to previous
            qtimg.setPos(start_x, start_y)
            scale_x = (stop_x - start_x)/(qtimg.image.shape[0])
            scale_y = (stop_y - start_y)/(qtimg.image.shape[1])
            qtimg.scale(scale_x, scale_y)

        if self.confocal_mode == 0:
            self.plt_confocal.setLabels(bottom='xpos (&mu;m)', left='ypos (&mu;m)')
        if self.confocal_mode == 1:
            self.plt_confocal.setLabels(bottom='xpos (&mu;m)', left='zpos (&mu;m)')
        if self.confocal_mode == 2:
            self.plt_confocal.setLabels(bottom='ypos (&mu;m)', left='zpos (&mu;m)')

        processEvents()

    def confocal_updateplot(self, zindex=0):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            self.qtimg_confocal.setImage(self.confocal_pl[:, :, zindex])
            # self.hlw_confocal.setImageItem(self.qtimg_confocal)

            if self.confocal_mode == 0:
                if self.int_confocal_z_numdivs.value() == 0:
                    filename = 'PLxposypos_%d' % self.wavenum
                else:
                    filename = 'PLxposyposzpos_%d' % self.wavenum

                self.plt_confocal.setTitle('%s: Z = %.2f' % (filename, self.confocal_rngz[zindex]))

            if self.confocal_mode == 1:
                filename = 'PLxposzpos_%d' % self.wavenum
                self.plt_confocal.setTitle('%s: Y = %.2f' % (filename, self.confocal_rngz[zindex]))

            if self.confocal_mode == 2:
                filename = 'PLyposzpos_%d' % self.wavenum
                self.plt_confocal.setTitle('%s: X = %.2f' % (filename, self.confocal_rngz[zindex]))

            self.label_filename.setText(filename)
            processEvents()

    def confocal_set_autolevel(self, b):
        self.hlw_confocal.item.autoLevel = bool(b)

    def confocal_grab_screenshots(self):
        # self.pixmap_confocal_graph = self.frame_main.grab()
        self.pixmap_confocal_graph = self.centralWidget().grab()

        self.pixmap_confocal_fig = self.tab_confocal.grab()
        processEvents()

    def confocal_confocalZ_add(self):
        numrows = self.table_confocalZ.rowCount()
        self.table_confocalZ.setRowCount(numrows+1)

        self.table_confocalZ.setItem(numrows, 0, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_xpos.value()))
        self.table_confocalZ.setItem(numrows, 1, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_ypos.value()))
        self.table_confocalZ.setItem(numrows, 2, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_zpos.value()))

    def confocal_confocalZ_del(self):
        self.table_confocalZ.removeRow(self.table_confocalZ.currentRow())

    def map_load(self):
        documents_path = os.path.expanduser(os.path.join('~', 'Documents', 'data_mat'))
        fd = QtGui.QFileDialog(directory=documents_path)
        targetfile = fd.getOpenFileName(filter='mat files (*.mat)')

        targetfile = targetfile[0]
        if targetfile != '':
            matfile = scipy.io.loadmat(targetfile)

            xvals = matfile['xvals'][0]
            yvals = matfile['yvals'][0]
            pl = np.squeeze(matfile['pl'])

            self.map_ax_xmin = xvals[0]
            self.map_ax_xmax = xvals[-1]
            self.map_ax_ymin = yvals[0]
            self.map_ax_ymax = yvals[-1]

            self.map_data = pl

            self.linein_map.setText(targetfile.split('/')[-1].split('.mat')[0])
            self.map_updateplot()

    def map_copy(self):
        self.map_ax_xmin = self.dbl_confocal_x_start.value()
        self.map_ax_xmax = self.dbl_confocal_x_stop.value()
        self.map_ax_ymin = self.dbl_confocal_y_start.value()
        self.map_ax_ymax = self.dbl_confocal_y_stop.value()

        self.map_data = self.confocal_pl[:, :, 0]

        self.linein_map.setText(self.label_filename.text())
        self.map_updateplot()

    def map_select(self, checked):
        if checked:  # enable cursor
            self.map_connect(self.map_clicked_drive)
        else:  # disable cursor here
            self.map_disconnect()

    def map_updateplot(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            if len(self.map_data) > 0:
                self.qtimg_map.setImage(self.map_data)
                self.qtimg_map.resetTransform()
                self.qtimg_map.setPos(self.map_ax_xmin, self.map_ax_ymin)
                scale_x = (self.map_ax_xmax - self.map_ax_xmin) / (self.qtimg_map.image.shape[0])
                scale_y = (self.map_ax_ymax - self.map_ax_ymin) / (self.qtimg_map.image.shape[1])
                self.qtimg_map.scale(scale_x, scale_y)

                # self.hlw_map.setImageItem(self.qtimg_map)

                processEvents()

    def map_mouseMoved(self, pos):
        if self.plt_map.sceneBoundingRect().contains(pos):
            mousePoint = self.vb_map.mapSceneToView(pos)
            self.map_vLine.setPos(mousePoint.x())
            self.map_hLine.setPos(mousePoint.y())

    def map_updatecursor(self):
        self.map_cursor.setData([self.dbl_tracker_xpos.value()], [self.dbl_tracker_ypos.value()])
        processEvents()

    def map_clicked_drive(self, event):
        if self.map_clicked_pos(event):
            self.chkbx_nvlist_update.setChecked(False)
            self.tracker_drive()

    def map_clicked_add_nvs(self, event):
        if self.map_clicked_pos(event):
            self.btn_nvlist_add.setChecked(False)
            self.map_updatecursor()
            self.tracker_start(self.int_nvlist_numtrack.value(), self.nvlist_add)

    def map_clicked_shift_nvs(self, event):
        if self.map_clicked_pos(event):
            self.btn_nvlist_shift.setChecked(False)
            self.map_updatecursor()

            selectedrows = self.table_nvlist.selectionModel().selectedRows()
            if not selectedrows:
                nvind = 1
            else:
                nvind = self.table_nvlist.currentRow() + 1

            self.exp_params_setval('nvnum', nvind)

            processEvents()

            self.tracker_start(self.int_nvlist_numtrack.value(), self.nvlist_update_offset)

    def map_clicked_pos(self, event):
        pos = event.scenePos()
        if self.plt_map.sceneBoundingRect().contains(pos) and event.button() == 1:
            mousePoint = self.vb_map.mapSceneToView(pos)
            self.dbl_tracker_xpos.setValue(mousePoint.x())
            self.dbl_tracker_ypos.setValue(mousePoint.y())
            self.dbl_tracker_zpos.setValue(self.dbl_tracker_zpos.value())
            return True
        else:
            return False

    def map_connect(self, clicked_func):
        self.map_vLine.show()
        self.map_hLine.show()
        self.plt_map.scene().sigMouseMoved.connect(self.map_mouseMoved)
        self.plt_map.scene().sigMouseClicked.connect(clicked_func)

    def map_disconnect(self):
        self.map_vLine.hide()
        self.map_hLine.hide()
        try:
            self.plt_map.scene().sigMouseMoved.disconnect()
        except TypeError:
            pass
        try:
            self.plt_map.scene().sigMouseClicked.disconnect()
        except TypeError:
            pass

    def tracker_start(self, numtrack=1, finished_func=None):
        # # Commented out to not log track() since it could be quite annoying
        # if not self.thread_terminal.isRunning():
        #     self.label_terminal_cmdlog.append('track()')

        if numtrack:
            # add here - check what things are running
            self.pb.set_cw()
            if self.thread_liveapd.isRunning():  # Live APD is running
                self.liveapd_stop()
                self.thread_liveapd.wait()
                self.thread_tracker.tracker_finished_func = self.liveapd_start
            else:
                self.thread_tracker.tracker_finished_func = finished_func

            self.set_gui_btn_enable('all', False)
            self.set_gui_input_enable('tracker', False)

            self.thread_tracker.numtrack = numtrack
            self.thread_tracker.start()
            # restart the things that were running
        else:  # numtrack==0, just skip tracking and do whatever is left to do, i.e. adding NV to list
            if finished_func is not None:
                if type(finished_func) == list:
                    for func in finished_func:
                        func()
                else:
                    finished_func()

    def tracker_drive(self):
        xpos = self.dbl_tracker_xpos.value()
        ypos = self.dbl_tracker_ypos.value()
        zpos = self.dbl_tracker_zpos.value()

        self.galpie.set_position([0, 1, 2], [xpos, ypos, zpos])

        self.exp_params['Confocal']['xpos'] = float(xpos)
        self.exp_params['Confocal']['ypos'] = float(ypos)
        self.exp_params['Confocal']['zpos'] = float(zpos)

        self.map_updatecursor()
        self.update_params_table()

    def tracker_home(self):
        self.dbl_tracker_xpos.setValue(0)
        self.dbl_tracker_ypos.setValue(0)
        self.dbl_tracker_zpos.setValue(5)
        self.tracker_drive()

    def tracker_step(self):
        # use drive2xyz to make fine steps upon button press, taking the position
        # listed in the drive lineins as the current position
        curpos = [self.dbl_tracker_xpos.value(), self.dbl_tracker_ypos.value(), self.dbl_tracker_zpos.value()]
        sender = self.sender()

        finalpos = curpos
        latstep = self.dbl_tracker_xystep.value()

        zstep = self.dbl_tracker_zstep.value()
        if sender == self.btn_tracker_driveup:
            finalpos[1] += latstep
        if sender == self.btn_tracker_drivedown:
            finalpos[1] -= latstep
        if sender == self.btn_tracker_driveleft:
            finalpos[0] -= latstep
        if sender == self.btn_tracker_driveright:
            finalpos[0] += latstep
        if sender == self.btn_tracker_drivezup:
            finalpos[2] += zstep
        if sender == self.btn_tracker_drivezdown:
            finalpos[2] -= zstep

        self.galpie.set_position([0, 1, 2], finalpos)
        self.dbl_tracker_xpos.setValue(finalpos[0])
        self.dbl_tracker_ypos.setValue(finalpos[1])
        self.dbl_tracker_zpos.setValue(finalpos[2])

    def tracker_auto_enable(self, b):
        if b:
            self.tracker_timer.start(self.dbl_tracker_period.value()*60*1000)
        else:
            self.tracker_timer.stop()

    def tracker_auto_start(self):
        if self.task_handler.everything_finished():
            self.tracker_start()

    def tracker_updateplot(self, i):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            self.curve_tracker_data[i].setData(self.trace_tracker_xvals[i], self.trace_tracker_yvals[i])
            self.curve_tracker_fit[i].setData(self.trace_tracker_xvals[i], self.trace_tracker_yfit[i])
            self.update_params_table()

            processEvents()

    def tracker_updateplot_freq(self, laser_name):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs
            getattr(self, 'curve_tracker_%s' % laser_name).setData(getattr(self, 'trace_tracker_%s_xvals' % laser_name),
                                                             getattr(self, 'trace_tracker_%s_yvals' % laser_name))
            getattr(self, 'curve_tracker_%s_fit' % laser_name).setData(getattr(self, 'trace_tracker_%s_xvals' % laser_name),
                                                                 getattr(self, 'trace_tracker_%s_yfit' % laser_name))
            self.update_params_table()

            processEvents()

    def tracker_updatelog(self, pl, p532):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            # round up all tracker values
            nvnum = self.exp_params['Confocal']['nvnum']
            xpos = self.dbl_tracker_xpos.value()
            ypos = self.dbl_tracker_ypos.value()
            zpos = self.dbl_tracker_zpos.value()

            self.tracker_xpos.append(xpos)
            self.tracker_ypos.append(ypos)
            self.tracker_zpos.append(zpos)

            self.tracker_p532.append(p532)

            self.label_p532.setText('Laser Power: %.3f mW' % p532)

            self.tracker_pl.append(pl)
            self.tracker_t.append(mainexp_widgets.now_timestamp())

            self.curve_tracker_xpos.setData(self.tracker_t, self.tracker_xpos)
            self.curve_tracker_ypos.setData(self.tracker_t, self.tracker_ypos)
            self.curve_tracker_zpos.setData(self.tracker_t, self.tracker_zpos)
            self.curve_tracker_p532.setData(self.tracker_t, self.tracker_p532)
            self.curve_tracker_pl.setData(self.tracker_t, self.tracker_pl)

            # update nv list when checked except when adding new NV
            if self.chkbx_nvlist_update.isChecked():
                self.nvlist_update_offset()

            # construct a binary record data
            now = datetime.datetime.now()
            # This is probably redundant and slightly different than the timestamp on the graph.
            # But for our purpose it doesn't matter
            stamp = time.mktime(now.timetuple())

            record = bytes()
            record += struct.pack('L', int(stamp))
            record += struct.pack('i', int(nvnum))
            record += struct.pack('f', xpos)
            record += struct.pack('f', ypos)
            record += struct.pack('f', zpos)
            record += struct.pack('f', p532)
            record += struct.pack('f', pl*1e3)

            for laser_name in self.tracker_laser_list:
                if laser_name != 'ctlfreq':
                    record += struct.pack('f', self.exp_params['Instrument'][laser_name + 'piezo'])
                else:
                    record += struct.pack('f', self.exp_params['Instrument'][laser_name + 'wm'])

            # prepend record length in anticipation for future changes
            record = struct.pack('i', len(record)) + record
            # If you want to be extra careful, could think about recording the signature of the record too.

            log_path = os.path.expanduser(os.path.join('~', 'Documents', 'exp_log'))

            f = open(os.path.join(log_path, now.strftime('%Y-%m-%d.log')), 'ab')
            f.write(record)
            f.close()

    def tracker_clear(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            self.tracker_xpos = []
            self.tracker_ypos = []
            self.tracker_zpos = []
            self.tracker_p532 = []
            self.tracker_pl = []
            self.tracker_t = []

            self.curve_tracker_xpos.setData(self.tracker_t, self.tracker_xpos)
            self.curve_tracker_ypos.setData(self.tracker_t, self.tracker_ypos)
            self.curve_tracker_zpos.setData(self.tracker_t, self.tracker_zpos)
            self.curve_tracker_p532.setData(self.tracker_t, self.tracker_p532)
            self.curve_tracker_pl.setData(self.tracker_t, self.tracker_pl)

    '''SWEEP PLOTTING'''
    def sweep_exp_set(self, exp_name):
        self.tab_main.setCurrentIndex(1)
        self.cbox_exp_name.blockSignals(True)
        self.cbox_exp_name.setCurrentIndex(self.cbox_exp_name.findText(exp_name))
        self.cbox_exp_name.blockSignals(False)
        self.sweep_exp_update()

    def sweep_exp_update(self):
        exp_name = self.cbox_exp_name.currentText()
        if not self.thread_terminal.isRunning():
            self.label_terminal_cmdlog.append('setexp(\'%s\')' % exp_name)
        self.log("Set Experiment: %s" % exp_name)

        # default values for the checkboxes
        self.chkbx_newctr_2d.setVisible(False)
        self.chkbx_2dexp_meander.setVisible(False)
        self.chkbx_PLE_fast.setVisible(False)

        self.chkbx_inv.setChecked(False)
        self.chkbx_inv2.setChecked(False)
        self.chkbx_inv.setEnabled(False)
        self.chkbx_inv2.setEnabled(False)

        if exp_name in ['CW', 'CW2']:
            self.thread_sweep.use_pb = False
            self.thread_sweep.isPLE = False
            self.thread_sweep.use_wm = False
            self.exp_params['Pulse'] = {}
        elif exp_name == 'PLE_CW':
            self.thread_sweep.use_pb = False
            self.thread_sweep.isPLE = True
            self.thread_sweep.use_wm = False
            self.exp_params['Pulse'] = {}
            self.chkbx_PLE_fast.setVisible(True)
            self.chkbx_PLE_fast.setEnabled(True)
            self.chkbx_PLE_fast.setChecked(True)
        elif exp_name == 'PLE_CW_WM':  # todo: have this be a checkbox in PLE_CW?
            self.thread_sweep.use_pb = False
            self.thread_sweep.isPLE = True
            self.thread_sweep.use_wm = True
            self.exp_params['Pulse'] = {}
            self.chkbx_PLE_fast.setVisible(True)
            self.chkbx_PLE_fast.setEnabled(True)
            self.chkbx_PLE_fast.setChecked(True)
        elif 'PLE_pulsed' in exp_name:
            self.pb.set_pulse(exp_name)
            self.thread_sweep.use_pb = True
            self.thread_sweep.isPLE = True
            self.thread_sweep.use_wm = False
            self.exp_params['Pulse'] = self.pb.params
            self.chkbx_PLE_fast.setVisible(True)
            self.chkbx_PLE_fast.setEnabled(True)
            self.chkbx_PLE_fast.setChecked(True)
        elif exp_name != '':
            self.pb.set_pulse(exp_name)
            self.thread_sweep.use_pb = True
            self.thread_sweep.isPLE = False
            self.thread_sweep.use_wm = False
            self.exp_params['Pulse'] = self.pb.params
            if 'inv' in self.exp_params['Pulse'].keys():
                self.chkbx_inv.setEnabled(True)
                self.chkbx_inv.setChecked(True)
            if 'inv2' in self.exp_params['Pulse'].keys():
                self.chkbx_inv2.setEnabled(True)
                self.chkbx_inv2.setChecked(True)

        if 'newctr' in exp_name:
            self.thread_sweep.newctr = True
            self.chkbx_newctr_2d.setVisible(True)
            self.chkbx_newctr_2d.setChecked(False)
        else:
            self.thread_sweep.newctr = False

        # todo: check this from pulseblaster instead
        if not self.thread_sweep.isPLE:
            self.inst_chkbx_mw1_enable.setChecked(
                exp_name not in ['CW2', 'rabi2', 'odmr2'])  # every esr experiment uses mw1 except CW2
            self.inst_chkbx_mw2_enable.setChecked(exp_name in ['CW2', 'rabi2', 'odmr2']
                                                          or 'DQ' in exp_name
                                                          or exp_name in ['deer', 'deer_mamin', 'awg_qurep']
                                                          or 'deer' in exp_name
                                                          or 'qurep' in exp_name)  # deer uses mw2

        p = QtGui.QPixmap(os.path.join(os.getcwd(), 'pulse', exp_name + '.png'))
        self.label_pb_disp.setPixmap(p)

        # set the default fitters
        if exp_name in ['CW', 'CW2']:
            fit = 'Lorentzian'
        elif exp_name in ['rabi', 'rabi2']:
            fit = 'sin'
        elif exp_name in ['cpmg', 'deer']:
            fit = 'power'
        else:
            fit = 'None'

        fitter_index = self.cbox_fittype.findText(fit)

        if fitter_index != -1:
            self.cbox_fittype.setCurrentIndex(fitter_index)

        sweep_params = self.import_sweep_settings()

        self.update_params_table(refresh_params_inputs=True)
        self.update_params_label()

        if 'Sweep' in sweep_params.keys():
            self.var1_name.setCurrentIndex(
                self.var1_name.findText(sweep_params['Sweep']['var1_name']))
            self.var2_name.setCurrentIndex(
                self.var2_name.findText(sweep_params['Sweep']['var2_name']))

        processEvents()

    def sweep_set_var1(self):
        var1_name = self.var1_name.currentText()
        if var1_name in self.sweep_var_defaults.keys():
            sweep_var_defaults = self.sweep_var_defaults[var1_name]
            self.var1_start.setValue(sweep_var_defaults['start'])
            self.var1_start_unit.setCurrentIndex(self.var1_start_unit.findText(sweep_var_defaults['start_unit']))
            self.var1_stop.setValue(sweep_var_defaults['stop'])
            self.var1_stop_unit.setCurrentIndex(self.var1_start_unit.findText(sweep_var_defaults['stop_unit']))
            self.var1_numdivs.setValue(sweep_var_defaults['numdivs'])
            self.var1_delay.setValue(sweep_var_defaults['delay'])

    def sweep_set_var2(self):
        var2_name = self.var2_name.currentText()
        if var2_name in self.sweep_var_defaults.keys():
            sweep_var_defaults = self.sweep_var_defaults[var2_name]
            self.var2_start.setValue(sweep_var_defaults['start'])
            self.var2_start_unit.setCurrentIndex(self.var2_start_unit.findText(sweep_var_defaults['start_unit']))
            self.var2_stop.setValue(sweep_var_defaults['stop'])
            self.var2_stop_unit.setCurrentIndex(self.var2_start_unit.findText(sweep_var_defaults['stop_unit']))
            self.var2_numdivs.setValue(sweep_var_defaults['numdivs'])
            self.var2_delay.setValue(sweep_var_defaults['delay'])

    def sweep_swap_var(self):
        var1_name = self.var1_name.currentIndex()
        var1_start = self.var1_start.value()
        var1_start_unit = self.var1_start_unit.currentIndex()
        var1_stop = self.var1_stop.value()
        var1_stop_unit = self.var1_stop_unit.currentIndex()
        var1_numdivs = self.var1_numdivs.value()
        var1_delay = self.var1_delay.value()
        var2_name = self.var2_name.currentIndex()
        var2_start = self.var2_start.value()
        var2_start_unit = self.var2_start_unit.currentIndex()
        var2_stop = self.var2_stop.value()
        var2_stop_unit = self.var2_stop_unit.currentIndex()
        var2_numdivs = self.var2_numdivs.value()
        var2_delay = self.var2_delay.value()

        self.var1_name.setCurrentIndex(var2_name)
        self.var1_start.setValue(var2_start)
        self.var1_start_unit.setCurrentIndex(var2_start_unit)
        self.var1_stop.setValue(var2_stop)
        self.var1_stop_unit.setCurrentIndex(var2_stop_unit)
        self.var1_numdivs.setValue(var2_numdivs)
        self.var1_delay.setValue(var2_delay)
        self.var2_name.setCurrentIndex(var1_name)
        self.var2_start.setValue(var1_start)
        self.var2_start_unit.setCurrentIndex(var1_start_unit)
        self.var2_stop.setValue(var1_stop)
        self.var2_stop_unit.setCurrentIndex(var1_stop_unit)
        self.var2_numdivs.setValue(var1_numdivs)
        self.var2_delay.setValue(var1_delay)

    def sweep_start(self):
        if not self.thread_terminal.isRunning():
            if not self.chkbx_2dexp.isChecked():
                self.label_terminal_cmdlog.append('do1d(\'%s\', %.3f, \'%s\', %.3f, \'%s\', %d, %.4f)' %
                                                          (self.var1_name.currentText(),
                                                           self.var1_start.value(),
                                                           self.var1_start_unit.currentText(),
                                                           self.var1_stop.value(),
                                                           self.var1_stop_unit.currentText(),
                                                           self.var1_numdivs.value(),
                                                           self.var1_delay.value()))
            else:
                self.label_terminal_cmdlog.append('do2d(\'%s\', %.3f, \'%s\', %.3f, \'%s\', %d, %.4f, \'%s\', %.3f, \'%s\', %.3f, \'%s\', %d, %.4f, meander=%r)' %
                                                  (self.var1_name.currentText(),
                                                   self.var1_start.value(),
                                                   self.var1_start_unit.currentText(),
                                                   self.var1_stop.value(),
                                                   self.var1_stop_unit.currentText(),
                                                   self.var1_numdivs.value(),
                                                   self.var1_delay.value(),
                                                   self.var2_name.currentText(),
                                                   self.var2_start.value(),
                                                   self.var2_start_unit.currentText(),
                                                   self.var2_stop.value(),
                                                   self.var2_stop_unit.currentText(),
                                                   self.var2_numdivs.value(),
                                                   self.var2_delay.value(),
                                                   self.chkbx_2dexp_meander.isChecked()))
        self.tab_main.setCurrentIndex(1)
        self.thread_sweep.start()

    def sweep_stop(self):
        # this does not get called when experiment finishes normally
        self.log('Experiment Manually Stopped.')
        self.thread_sweep.cancel = True

    def sweep_clear_plots(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            for index in reversed(range(self.grid_data_1.count())):
                self.grid_data_1.removeItem(self.grid_data_1.itemAt(index))
            for index in reversed(range(self.grid_data_2.count())):
                self.grid_data_2.removeItem(self.grid_data_2.itemAt(index))

            for name in ['main', 'inv', 'raw']:
                getattr(self, 'glw_%s' % name).clear()
                getattr(self, 'glw_%s' % name).hide()
                getattr(self, 'hlw_%s' % name).hide()

            self.grid_data_1.setColumnStretch(0, 12)
            self.grid_data_1.setColumnStretch(1, 2)

            self.grid_data_2.setColumnStretch(0, 5)
            self.grid_data_2.setColumnStretch(1, 2)
            self.grid_data_2.setColumnStretch(2, 5)
            self.grid_data_2.setColumnStretch(3, 2)

            for datatype in ['pl', 'pl_fit', 'ref', 'sig', 'pl2', 'ref2', 'sig2']:
                getattr(self, 'curve_%s' % datatype).setData([], [])

            for ch in range(6):
                getattr(self, 'curve_ple_ref_%d' % ch).setData([], [])
                getattr(self, 'curve_newctr_%d' % ch).setData([], [])

        processEvents()

    def sweep_esr_initplots(self):
        self.sweep_clear_plots()

        filename = self.label_filename.text()

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            if not self.thread_sweep.is2D:    # 1d scan
                self.grid_data_1.addWidget(self.glw_main, 0, 0, 1, 2)
                self.glw_main.show()
                self.glw_main.addItem(self.plt1d_pl)

                if not self.thread_sweep.use_pb:  # CW Experiment
                    self.plt1d_pl.setLabels(title=None, left=('PL', 'Hz'))
                    self.plt1d_pl.setLabel('bottom', text=self.var1_name.currentText(), units=self.exp_params_unit(self.var1_name.currentText()))
                else:  # Pulsed Experiment
                    self.grid_data_2.addWidget(self.glw_raw, 0, 0, 1, 4)
                    self.glw_raw.show()
                    self.glw_raw.addItem(self.plt1d_raw)

                    if not self.thread_sweep.isINV:
                        if 'timetrace' in self.cbox_exp_name.currentText():
                            self.plt1d_pl.setLabels(title=None, left=('PL', 'Hz', None))
                        elif not self.thread_sweep.pl_norm:
                            self.plt1d_pl.setLabels(title=None, left=('PL', 'a.u.', None))
                        else:
                            self.plt1d_pl.setLabels(title=None, left=('Norm. PL', 'a.u.', None))
                        self.curve_ref.setPen(pg.mkPen(color=(255, 196, 196)))
                    else:
                        if not self.thread_sweep.pl_norm:
                            self.plt1d_pl.setLabels(title=None, left=('Contrast', 'a.u.', None))
                        else:
                            self.plt1d_pl.setLabels(title=None, left=('Norm. Contrast', 'a.u.', None))
                        self.curve_ref.setPen('b')

                    self.plt1d_pl.setLabel('bottom', text=self.var1_name.currentText(), units=self.exp_params_unit(self.var1_name.currentText()))
                    self.plt1d_raw.setLabels(title='ESR Counts', left=('Counters', 'cnts'))
                    self.plt1d_raw.setLabel('bottom', text=self.var1_name.currentText(), units=self.exp_params_unit(self.var1_name.currentText()))

            else:   # 2d scan
                start_x = self.esr_rngx[0]
                stop_x = self.esr_rngx[-1]
                start_y = self.esr_rngy[0]
                stop_y = self.esr_rngy[-1]

                if not self.thread_sweep.isINV2:
                    self.grid_data_1.addWidget(self.glw_main, 0, 0)
                    self.glw_main.show()
                    self.glw_main.addItem(self.plt2d_pl, 0, 0)
                    self.grid_data_1.addWidget(self.hlw_main, 0, 1)
                    self.hlw_main.show()
                    self.hlw_main.setImageItem(self.qtimg_pl)
                    datatypes = ['pl']
                else:
                    self.grid_data_1.addWidget(self.glw_main, 0, 0, 1, 3)
                    self.grid_data_1.addWidget(self.hlw_main, 0, 3)

                    self.glw_main.show()
                    self.glw_main.addItem(self.plt2d_pl, 0, 0)
                    self.glw_main.addItem(self.plt2d_pl2, 0, 1)
                    self.hlw_main.show()
                    self.hlw_main.setImageItem([self.qtimg_pl, self.qtimg_pl2])
                    datatypes = ['pl', 'pl2']

                if not self.thread_sweep.isINV:
                    plt_title = {'pl': filename, 'sig': 'Sig Counts', 'ref': 'Ref Counts'}
                else:
                    if not self.thread_sweep.isINV2:
                        plt_title = {'pl': filename, 'sig': 'inv0_counts', 'ref': 'inv1_counts'}
                    else:
                        plt_title = {'pl': 'DEER', 'pl2': 'CPMG',
                                     'sig': 'DEER_inv0', 'ref': 'DEER_inv1',
                                     'sig2': 'CPMG_inv0', 'ref2': 'CPMG_inv1'}

                if not self.thread_sweep.use_pb:
                    self.hlw_main.setLabel('PL', units='Hz')
                else:
                    if not self.thread_sweep.isINV:
                        if 'timetrace' in self.cbox_exp_name.currentText():
                            self.hlw_main.setLabel('PL', units='Hz')
                        elif not self.thread_sweep.pl_norm:
                            self.hlw_main.setLabel('PL (a.u.)')
                        else:
                            self.hlw_main.setLabel('Norm. PL (a.u.)')
                    else:
                        if not self.thread_sweep.pl_norm:
                            self.hlw_main.setLabel('Contrast (a.u.)')
                        else:
                            self.hlw_main.setLabel('Norm. Contrast (a.u.)')

                    if not self.thread_sweep.isINV2:
                        datatypes.extend(['sig', 'ref'])
                        self.grid_data_2.addWidget(self.glw_raw, 0, 0, 1, 3)
                        self.grid_data_2.addWidget(self.hlw_raw, 0, 3)

                        self.glw_raw.show()
                        self.glw_raw.addItem(self.plt2d_sig, 0, 0)
                        self.glw_raw.addItem(self.plt2d_ref, 0, 1)
                        self.hlw_raw.show()
                        self.hlw_raw.setImageItem([self.qtimg_sig, self.qtimg_ref])
                    else:
                        datatypes.extend(['sig', 'ref', 'sig2', 'ref2'])
                        self.grid_data_2.addWidget(self.glw_raw, 0, 0, 1, 3)
                        self.grid_data_2.addWidget(self.hlw_raw, 0, 3)

                        self.glw_raw.show()
                        self.glw_raw.addItem(self.plt2d_sig, 0, 0)
                        self.glw_raw.addItem(self.plt2d_sig2, 0, 1)
                        self.glw_raw.addItem(self.plt2d_ref, 1, 0)
                        self.glw_raw.addItem(self.plt2d_ref2, 1, 1)
                        self.hlw_raw.show()
                        self.hlw_raw.setImageItem([self.qtimg_sig, self.qtimg_ref, self.qtimg_sig2, self.qtimg_ref2])

                    self.hlw_raw.setLabel('Counters', units='cnts')

                for datatype in datatypes:
                    qtimg = getattr(self, 'qtimg_%s' % datatype)
                    data = getattr(self, 'esrtrace_%s' % datatype)
                    qtimg.setImage(data)
                    qtimg.resetTransform()  # need to call this. otherwise pos and scale are relative to previous
                    qtimg.setPos(start_x, start_y)
                    scale_x = (stop_x - start_x) / (qtimg.image.shape[0])
                    scale_y = (stop_y - start_y) / (qtimg.image.shape[1])
                    qtimg.scale(scale_x, scale_y)

                    plt = getattr(self, 'plt2d_%s' % datatype)
                    plt.setTitle(plt_title[datatype], size='8pt')
                    plt.titleLabel.setMaximumHeight(10)
                    plt.layout.setRowFixedHeight(0, 5)

                    hiddenLabelStyle = {'color': 'transparent', 'font-size': '1px'} # to take care of the units

                    if not self.thread_sweep.isINV2:
                        _left_panels = ['pl', 'sig']
                        _bottom_panels = ['pl', 'sig', 'ref']
                    else:
                        _left_panels = ['pl', 'sig', 'ref']
                        _bottom_panels = ['pl', 'pl2', 'ref', 'ref2']

                    # Display y-axis labels only on the left panels
                    if datatype in _left_panels:
                        plt.setLabel('left', self.var2_name.currentText(),
                                     units=self.exp_params_unit(self.var2_name.currentText()))
                        plt.getAxis('left').setWidth(20)
                    else:
                        plt.setLabel('left', self.var2_name.currentText(),
                                     units=self.exp_params_unit(self.var2_name.currentText()), **hiddenLabelStyle)
                        plt.getAxis('left').setWidth(10)

                    # Display x-axis labels only on the bottom panels
                    if datatype in _bottom_panels:
                        plt.setLabel('bottom', self.var1_name.currentText(),
                                     units=self.exp_params_unit(self.var1_name.currentText()))
                        plt.getAxis('bottom').setHeight(25)
                    else:
                        plt.setLabel('bottom', self.var1_name.currentText(),
                                     units=self.exp_params_unit(self.var1_name.currentText()), **hiddenLabelStyle)
                        plt.getAxis('bottom').setHeight(10)

            processEvents()

    def sweep_esr_updateplots(self):
        self.update_params_table()

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs

            if not self.thread_sweep.is2D:    # 1d scan
                if not self.thread_sweep.use_pb:
                    self.curve_pl.setData(self.esr_rngx, self.esrtrace_pl)
                else:
                    self.curve_pl.setData(self.esr_rngx, self.esrtrace_pl)

                    if not self.thread_sweep.newctr:
                        self.curve_ref.setData(self.esr_rngx, self.esrtrace_ref)
                        self.curve_sig.setData(self.esr_rngx, self.esrtrace_sig)
                        if self.thread_sweep.isINV2:
                            self.curve_pl2.setData(self.esr_rngx, self.esrtrace_pl2)
                            self.curve_ref2.setData(self.esr_rngx, self.esrtrace_ref2)
                            self.curve_sig2.setData(self.esr_rngx, self.esrtrace_sig2)
                    else:  # new counter gating
                        numctr = self.esrtrace_newctr.shape[0]
                        if numctr > 7:
                            numctr = 7
                            print('too many curves to plot. only showing the first seven')

                        for i in range(numctr):
                            if not self.thread_sweep.newctr_2d:
                                getattr(self, 'curve_newctr_%d' % i).setData(self.esr_rngx, self.esrtrace_newctr[i, :])
                            else:
                                getattr(self, 'curve_newctr_%d' % i).setData(self.esr_rngx, np.sum(self.esrtrace_newctr[i, :, :], axis=1))
            else:   # 2d scan
                datatypes = ['pl']

                if self.thread_sweep.use_pb:
                    datatypes.extend(['sig', 'ref'])

                for datatype in datatypes:
                    qtimg = getattr(self, 'qtimg_%s' % datatype)
                    data = getattr(self, 'esrtrace_%s' % datatype)
                    qtimg.setImage(data)
                    processEvents()

            processEvents()

    def sweep_ple_initplots(self):
        self.sweep_clear_plots()

        if not self.thread_sweep.is2D:    # 1d scan
            self.grid_data_1.addWidget(self.glw_main, 0, 0, 1, 2)
            self.glw_main.show()
            self.glw_main.addItem(self.plt1d_pl)

            self.grid_data_2.addWidget(self.glw_raw, 0, 0, 1, 4)
            self.glw_raw.show()
            self.glw_raw.addItem(self.plt1d_raw)

            self.plt1d_pl.setLabels(title='PLE PL', left=('PL', 'Hz'))
            self.plt1d_pl.setLabel('bottom', self.var1_name.currentText(),
                                   units=self.exp_params_unit(self.var1_name.currentText()))

            if self.tlb1.scale == 1 and self.tlb1.offset == 0:
                self.plt1d_raw.setLabels(title='Analog Input', left=('Voltage', 'V'))
            else:
                self.plt1d_raw.setLabels(title='Analog Input', left='Wavelength (nm)')

            self.plt1d_raw.setLabel('bottom', self.var1_name.currentText(),
                                    units=self.exp_params_unit(self.var1_name.currentText()))

        else:  # 2d scan
            start_x = self.esr_rngx[0]
            stop_x = self.esr_rngx[-1]
            start_y = self.esr_rngy[0]
            stop_y = self.esr_rngy[-1]

            self.grid_data_1.addWidget(self.glw_main, 0, 0)
            self.glw_main.show()
            self.glw_main.addItem(self.plt2d_pl, 0, 0)
            self.grid_data_1.addWidget(self.hlw_main, 0, 1)
            self.hlw_main.show()
            self.hlw_main.setImageItem(self.qtimg_pl)

            if not self.thread_sweep.use_pb:
                self.hlw_main.setLabel('PL', units='Hz')
            else:
                self.hlw_main.setLabel('PL', units='a.u.')

            self.plt2d_pl.setTitle('PLE Data')

            self.grid_data_2.addWidget(self.glw_raw, 0, 0, 1, 3)
            self.grid_data_2.addWidget(self.hlw_raw, 0, 3)

            self.glw_raw.show()
            self.glw_raw.addItem(self.plt2d_ref, 0, 0)
            self.hlw_raw.show()
            self.hlw_raw.setImageItem([self.qtimg_ref])

            self.hlw_raw.setLabel('Wavelength (nm)')

            self.plt2d_ref.setTitle('Analog Input')

            for datatype in ['pl', 'ref']:
                qtimg = getattr(self, 'qtimg_%s' % datatype)
                data = getattr(self, 'esrtrace_%s' % datatype)
                qtimg.setImage(data)
                qtimg.resetTransform()  # need to call this. otherwise pos and scale are relative to previous
                qtimg.setPos(start_x, start_y)
                scale_x = (stop_x - start_x) / (qtimg.image.shape[0])
                scale_y = (stop_y - start_y) / (qtimg.image.shape[1])
                qtimg.scale(scale_x, scale_y)

                plt = getattr(self, 'plt2d_%s' % datatype)

                plt.setLabel('left', self.var2_name.currentText(),
                             units=self.exp_params_unit(self.var2_name.currentText()))
                plt.setLabel('bottom', self.var1_name.currentText(),
                             units=self.exp_params_unit(self.var1_name.currentText()))

        processEvents()

    def sweep_ple_updateplots(self):
        if not self.thread_sweep.is2D:  # 1d scan
            self.curve_pl.setData(self.esr_rngx, self.esrtrace_pl)

            if len(self.esr_rngx) != len(self.esrtrace_ref):
                # esrtrace_ref contains multiple channels:
                for ch in range(round(len(self.esrtrace_ref)/len(self.esr_rngx))):
                    lenx = len(self.esr_rngx)
                    getattr(self, 'curve_ple_ref_%d' % ch).setData(self.esr_rngx, self.esrtrace_ref[ch*lenx:(ch+1)*lenx])
            else:
                self.curve_ple_ref_0.setData(self.esr_rngx, self.esrtrace_ref)
        else:
            self.qtimg_pl.setImage(self.esrtrace_pl)
            self.qtimg_ref.setImage(self.esrtrace_ref[0:self.esrtrace_pl.shape[0]][:])

            # self.hlw_main.setImageItem(self.qtimg_pl)
            # self.hlw_raw.setImageItem(self.qtimg_ref)

        processEvents()

    def sweep_fits_clear(self):
        self.disp_fits.clear()

    def sweep_fits_update(self, fit_results):
        self.sweep_fits_clear()
        self.curve_pl_fit.setData(self.esr_fitx, self.esr_fity)
        self.disp_fits.append(fit_results)

    def sweep_grab_screenshots(self):
        # self.pixmap_sweep_graph = self.frame_main.grab()

        self.pixmap_sweep_graph = self.centralWidget().grab()
        self.pixmap_sweep_fig = self.frame_exp_fig.grab()
        processEvents()

    def sweep_set_readoutcal(self, state):
        self.pb.params_readoutcal_enable = bool(state)

        self.sweep_exp_update()

    '''SPECTROMETER'''
    def spectrometer_connect(self, b):
        if hasattr(self, 'spectrometer'):
            if b:
                self.spectrometer.gpib_connect()
                self.thread_spectrometer_init.start()
                self.cbox_spectrometer_grating.addItems(['1: 1200 g/mm, 750 nm',
                                                         '2: 300 g/mm, 1 um'])
                self.cbox_spectrometer_grating.setCurrentIndex(0)
                self.cbox_spectrometer_grating.currentIndexChanged.connect(self.thread_spectrometer.set_grating)
            else:
                self.spectrometer.picam.disconnect()
                self.spectrometer.inst.close()
                self.cbox_spectrometer_grating.currentIndexChanged.disconnect()
                self.cbox_spectrometer_grating.clear()
                self.spectrometer_initialized = False

    def spectrometer_start(self):
        if self.task_handler.everything_finished():
            if not self.thread_terminal.isRunning():
                self.label_terminal_cmdlog.append('spectrometer()')
            self.tab_main.setCurrentIndex(2)  # set to spectrometer tab

            self.set_gui_btn_enable('all', False)
            self.set_gui_input_enable('spectrometer', False)
            self.btn_spectrometer_stop.setEnabled(True)
            self.btn_spectrometer_acquire.setEnabled(False)
            self.thread_spectrometer.start()

    def spectrometer_live(self, b):
        if b and not self.thread_spectrometer.isRunning():
            self.spectrometer_start()

    def spectrometer_initplots(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            filename = 'PLWavelength_%d' % self.wavenum
            self.plt_spectrometer.setTitle(filename)
            self.label_filename.setText(filename)
            processEvents()

    def spectrometer_updateplots(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)  # for ignoring warnings when plotting NaNs
            self.curve_spectrometer.setData(self.trace_spectrometer[:, 0], self.trace_spectrometer[:, 1])
            processEvents()

    def spectrometer_grab_screenshots(self):
        self.pixmap_spectrometer_graph = self.frame_main.grab()
        self.pixmap_spectrometer_fig = self.tab_spectrometer.grab()

    '''BATCH'''

    def nvlist_clear(self):
        self.table_nvlist.setRowCount(0)
        self.nvlist_number += 1
        self.nvlist_update()


    def nvlist_select(self, checked):
        if checked:
            # stop updating nv list when adding new NVs
            self.chkbx_nvlist_update.setChecked(False)

            if not self.thread_liveapd.isRunning():
                self.map_connect(self.map_clicked_add_nvs)
            else:  # NV is being add from Live APD viewing. Skip the manual selection from map.
                self.btn_nvlist_add.setChecked(False)
                self.liveapd_stop()
                self.thread_liveapd.wait()
                finished_func = [self.nvlist_add, self.liveapd_start]
                self.tracker_start(self.int_nvlist_numtrack.value(), finished_func)
        else:
            self.map_disconnect()

    def nvlist_add(self):
        numrows = self.table_nvlist.rowCount()
        self.table_nvlist.setRowCount(numrows+1)

        self.table_nvlist.setItem(numrows, 0, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_xpos.value()))
        self.table_nvlist.setItem(numrows, 1, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_ypos.value()))
        self.table_nvlist.setItem(numrows, 2, QtGui.QTableWidgetItem('%.3f' % self.dbl_tracker_zpos.value()))

        self.nvlist_update()

    def nvlist_del(self):
        self.table_nvlist.removeRow(self.table_nvlist.currentRow())
        self.nvlist_update()

    def nvlist_save(self):
        fd = QtGui.QFileDialog(directory=os.path.expanduser(os.path.join('~', 'Documents')))
        fd.setAcceptMode(1)

        targetfile = fd.getSaveFileName(filter='csv file (*.csv)')[0]
        if targetfile != '':
            file_utils.table2csv(self.table_nvlist, targetfile)

    def nvlist_save_auto(self):
        now = datetime.datetime.now()
        nvlist_auto_save_file = os.path.expanduser(os.path.join('~', 'Documents', 'NV_list'))+'\\'\
                                +now.strftime('%Y-%m-%d-%H')+'_NV list_%d.csv' % self.nvlist_number
        file_utils.table2csv(self.table_nvlist, nvlist_auto_save_file)

    def nvlist_load(self):
        fd = QtGui.QFileDialog(directory=os.path.expanduser(os.path.join('~', 'Documents')))
        targetfile = fd.getOpenFileName(filter='csv files (*.csv)')[0]

        if targetfile != '':
            file_utils.csv2table(self.table_nvlist, targetfile)
            self.nvlist_number += 1
            self.nvlist_update()

    def nvlist_shift(self, checked):
        if checked:
            selectedrows = self.table_nvlist.selectionModel().selectedRows()
            if not selectedrows:
                nvref_row = 0
            else:
                nvref_row = self.table_nvlist.currentRow()

            # make a cursor and on click track and update the list
            self.log('Select the new position for NV #%d' % (nvref_row+1))
            self.map_connect(self.map_clicked_shift_nvs)
        else:
            self.map_disconnect()

    def nvlist_shift_manual(self):
        # copy position from tracker to current NV
        nvref_row = self.table_nvlist.currentRow()

        xpos = self.dbl_tracker_xpos.value()
        ypos = self.dbl_tracker_ypos.value()
        zpos = self.dbl_tracker_zpos.value()

        self.table_nvlist.setItem(nvref_row, 0, QtGui.QTableWidgetItem('%.3f' % xpos))
        self.table_nvlist.setItem(nvref_row, 1, QtGui.QTableWidgetItem('%.3f' % ypos))
        self.table_nvlist.setItem(nvref_row, 2, QtGui.QTableWidgetItem('%.3f' % zpos))

        self.nvlist_update()

    # Update the NV list based on the current tracker position as the current NV position.
    def nvlist_update_offset(self):
        nvind = self.exp_params['Confocal']['nvnum'] - 1  # this is not a very good way to write it
        if nvind < 0:
            self.log('Cannot update NV list. No NV list selected!')
        else:
            xpos = self.dbl_tracker_xpos.value()
            ypos = self.dbl_tracker_ypos.value()
            zpos = self.dbl_tracker_zpos.value()

            offset_x = xpos - float(self.table_nvlist.item(nvind, 0).text())
            offset_y = ypos - float(self.table_nvlist.item(nvind, 1).text())
            offset_z = zpos - float(self.table_nvlist.item(nvind, 2).text())

            # add the offset to the table
            numrows = self.table_nvlist.rowCount()
            for nvind2 in range(numrows):
                old_x = float(self.table_nvlist.item(nvind2, 0).text())
                old_y = float(self.table_nvlist.item(nvind2, 1).text())
                old_z = float(self.table_nvlist.item(nvind2, 2).text())

                self.table_nvlist.setItem(nvind2, 0, QtGui.QTableWidgetItem('%.3f' % (old_x + offset_x)))
                self.table_nvlist.setItem(nvind2, 1, QtGui.QTableWidgetItem('%.3f' % (old_y + offset_y)))
                self.table_nvlist.setItem(nvind2, 2, QtGui.QTableWidgetItem('%.3f' % (old_z + offset_z)))

            self.nvlist_update()

    def nvlist_update(self):
        numrows = self.table_nvlist.rowCount()

        numlabels = len(self.map_nvlabels)

        # add more label objects if necessary
        if numrows > numlabels:
            for i in range(numrows - numlabels):
                self.map_nvlabels.append(pg.TextItem(str(numlabels+i+1), color='w', anchor=(0.2, 0.8)))
                self.plt_map.addItem(self.map_nvlabels[numlabels+i])

        for label in self.map_nvlabels:
            label.hide()
        xlist = []
        ylist = []

        if numrows != 0:
            for nvind in range(numrows):
                xval = float(self.table_nvlist.item(nvind, 0).text())
                yval = float(self.table_nvlist.item(nvind, 1).text())

                self.map_nvlabels[nvind].show()
                self.map_nvlabels[nvind].setPos(xval, yval)

                xlist.append(xval)
                ylist.append(yval)

        self.map_nvlist.setData(xlist, ylist)
        processEvents()
        self.nvlist_save_auto()

    def nvlist_drive(self):
        self.task_handler.setval('nvnum', self.table_nvlist.currentRow()+1, ext=True)

    def nvlist_scripts_add(self):
        documents_path = os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts'))
        fd = QtGui.QFileDialog(directory=documents_path)
        targetfile = fd.getOpenFileName(filter='Python Scripts (*.py)')[0]

        if targetfile != '':
            self.list_nvlist_scripts.addItem(os.path.relpath(targetfile, documents_path))

    def nvlist_scripts_del(self):
        self.list_nvlist_scripts.takeItem(self.list_nvlist_scripts.currentRow())

    def nvlist_scripts_clear(self):
        self.list_nvlist_scripts.clear()

    def nvlist_calscripts_add(self):
        documents_path = os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts'))
        fd = QtGui.QFileDialog(directory=documents_path)
        targetfile = fd.getOpenFileName(filter='Python Scripts (*.py)')[0]

        if targetfile != '':
            self.list_nvlist_calscripts.addItem(os.path.relpath(targetfile, documents_path))

    def nvlist_calscripts_del(self):
        self.list_nvlist_calscripts.takeItem(self.list_nvlist_scripts.currentRow())

    def nvlist_calscripts_clear(self):
        self.list_nvlist_calscripts.clear()

    def nvlist_script_open(self, listitem):
        filename = listitem.text()
        os.startfile(os.path.expanduser(os.path.join('~', 'Documents', 'exp_scripts', filename)))

    def nvlist_auto_make_batch(self):
        confocal_map = self.map_data
        pl_shape_x = np.shape(confocal_map)[0]
        pl_shape_y = np.shape(confocal_map)[1]
        xvals = np.linspace(self.map_ax_xmin, self.map_ax_xmax, pl_shape_x)
        yvals = np.linspace(self.map_ax_ymin, self.map_ax_ymax, pl_shape_y)

        threshold = self.dbl_nvlist_make_batch_threshold.value()*1e3 # convert from kcps to cps
        min_sigma = self.dbl_nvlist_make_batch_min_sigma.value()
        max_sigma = self.dbl_nvlist_make_batch_max_sigma.value()
        overlap = self.dbl_nvlist_make_batch_overlap.value()

        blobs_log = blob_log(confocal_map, threshold=threshold, min_sigma=min_sigma, max_sigma=max_sigma, overlap=overlap)

        z_pos = self.dbl_tracker_zpos.value()
        for blob in blobs_log:
            x_pos = xvals[int(blob[0])]
            y_pos = yvals[int(blob[1])]
            numrows = self.table_nvlist.rowCount()
            self.table_nvlist.setRowCount(numrows + 1)

            self.table_nvlist.setItem(numrows, 0, QtGui.QTableWidgetItem('%.3f' % x_pos))
            self.table_nvlist.setItem(numrows, 1, QtGui.QTableWidgetItem('%.3f' % y_pos))
            self.table_nvlist.setItem(numrows, 2, QtGui.QTableWidgetItem('%.3f' % z_pos))

        self.nvlist_update()

    '''LIVE APD'''
    def liveapd_start(self):
        self.thread_liveapd.start()

    def liveapd_stop(self):
        self.thread_liveapd.cancel = True

    def liveapd_updateplots(self, acqtime, pl):
        self.liveapd_pl = np.append(self.liveapd_pl, pl)

        if not len(self.liveapd_t):
            self.liveapd_t = np.append(self.liveapd_t, 0)
        else:
            self.liveapd_t = np.append(self.liveapd_t, self.liveapd_t[-1] + acqtime)

        self.curve_liveapd.setData(self.liveapd_t, self.liveapd_pl)
        processEvents()

    def liveapd_clear(self):
        self.liveapd_pl = np.array([])
        self.liveapd_t = np.array([])
        self.curve_liveapd.setData([], [])

    def liveapd_grab_screenshots(self):
        self.pixmap_liveapd_graph = self.widget_liveapd.grab()
        processEvents()

    def seqapd_start(self):
        self.thread_seqapd.start()

    def seqapd_stop(self):
        self.thread_seqapd.cancel = True

    def seqapd_clear(self):
        self.seqapd_pl = np.array([])
        self.curve_seqapd.setData([], [])

    def seqapd_updateplots(self):
        self.curve_seqapd.setData(self.seqapd_t, self.seqapd_pl)
        processEvents()

    def seqapd_grab_screenshots(self):
        self.pixmap_seqapd_graph = self.widget_seqapd.grab()
        processEvents()

    def satcurve_start(self):
        self.thread_satcurve.start()

    def satcurve_stop(self):
        self.thread_satcurve.cancel = True

    def satcurve_updateplots(self):
        self.curve_satcurve.setData(self.satcurve_p, self.satcurve_pl)
        # Clear fit since the data is updated
        self.curve_satcurve_fit.setData([], [])
        self.label_satcurve_fit.setText('')
        processEvents()

    def satcurve_updatefits(self):
        self.curve_satcurve_fit.setData(self.satcurve_p_fit, self.satcurve_pl_fit)
        processEvents()

    def satcurve_grab_screenshots(self):
        self.pixmap_satcurve_graph = self.widget_satcurve.grab()
        processEvents()

    def terminal_clear_cmdlog(self):
        self.label_terminal_cmdlog.clear()

    def terminal_clear_cmdqueue(self):
        self.list_terminal_cmdqueue.clear()

    def terminal_del_cmdqueue(self):
        self.list_terminal_cmdqueue.takeItem(self.list_terminal_cmdqueue.currentRow())

    def terminal_enable_cmdqueue(self, enable):
        if enable:
            self.thread_terminal.timer.start(100)
        else:
            self.thread_terminal.timer.stop()

    def pb_load_params(self):
        documents_path = os.path.expanduser(os.path.join('~', 'Documents', 'data_mat'))
        fd = QtGui.QFileDialog(directory=documents_path)
        targetfile = fd.getOpenFileName(filter='yaml files (*.yaml)')

        targetfile = targetfile[0]
        if targetfile != '':
            if os.path.isfile(targetfile):
                sweep_params = file_utils.yaml2dict(targetfile)
                if 'Sweep' in sweep_params.keys():
                    if sweep_params['Sweep']['pulsename'] != self.cbox_exp_name.currentText():
                        self.log('Warning: Sweep settings load from a different experiment type!')
                        self.log(sweep_params['Sweep']['pulsename'])
                    if 'Pulse' in sweep_params.keys():
                        for name in sweep_params['Pulse'].keys():
                            val = sweep_params['Pulse'][name]
                            if name in self.exp_params['Pulse'].keys() and self.exp_params['Pulse'][name] != val:
                                self.exp_params_setval(name, val, log=False)
                                # call pb function directly to avoid delays in each settings
                                self.pb.set_param(name, val)

        self.update_params_table()

    def pb_set_static(self):
        numchan = 12

        pbflags_dec = 0

        for ch in range(numchan):
            if getattr(self, 'chkbx_pb%d' % ch).isChecked():
                pbflags_dec += pow(2, ch)

        self.pb.set_static(pbflags_dec)

    def pb_update_pulse_list(self):
        self.cbox_exp_name.blockSignals(True)
        self.pb.update_pulse_list(log=True)
        self.cbox_exp_name.clear()
        self.cbox_exp_name.addItems(self.pb.list_functions())
        self.cbox_exp_name.setCurrentIndex(0)
        self.cbox_exp_name.blockSignals(False)

    def pb_update_dict(self):
        file_pb_params = os.path.expanduser(os.path.join('~', 'Documents', 'exp_config', 'pb_dict.csv'))
        if not os.path.isfile(file_pb_params):
            pb_dict = {}
            self.log('pb_dict.csv does not exist!')
        else:
            try:
                _table = list(zip(*list(csv.reader(open(file_pb_params)))))
                _pbnum = [int(x) for x in _table[0]]
                _key = list(_table[1])
                _inv = [int(x) for x in _table[2]]
                pb_dict = {'pbnum': _pbnum, 'key': _key, 'inv': _inv}
                self.log('Updated config from pb_dict.csv')
            except IndexError:
                self.log('Invalid pb_dict.csv file.')
                pb_dict = {}

        if pb_dict:
            self.pb.set_pb_dict(pb_dict)
            # clear labels
            numchan = 12
            for ch in range(numchan):
                getattr(self, 'chkbx_pb%d' % ch).setText('PB%d' % ch)

            # redo the labels
            _pbnum = pb_dict['pbnum']
            _key = pb_dict['key']
            _inv = pb_dict['inv']

            for i, v in enumerate(_pbnum):
                if not _inv[i]:
                    getattr(self, 'chkbx_pb%d' % v).setText('PB%d (%s)' % (v, _key[i]))
                else:
                    getattr(self, 'chkbx_pb%d' % v).setText('PB%d (blank %s)' % (v, _key[i]))

    def pb_set_tracker_laser(self):
        self.pb.tracker_laser = self.linein_trackinglaser.text().replace(' ', '').split(',')

    def pbcustom_add(self):
        numrows = self.table_pbcustom.rowCount()
        self.table_pbcustom.setRowCount(numrows+1)
        self.table_pbcustom.setVerticalHeaderLabels([str(x) for x in list(range(numrows+1))])

    def pbcustom_del(self):
        current_row = self.table_pbcustom.currentRow()
        if current_row != -1:
            self.table_pbcustom.removeRow(current_row)
        else:
            self.table_pbcustom.removeRow(self.table_pbcustom.rowCount()-1)

        numrows = self.table_pbcustom.rowCount()
        self.table_pbcustom.setVerticalHeaderLabels([str(x) for x in list(range(numrows))])

    def pbcustom_run(self):
        numrows = self.table_pbcustom.rowCount()
        pb_dict = self.exp_params['Pulse']
        pb_dict.update(self.pb.readout_params)

        try:
            self.pb.start_programming()

            for inst in range(numrows):
                flags = self.table_pbcustom.item(inst, 0).text().replace(' ', '').split(',')
                op_code = getattr(self.pb.inst_set, self.table_pbcustom.item(inst, 1).text())
                inst_data = int(self.table_pbcustom.item(inst, 2).text())
                inst_length = eval(self.table_pbcustom.item(inst, 3).text(), globals(), pb_dict)
                self.pb.add_inst(flags, op_code, inst_data, inst_length)
            self.pb.stop_programming()
            self.pb.start()
        except Exception as e:
            self.log(str(e))

    def pbcustom_save(self):
        fd = QtGui.QFileDialog(directory=os.path.expanduser(os.path.join('~', 'Documents')))
        fd.setAcceptMode(1)

        targetfile = fd.getSaveFileName(filter='csv file (*.csv)')[0]
        if targetfile != '':
            file_utils.table2csv(self.table_pbcustom, targetfile)

    def pbcustom_load(self):
        fd = QtGui.QFileDialog(directory=os.path.expanduser(os.path.join('~', 'Documents')))
        targetfile = fd.getOpenFileName(filter='csv files (*.csv)')[0]

        if targetfile != '':
            file_utils.csv2table(self.table_pbcustom, targetfile)

    def picoharp_start(self):
        self.thread_picoharp.start()

    def picoharp_stop(self):
        self.thread_picoharp.cancel = True

    def picoharp_initplots(self):
        self.label_picoharp_filename.setText('PLpicoharp_%d' % self.wavenum)
        self.plt_picoharp.setTitle('Picoharp Histogram: %s' % self.label_nvlist.text())
        self.picoharp_disp_autoscale(self.chkbx_picoharp_disp_autoscale.isChecked())
        processEvents()

    def picoharp_update_plot(self, t_remain):
        self.curve_picoharp.setData(self.picoharp_xvals_disp, self.picoharp_yvals_disp)
        self.label_picoharp_remaining.setText('%.1f' % t_remain)
        processEvents()

    def picoharp_update_rate(self, rate0, rate1):
        self.label_picoharp_rate0.setText('%.3e' % rate0)
        self.label_picoharp_rate1.setText('%.3e' % rate1)
        processEvents()

    def picoharp_update_status(self, s):
        self.label_picoharp_status.setText(s)
        processEvents()

    def picoharp_disp_autoscale(self, b):
        if b:
            self.dbl_picoharp_disp_xmin.setValue(0.0)
            self.dbl_picoharp_disp_xmax.setValue(65535 * self.thread_picoharp.res_acq / 1000)
            self.picoharp_disp_scale()
            processEvents()

    def picoharp_grab_screenshots(self):
        self.pixmap_picoharp_graph = self.widget_picoharp.grab()
        processEvents()

    def picoharp_disp_scale(self):
        self.plt_picoharp.setXRange(self.dbl_picoharp_disp_xmin.value()*1e-9, self.dbl_picoharp_disp_xmax.value()*1e-9)

    def get_pl(self, acqtime):
        self.ctrapd.reset()
        self.ctrtrig.reset()
        self.ctrapd.set_source(self.mainexp.inst_params['instruments']['ctrapd']['addr_src'])
        self.ctrapd.set_pause_trigger(self.mainexp.inst_params['instruments']['ctrtrig']['addr_out'])

        self.ctrapd.start()
        self.ctrtrig.set_time(acqtime)
        self.ctrtrig.start()
        self.ctrtrig.wait_until_done()
        self.ctrtrig.stop()
        val = self.ctrapd.get_count() / acqtime
        self.ctrapd.stop()
        self.ctrapd.reset()
        self.ctrtrig.reset()
        return val

    def set_label_nvnum(self, num):
        self.label_nvlist.setText('NV #%d' % num)
        self.label_nvlist_spectrometer.setText('NV #%d' % num)

    def closeEvent(self, *args, **kwargs):
        self.widget_tracker.close()
        self.widget_liveapd.close()
        self.widget_seqapd.close()
        self.widget_satcurve.close()
        self.widget_histogram.close()
        self.widget_picoharp.close()
        self.widget_calculator.close()
        self.widget_batch.close()
        self.widget_terminal.close()
        self.widget_shortcuts.close()

        if hasattr(self, 'wavemeter'):
            if self.wavemeter.isconnected:
                self.wavemeter.close()
        if hasattr(self, 'prm1z8'):
            if self.prm1z8.isconnected:
                self.prm1z8.close()

        self.export_gui_settings()

        if hasattr(self, 'video_test_timer'):
            self.video_test_timer.stop()

    def wavemeter_update_freq(self):
        if self.wavemeter.isconnected:
            freq = self.wavemeter.getLambda()
            self.label_wavemeter_freq.setText('Wavemeter: %.6f GHz' % freq)

    def log(self, text):
        self.logdisp.append(text)

        self.logdisp_scroll.verticalScrollBar().setSliderPosition(self.logdisp_scroll.verticalScrollBar().maximum())

    def log_clear(self):
        self.logdisp.clear()

    def debug(self):
        pdb.set_trace()


def processEvents():
    QtGui.QApplication.processEvents()


def main(dualgalvo=False):
    """Packaged main function that launches GUI"""
    app = QtWidgets.QApplication(sys.argv)
    form = MainExp_GUI()
    form.show()

    if dualgalvo:
        form2 = MainExp_GUI(galvo2=True)
        form2.show()

    # form.chkbox_tracktime.setChecked(False)
    # form.chkboxsave.setChecked(False)
    app.exec_()


if __name__ == '__main__':
    main('dualgalvo' in sys.argv)
