# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_seqapd.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(434, 346)
        self.glw_seqapd = GraphicsLayoutWidget(Form)
        self.glw_seqapd.setGeometry(QtCore.QRect(10, 10, 411, 251))
        self.glw_seqapd.setObjectName("glw_seqapd")
        self.label_seqapd_stoptime = QtWidgets.QLabel(Form)
        self.label_seqapd_stoptime.setGeometry(QtCore.QRect(10, 300, 91, 20))
        self.label_seqapd_stoptime.setObjectName("label_seqapd_stoptime")
        self.dbl_seqapd_int_time = QtWidgets.QDoubleSpinBox(Form)
        self.dbl_seqapd_int_time.setGeometry(QtCore.QRect(120, 300, 71, 22))
        self.dbl_seqapd_int_time.setKeyboardTracking(False)
        self.dbl_seqapd_int_time.setMaximum(3600.0)
        self.dbl_seqapd_int_time.setObjectName("dbl_seqapd_int_time")
        self.btn_seqapd_start = QtWidgets.QPushButton(Form)
        self.btn_seqapd_start.setGeometry(QtCore.QRect(250, 310, 41, 21))
        self.btn_seqapd_start.setObjectName("btn_seqapd_start")
        self.btn_seqapd_stop = QtWidgets.QPushButton(Form)
        self.btn_seqapd_stop.setGeometry(QtCore.QRect(290, 310, 41, 21))
        self.btn_seqapd_stop.setObjectName("btn_seqapd_stop")
        self.btn_seqapd_clear = QtWidgets.QPushButton(Form)
        self.btn_seqapd_clear.setGeometry(QtCore.QRect(330, 310, 41, 21))
        self.btn_seqapd_clear.setObjectName("btn_seqapd_clear")
        self.btn_seqapd_save = QtWidgets.QPushButton(Form)
        self.btn_seqapd_save.setGeometry(QtCore.QRect(370, 310, 41, 21))
        self.btn_seqapd_save.setObjectName("btn_seqapd_save")
        self.label_seqapd_inttime = QtWidgets.QLabel(Form)
        self.label_seqapd_inttime.setGeometry(QtCore.QRect(10, 270, 91, 20))
        self.label_seqapd_inttime.setObjectName("label_seqapd_inttime")
        self.dbl_seqapd_acqtime = QtWidgets.QDoubleSpinBox(Form)
        self.dbl_seqapd_acqtime.setGeometry(QtCore.QRect(120, 270, 71, 22))
        self.dbl_seqapd_acqtime.setKeyboardTracking(False)
        self.dbl_seqapd_acqtime.setMaximum(1000.0)
        self.dbl_seqapd_acqtime.setObjectName("dbl_seqapd_acqtime")
        self.label_seqapd_filename = QtWidgets.QLabel(Form)
        self.label_seqapd_filename.setGeometry(QtCore.QRect(260, 270, 161, 20))
        self.label_seqapd_filename.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_seqapd_filename.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_seqapd_filename.setObjectName("label_seqapd_filename")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.glw_seqapd, self.dbl_seqapd_acqtime)
        Form.setTabOrder(self.dbl_seqapd_acqtime, self.dbl_seqapd_int_time)
        Form.setTabOrder(self.dbl_seqapd_int_time, self.btn_seqapd_start)
        Form.setTabOrder(self.btn_seqapd_start, self.btn_seqapd_stop)
        Form.setTabOrder(self.btn_seqapd_stop, self.btn_seqapd_clear)
        Form.setTabOrder(self.btn_seqapd_clear, self.btn_seqapd_save)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Seq APD"))
        self.label_seqapd_stoptime.setText(_translate("Form", "Stop Time (s)"))
        self.btn_seqapd_start.setText(_translate("Form", "start"))
        self.btn_seqapd_stop.setText(_translate("Form", "stop"))
        self.btn_seqapd_clear.setText(_translate("Form", "clear"))
        self.btn_seqapd_save.setText(_translate("Form", "save"))
        self.label_seqapd_inttime.setText(_translate("Form", "Time Interval (ms)"))
        self.label_seqapd_filename.setText(_translate("Form", "label_seqapd_filename"))


from pyqtgraph import GraphicsLayoutWidget
