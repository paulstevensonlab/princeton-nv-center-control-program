# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_histogram.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(434, 374)
        self.glw_histogram = GraphicsLayoutWidget(Form)
        self.glw_histogram.setGeometry(QtCore.QRect(10, 10, 411, 291))
        self.glw_histogram.setObjectName("glw_histogram")
        self.label_histogram_counts = QtWidgets.QLabel(Form)
        self.label_histogram_counts.setGeometry(QtCore.QRect(10, 310, 191, 20))
        self.label_histogram_counts.setObjectName("label_histogram_counts")
        self.btn_histogram_start = QtWidgets.QPushButton(Form)
        self.btn_histogram_start.setGeometry(QtCore.QRect(290, 310, 41, 21))
        self.btn_histogram_start.setObjectName("btn_histogram_start")
        self.btn_histogram_stop = QtWidgets.QPushButton(Form)
        self.btn_histogram_stop.setGeometry(QtCore.QRect(330, 310, 41, 21))
        self.btn_histogram_stop.setObjectName("btn_histogram_stop")
        self.btn_histogram_save = QtWidgets.QPushButton(Form)
        self.btn_histogram_save.setGeometry(QtCore.QRect(380, 310, 41, 21))
        self.btn_histogram_save.setObjectName("btn_histogram_save")
        self.int_histogram_maxcounts = QtWidgets.QSpinBox(Form)
        self.int_histogram_maxcounts.setGeometry(QtCore.QRect(330, 340, 91, 22))
        self.int_histogram_maxcounts.setMaximum(10000000)
        self.int_histogram_maxcounts.setSingleStep(100)
        self.int_histogram_maxcounts.setObjectName("int_histogram_maxcounts")
        self.int_histogram_bin_min = QtWidgets.QSpinBox(Form)
        self.int_histogram_bin_min.setGeometry(QtCore.QRect(70, 340, 51, 22))
        self.int_histogram_bin_min.setMaximum(10000000)
        self.int_histogram_bin_min.setSingleStep(1)
        self.int_histogram_bin_min.setObjectName("int_histogram_bin_min")
        self.label_histogram_maxcounts = QtWidgets.QLabel(Form)
        self.label_histogram_maxcounts.setGeometry(QtCore.QRect(290, 340, 41, 20))
        self.label_histogram_maxcounts.setObjectName("label_histogram_maxcounts")
        self.label_histogram_bins = QtWidgets.QLabel(Form)
        self.label_histogram_bins.setGeometry(QtCore.QRect(10, 340, 31, 20))
        self.label_histogram_bins.setObjectName("label_histogram_bins")
        self.label_histogram_bins_2 = QtWidgets.QLabel(Form)
        self.label_histogram_bins_2.setGeometry(QtCore.QRect(50, 340, 31, 20))
        self.label_histogram_bins_2.setObjectName("label_histogram_bins_2")
        self.label_histogram_bins_3 = QtWidgets.QLabel(Form)
        self.label_histogram_bins_3.setGeometry(QtCore.QRect(130, 340, 31, 20))
        self.label_histogram_bins_3.setObjectName("label_histogram_bins_3")
        self.label_histogram_bins_4 = QtWidgets.QLabel(Form)
        self.label_histogram_bins_4.setGeometry(QtCore.QRect(220, 340, 16, 20))
        self.label_histogram_bins_4.setObjectName("label_histogram_bins_4")
        self.int_histogram_bin_max = QtWidgets.QSpinBox(Form)
        self.int_histogram_bin_max.setGeometry(QtCore.QRect(160, 340, 51, 22))
        self.int_histogram_bin_max.setMaximum(10000000)
        self.int_histogram_bin_max.setSingleStep(1)
        self.int_histogram_bin_max.setObjectName("int_histogram_bin_max")
        self.int_histogram_bin_n = QtWidgets.QSpinBox(Form)
        self.int_histogram_bin_n.setGeometry(QtCore.QRect(230, 340, 51, 22))
        self.int_histogram_bin_n.setMaximum(100)
        self.int_histogram_bin_n.setSingleStep(1)
        self.int_histogram_bin_n.setObjectName("int_histogram_bin_n")
        self.btn_histogram_rescale = QtWidgets.QPushButton(Form)
        self.btn_histogram_rescale.setGeometry(QtCore.QRect(230, 310, 51, 21))
        self.btn_histogram_rescale.setObjectName("btn_histogram_rescale")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.glw_histogram, self.int_histogram_bin_min)
        Form.setTabOrder(self.int_histogram_bin_min, self.int_histogram_bin_max)
        Form.setTabOrder(self.int_histogram_bin_max, self.int_histogram_bin_n)
        Form.setTabOrder(self.int_histogram_bin_n, self.int_histogram_maxcounts)
        Form.setTabOrder(self.int_histogram_maxcounts, self.btn_histogram_start)
        Form.setTabOrder(self.btn_histogram_start, self.btn_histogram_stop)
        Form.setTabOrder(self.btn_histogram_stop, self.btn_histogram_save)
        Form.setTabOrder(self.btn_histogram_save, self.btn_histogram_rescale)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Single Shot Histogram"))
        self.label_histogram_counts.setText(_translate("Form", "Histogram Counts"))
        self.btn_histogram_start.setText(_translate("Form", "start"))
        self.btn_histogram_stop.setText(_translate("Form", "stop"))
        self.btn_histogram_save.setText(_translate("Form", "save"))
        self.label_histogram_maxcounts.setText(_translate("Form", "stop at:"))
        self.label_histogram_bins.setText(_translate("Form", "bins:"))
        self.label_histogram_bins_2.setText(_translate("Form", "min:"))
        self.label_histogram_bins_3.setText(_translate("Form", "max:"))
        self.label_histogram_bins_4.setText(_translate("Form", "#"))
        self.btn_histogram_rescale.setText(_translate("Form", "rescale"))

from pyqtgraph import GraphicsLayoutWidget
