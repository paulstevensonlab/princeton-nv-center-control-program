# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test_threading.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(361, 201)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.btn_start_script = QtWidgets.QPushButton(self.centralwidget)
        self.btn_start_script.setGeometry(QtCore.QRect(60, 70, 75, 23))
        self.btn_start_script.setObjectName("btn_start_script")
        self.btn_test = QtWidgets.QPushButton(self.centralwidget)
        self.btn_test.setGeometry(QtCore.QRect(200, 70, 75, 23))
        self.btn_test.setObjectName("btn_test")
        self.btn_cancel = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cancel.setGeometry(QtCore.QRect(60, 110, 75, 23))
        self.btn_cancel.setCheckable(False)
        self.btn_cancel.setObjectName("btn_cancel")
        self.cbox_pb = QtWidgets.QComboBox(self.centralwidget)
        self.cbox_pb.setGeometry(QtCore.QRect(60, 20, 151, 21))
        self.cbox_pb.setObjectName("cbox_pb")
        self.btn_run = QtWidgets.QPushButton(self.centralwidget)
        self.btn_run.setGeometry(QtCore.QRect(220, 20, 75, 23))
        self.btn_run.setObjectName("btn_run")
        self.btn_import = QtWidgets.QPushButton(self.centralwidget)
        self.btn_import.setGeometry(QtCore.QRect(20, 40, 75, 23))
        self.btn_import.setObjectName("btn_import")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 361, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btn_start_script.setText(_translate("MainWindow", "Start Script"))
        self.btn_test.setText(_translate("MainWindow", "test"))
        self.btn_cancel.setText(_translate("MainWindow", "cancel"))
        self.btn_run.setText(_translate("MainWindow", "Run"))
        self.btn_import.setText(_translate("MainWindow", "Import"))


