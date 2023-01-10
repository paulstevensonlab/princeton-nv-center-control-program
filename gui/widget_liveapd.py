# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_liveapd.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(434, 346)
        self.glw_liveapd = GraphicsLayoutWidget(Form)
        self.glw_liveapd.setGeometry(QtCore.QRect(10, 10, 411, 291))
        self.glw_liveapd.setObjectName("glw_liveapd")
        self.label_liveapd_acqtime = QtWidgets.QLabel(Form)
        self.label_liveapd_acqtime.setGeometry(QtCore.QRect(10, 310, 91, 22))
        self.label_liveapd_acqtime.setObjectName("label_liveapd_acqtime")
        self.dbl_liveapd_acqtime = QtWidgets.QDoubleSpinBox(Form)
        self.dbl_liveapd_acqtime.setGeometry(QtCore.QRect(110, 310, 71, 22))
        self.dbl_liveapd_acqtime.setKeyboardTracking(False)
        self.dbl_liveapd_acqtime.setObjectName("dbl_liveapd_acqtime")
        self.btn_liveapd_start = QtWidgets.QPushButton(Form)
        self.btn_liveapd_start.setGeometry(QtCore.QRect(180, 310, 41, 22))
        self.btn_liveapd_start.setObjectName("btn_liveapd_start")
        self.btn_liveapd_stop = QtWidgets.QPushButton(Form)
        self.btn_liveapd_stop.setGeometry(QtCore.QRect(220, 310, 41, 22))
        self.btn_liveapd_stop.setObjectName("btn_liveapd_stop")
        self.btn_liveapd_clear = QtWidgets.QPushButton(Form)
        self.btn_liveapd_clear.setGeometry(QtCore.QRect(260, 310, 41, 22))
        self.btn_liveapd_clear.setObjectName("btn_liveapd_clear")
        self.btn_liveapd_save = QtWidgets.QPushButton(Form)
        self.btn_liveapd_save.setGeometry(QtCore.QRect(300, 310, 41, 22))
        self.btn_liveapd_save.setObjectName("btn_liveapd_save")
        self.btn_liveapd_single = QtWidgets.QPushButton(Form)
        self.btn_liveapd_single.setGeometry(QtCore.QRect(380, 310, 41, 22))
        self.btn_liveapd_single.setObjectName("btn_liveapd_single")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.glw_liveapd, self.dbl_liveapd_acqtime)
        Form.setTabOrder(self.dbl_liveapd_acqtime, self.btn_liveapd_start)
        Form.setTabOrder(self.btn_liveapd_start, self.btn_liveapd_stop)
        Form.setTabOrder(self.btn_liveapd_stop, self.btn_liveapd_clear)
        Form.setTabOrder(self.btn_liveapd_clear, self.btn_liveapd_save)
        Form.setTabOrder(self.btn_liveapd_save, self.btn_liveapd_single)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Live APD"))
        self.label_liveapd_acqtime.setText(_translate("Form", "Acquisition Time (s)"))
        self.btn_liveapd_start.setText(_translate("Form", "start"))
        self.btn_liveapd_stop.setText(_translate("Form", "stop"))
        self.btn_liveapd_clear.setText(_translate("Form", "clear"))
        self.btn_liveapd_save.setText(_translate("Form", "save"))
        self.btn_liveapd_single.setText(_translate("Form", "single"))

from pyqtgraph import GraphicsLayoutWidget
