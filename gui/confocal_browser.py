# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'confocal_browser.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1573, 842)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 771, 821))
        self.groupBox.setObjectName("groupBox")
        self.confocal_1_btn_browse = QtWidgets.QPushButton(self.groupBox)
        self.confocal_1_btn_browse.setGeometry(QtCore.QRect(620, 450, 51, 21))
        self.confocal_1_btn_browse.setObjectName("confocal_1_btn_browse")
        self.confocal_1_chkbx_transpose = QtWidgets.QCheckBox(self.groupBox)
        self.confocal_1_chkbx_transpose.setGeometry(QtCore.QRect(610, 760, 71, 17))
        self.confocal_1_chkbx_transpose.setObjectName("confocal_1_chkbx_transpose")
        self.confocal_1_chkbx_invX = QtWidgets.QCheckBox(self.groupBox)
        self.confocal_1_chkbx_invX.setGeometry(QtCore.QRect(690, 760, 61, 17))
        self.confocal_1_chkbx_invX.setObjectName("confocal_1_chkbx_invX")
        self.confocal_1_chkbx_invY = QtWidgets.QCheckBox(self.groupBox)
        self.confocal_1_chkbx_invY.setGeometry(QtCore.QRect(690, 780, 61, 17))
        self.confocal_1_chkbx_invY.setObjectName("confocal_1_chkbx_invY")
        self.confocal_1_table_nvlist = QtWidgets.QTableWidget(self.groupBox)
        self.confocal_1_table_nvlist.setGeometry(QtCore.QRect(10, 500, 241, 261))
        self.confocal_1_table_nvlist.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.confocal_1_table_nvlist.setObjectName("confocal_1_table_nvlist")
        self.confocal_1_table_nvlist.setColumnCount(0)
        self.confocal_1_table_nvlist.setRowCount(0)
        self.confocal_1_table_nvlist.horizontalHeader().setDefaultSectionSize(50)
        self.confocal_1_table_nvlist.verticalHeader().setDefaultSectionSize(20)
        self.confocal_1_table_nvlist.verticalHeader().setMinimumSectionSize(20)
        self.nvlist1 = QtWidgets.QLabel(self.groupBox)
        self.nvlist1.setGeometry(QtCore.QRect(10, 480, 47, 13))
        self.nvlist1.setObjectName("nvlist1")
        self.confocal_1_btn_pnt2 = QtWidgets.QPushButton(self.groupBox)
        self.confocal_1_btn_pnt2.setGeometry(QtCore.QRect(290, 530, 51, 21))
        self.confocal_1_btn_pnt2.setObjectName("confocal_1_btn_pnt2")
        self.confocal_1_btn_pnt1 = QtWidgets.QPushButton(self.groupBox)
        self.confocal_1_btn_pnt1.setGeometry(QtCore.QRect(290, 500, 51, 21))
        self.confocal_1_btn_pnt1.setObjectName("confocal_1_btn_pnt1")
        self.confocal_1_pnt1_x = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.confocal_1_pnt1_x.setGeometry(QtCore.QRect(350, 500, 62, 22))
        self.confocal_1_pnt1_x.setDecimals(3)
        self.confocal_1_pnt1_x.setMinimum(-200.0)
        self.confocal_1_pnt1_x.setMaximum(200.0)
        self.confocal_1_pnt1_x.setObjectName("confocal_1_pnt1_x")
        self.confocal_1_pnt1_y = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.confocal_1_pnt1_y.setGeometry(QtCore.QRect(410, 500, 62, 22))
        self.confocal_1_pnt1_y.setDecimals(3)
        self.confocal_1_pnt1_y.setMinimum(-200.0)
        self.confocal_1_pnt1_y.setMaximum(200.0)
        self.confocal_1_pnt1_y.setObjectName("confocal_1_pnt1_y")
        self.confocal_1_pnt2_x = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.confocal_1_pnt2_x.setGeometry(QtCore.QRect(350, 530, 62, 22))
        self.confocal_1_pnt2_x.setDecimals(3)
        self.confocal_1_pnt2_x.setMinimum(-200.0)
        self.confocal_1_pnt2_x.setMaximum(200.0)
        self.confocal_1_pnt2_x.setObjectName("confocal_1_pnt2_x")
        self.confocal_1_pnt2_y = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.confocal_1_pnt2_y.setGeometry(QtCore.QRect(410, 530, 62, 22))
        self.confocal_1_pnt2_y.setDecimals(3)
        self.confocal_1_pnt2_y.setMinimum(-200.0)
        self.confocal_1_pnt2_y.setMaximum(200.0)
        self.confocal_1_pnt2_y.setObjectName("confocal_1_pnt2_y")
        self.confocal_1_btn_load = QtWidgets.QPushButton(self.groupBox)
        self.confocal_1_btn_load.setGeometry(QtCore.QRect(170, 760, 41, 23))
        self.confocal_1_btn_load.setObjectName("confocal_1_btn_load")
        self.confocal_1_btn_save = QtWidgets.QPushButton(self.groupBox)
        self.confocal_1_btn_save.setGeometry(QtCore.QRect(210, 760, 41, 23))
        self.confocal_1_btn_save.setObjectName("confocal_1_btn_save")
        self.confocal_1_label = QtWidgets.QLabel(self.groupBox)
        self.confocal_1_label.setGeometry(QtCore.QRect(10, 800, 241, 20))
        self.confocal_1_label.setObjectName("confocal_1_label")
        self.gridLayoutWidget_4 = QtWidgets.QWidget(self.groupBox)
        self.gridLayoutWidget_4.setGeometry(QtCore.QRect(20, 20, 591, 451))
        self.gridLayoutWidget_4.setObjectName("gridLayoutWidget_4")
        self.confocal_1_grid = QtWidgets.QGridLayout(self.gridLayoutWidget_4)
        self.confocal_1_grid.setContentsMargins(0, 0, 0, 0)
        self.confocal_1_grid.setObjectName("confocal_1_grid")
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(790, 10, 771, 821))
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayoutWidget_3 = QtWidgets.QWidget(self.groupBox_2)
        self.gridLayoutWidget_3.setGeometry(QtCore.QRect(170, 10, 591, 451))
        self.gridLayoutWidget_3.setObjectName("gridLayoutWidget_3")
        self.confocal_2_grid = QtWidgets.QGridLayout(self.gridLayoutWidget_3)
        self.confocal_2_grid.setContentsMargins(0, 0, 0, 0)
        self.confocal_2_grid.setObjectName("confocal_2_grid")
        self.confocal_2_btn_browse = QtWidgets.QPushButton(self.groupBox_2)
        self.confocal_2_btn_browse.setGeometry(QtCore.QRect(100, 440, 51, 21))
        self.confocal_2_btn_browse.setObjectName("confocal_2_btn_browse")
        self.confocal_2_chkbx_transpose = QtWidgets.QCheckBox(self.groupBox_2)
        self.confocal_2_chkbx_transpose.setGeometry(QtCore.QRect(610, 760, 71, 17))
        self.confocal_2_chkbx_transpose.setObjectName("confocal_2_chkbx_transpose")
        self.confocal_2_chkbx_invX = QtWidgets.QCheckBox(self.groupBox_2)
        self.confocal_2_chkbx_invX.setGeometry(QtCore.QRect(690, 760, 61, 17))
        self.confocal_2_chkbx_invX.setObjectName("confocal_2_chkbx_invX")
        self.confocal_2_chkbx_invY = QtWidgets.QCheckBox(self.groupBox_2)
        self.confocal_2_chkbx_invY.setGeometry(QtCore.QRect(690, 780, 61, 17))
        self.confocal_2_chkbx_invY.setObjectName("confocal_2_chkbx_invY")
        self.confocal_2_table_nvlist = QtWidgets.QTableWidget(self.groupBox_2)
        self.confocal_2_table_nvlist.setGeometry(QtCore.QRect(170, 480, 241, 271))
        self.confocal_2_table_nvlist.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.confocal_2_table_nvlist.setObjectName("confocal_2_table_nvlist")
        self.confocal_2_table_nvlist.setColumnCount(0)
        self.confocal_2_table_nvlist.setRowCount(0)
        self.confocal_2_table_nvlist.horizontalHeader().setDefaultSectionSize(50)
        self.confocal_2_table_nvlist.verticalHeader().setDefaultSectionSize(20)
        self.confocal_2_table_nvlist.verticalHeader().setMinimumSectionSize(20)
        self.nvlist2 = QtWidgets.QLabel(self.groupBox_2)
        self.nvlist2.setGeometry(QtCore.QRect(176, 460, 51, 20))
        self.nvlist2.setObjectName("nvlist2")
        self.confocal_2_btn_pnt1 = QtWidgets.QPushButton(self.groupBox_2)
        self.confocal_2_btn_pnt1.setGeometry(QtCore.QRect(540, 490, 51, 21))
        self.confocal_2_btn_pnt1.setObjectName("confocal_2_btn_pnt1")
        self.confocal_2_btn_pnt2 = QtWidgets.QPushButton(self.groupBox_2)
        self.confocal_2_btn_pnt2.setGeometry(QtCore.QRect(540, 520, 51, 21))
        self.confocal_2_btn_pnt2.setObjectName("confocal_2_btn_pnt2")
        self.confocal_2_pnt1_x = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.confocal_2_pnt1_x.setGeometry(QtCore.QRect(600, 490, 62, 22))
        self.confocal_2_pnt1_x.setDecimals(3)
        self.confocal_2_pnt1_x.setMinimum(-200.0)
        self.confocal_2_pnt1_x.setMaximum(200.0)
        self.confocal_2_pnt1_x.setObjectName("confocal_2_pnt1_x")
        self.confocal_2_pnt1_y = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.confocal_2_pnt1_y.setGeometry(QtCore.QRect(660, 490, 62, 22))
        self.confocal_2_pnt1_y.setDecimals(3)
        self.confocal_2_pnt1_y.setMinimum(-200.0)
        self.confocal_2_pnt1_y.setMaximum(200.0)
        self.confocal_2_pnt1_y.setObjectName("confocal_2_pnt1_y")
        self.confocal_2_pnt2_x = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.confocal_2_pnt2_x.setGeometry(QtCore.QRect(600, 520, 62, 22))
        self.confocal_2_pnt2_x.setDecimals(3)
        self.confocal_2_pnt2_x.setMinimum(-200.0)
        self.confocal_2_pnt2_x.setMaximum(200.0)
        self.confocal_2_pnt2_x.setObjectName("confocal_2_pnt2_x")
        self.confocal_2_pnt2_y = QtWidgets.QDoubleSpinBox(self.groupBox_2)
        self.confocal_2_pnt2_y.setGeometry(QtCore.QRect(660, 520, 62, 22))
        self.confocal_2_pnt2_y.setDecimals(3)
        self.confocal_2_pnt2_y.setMinimum(-200.0)
        self.confocal_2_pnt2_y.setMaximum(200.0)
        self.confocal_2_pnt2_y.setObjectName("confocal_2_pnt2_y")
        self.confocal_2_btn_save = QtWidgets.QPushButton(self.groupBox_2)
        self.confocal_2_btn_save.setGeometry(QtCore.QRect(370, 760, 41, 23))
        self.confocal_2_btn_save.setObjectName("confocal_2_btn_save")
        self.confocal_2_btn_calculate = QtWidgets.QPushButton(self.groupBox_2)
        self.confocal_2_btn_calculate.setGeometry(QtCore.QRect(310, 760, 61, 23))
        self.confocal_2_btn_calculate.setObjectName("confocal_2_btn_calculate")
        self.confocal_2_label = QtWidgets.QLabel(self.groupBox_2)
        self.confocal_2_label.setGeometry(QtCore.QRect(170, 790, 241, 20))
        self.confocal_2_label.setObjectName("confocal_2_label")
        self.statustext = QtWidgets.QTextBrowser(self.groupBox_2)
        self.statustext.setGeometry(QtCore.QRect(440, 580, 201, 141))
        self.statustext.setObjectName("statustext")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "Confocal Image 1"))
        self.confocal_1_btn_browse.setText(_translate("MainWindow", "browse"))
        self.confocal_1_chkbx_transpose.setText(_translate("MainWindow", "Transpose"))
        self.confocal_1_chkbx_invX.setText(_translate("MainWindow", "X invert"))
        self.confocal_1_chkbx_invY.setText(_translate("MainWindow", "Y invert"))
        self.nvlist1.setText(_translate("MainWindow", "NV list 1"))
        self.confocal_1_btn_pnt2.setText(_translate("MainWindow", "pt2"))
        self.confocal_1_btn_pnt1.setText(_translate("MainWindow", "pt1"))
        self.confocal_1_btn_load.setText(_translate("MainWindow", "load"))
        self.confocal_1_btn_save.setText(_translate("MainWindow", "save"))
        self.confocal_1_label.setText(_translate("MainWindow", "Confocal 1 Label"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Confocal Image 2"))
        self.confocal_2_btn_browse.setText(_translate("MainWindow", "browse"))
        self.confocal_2_chkbx_transpose.setText(_translate("MainWindow", "Transpose"))
        self.confocal_2_chkbx_invX.setText(_translate("MainWindow", "X invert"))
        self.confocal_2_chkbx_invY.setText(_translate("MainWindow", "Y invert"))
        self.nvlist2.setText(_translate("MainWindow", "NV list 2"))
        self.confocal_2_btn_pnt1.setText(_translate("MainWindow", "pt1"))
        self.confocal_2_btn_pnt2.setText(_translate("MainWindow", "pt2"))
        self.confocal_2_btn_save.setText(_translate("MainWindow", "save"))
        self.confocal_2_btn_calculate.setText(_translate("MainWindow", "calculate"))
        self.confocal_2_label.setText(_translate("MainWindow", "Confocal 2 Label"))

