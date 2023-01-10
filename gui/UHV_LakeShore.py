# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UHV_LakeShore.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(595, 489)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lcd_temp = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcd_temp.setGeometry(QtCore.QRect(370, 390, 201, 91))
        self.lcd_temp.setDigitCount(6)
        self.lcd_temp.setObjectName("lcd_temp")
        self.label_temp = QtWidgets.QLabel(self.centralwidget)
        self.label_temp.setGeometry(QtCore.QRect(370, 370, 91, 20))
        self.label_temp.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_temp.setObjectName("label_temp")
        self.glw_log = GraphicsLayoutWidget(self.centralwidget)
        self.glw_log.setGeometry(QtCore.QRect(10, 10, 561, 351))
        self.glw_log.setObjectName("glw_log")
        self.btn_log_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_log_clear.setGeometry(QtCore.QRect(520, 370, 51, 21))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.btn_log_clear.setFont(font)
        self.btn_log_clear.setCheckable(False)
        self.btn_log_clear.setObjectName("btn_log_clear")
        self.lcd_output = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcd_output.setGeometry(QtCore.QRect(10, 390, 91, 31))
        self.lcd_output.setDigitCount(6)
        self.lcd_output.setObjectName("lcd_output")
        self.label_time_start = QtWidgets.QLabel(self.centralwidget)
        self.label_time_start.setGeometry(QtCore.QRect(120, 390, 341, 19))
        self.label_time_start.setObjectName("label_time_start")
        self.label_time_stop = QtWidgets.QLabel(self.centralwidget)
        self.label_time_stop.setGeometry(QtCore.QRect(120, 410, 341, 19))
        self.label_time_stop.setObjectName("label_time_stop")
        self.cbox_heater_mode = QtWidgets.QComboBox(self.centralwidget)
        self.cbox_heater_mode.setGeometry(QtCore.QRect(120, 450, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.cbox_heater_mode.setFont(font)
        self.cbox_heater_mode.setObjectName("cbox_heater_mode")
        self.label_output = QtWidgets.QLabel(self.centralwidget)
        self.label_output.setGeometry(QtCore.QRect(10, 370, 101, 20))
        self.label_output.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_output.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_output.setObjectName("label_output")
        self.dbl_setpoint = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.dbl_setpoint.setGeometry(QtCore.QRect(10, 450, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.dbl_setpoint.setFont(font)
        self.dbl_setpoint.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.dbl_setpoint.setKeyboardTracking(False)
        self.dbl_setpoint.setMaximum(450.0)
        self.dbl_setpoint.setObjectName("dbl_setpoint")
        self.label_setpoint = QtWidgets.QLabel(self.centralwidget)
        self.label_setpoint.setGeometry(QtCore.QRect(10, 430, 91, 20))
        self.label_setpoint.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_setpoint.setObjectName("label_setpoint")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "LakeShore Temperature Controller"))
        self.label_temp.setText(_translate("MainWindow", "System Temp (K)"))
        self.btn_log_clear.setText(_translate("MainWindow", "Clear"))
        self.label_time_start.setText(_translate("MainWindow", "time"))
        self.label_time_stop.setText(_translate("MainWindow", "time"))
        self.label_output.setText(_translate("MainWindow", "Heater Output (%)"))
        self.label_setpoint.setText(_translate("MainWindow", "Setpoint (K)"))

from pyqtgraph import GraphicsLayoutWidget
