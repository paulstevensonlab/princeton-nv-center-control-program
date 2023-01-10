# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GPIBdev_gui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(219, 186)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.linein_return = QtWidgets.QTextBrowser(Form)
        self.linein_return.setGeometry(QtCore.QRect(10, 80, 201, 91))
        self.linein_return.setObjectName("linein_return")
        self.linein_cmd = QtWidgets.QLineEdit(Form)
        self.linein_cmd.setGeometry(QtCore.QRect(10, 10, 201, 20))
        self.linein_cmd.setObjectName("linein_cmd")
        self.btn_write = QtWidgets.QPushButton(Form)
        self.btn_write.setGeometry(QtCore.QRect(10, 40, 75, 23))
        self.btn_write.setObjectName("btn_write")
        self.btn_query = QtWidgets.QPushButton(Form)
        self.btn_query.setGeometry(QtCore.QRect(130, 40, 75, 23))
        self.btn_query.setObjectName("btn_query")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btn_write.setText(_translate("Form", "Write"))
        self.btn_query.setText(_translate("Form", "Query"))

