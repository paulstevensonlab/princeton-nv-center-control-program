# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_terminal.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(748, 403)
        self.label_terminal_cmdlog = QtWidgets.QTextBrowser(Form)
        self.label_terminal_cmdlog.setGeometry(QtCore.QRect(10, 10, 681, 171))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_terminal_cmdlog.sizePolicy().hasHeightForWidth())
        self.label_terminal_cmdlog.setSizePolicy(sizePolicy)
        self.label_terminal_cmdlog.setObjectName("label_terminal_cmdlog")
        self.linein_terminal_cmd = QtWidgets.QLineEdit(Form)
        self.linein_terminal_cmd.setGeometry(QtCore.QRect(10, 370, 681, 21))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.linein_terminal_cmd.sizePolicy().hasHeightForWidth())
        self.linein_terminal_cmd.setSizePolicy(sizePolicy)
        self.linein_terminal_cmd.setAutoFillBackground(False)
        self.linein_terminal_cmd.setFrame(True)
        self.linein_terminal_cmd.setObjectName("linein_terminal_cmd")
        self.btn_terminal_cmdlog_clear = QtWidgets.QPushButton(Form)
        self.btn_terminal_cmdlog_clear.setGeometry(QtCore.QRect(700, 10, 41, 23))
        self.btn_terminal_cmdlog_clear.setObjectName("btn_terminal_cmdlog_clear")
        self.btn_terminal_cmdqueue_clear = QtWidgets.QPushButton(Form)
        self.btn_terminal_cmdqueue_clear.setGeometry(QtCore.QRect(700, 190, 41, 23))
        self.btn_terminal_cmdqueue_clear.setObjectName("btn_terminal_cmdqueue_clear")
        self.list_terminal_cmdqueue = QtWidgets.QListWidget(Form)
        self.list_terminal_cmdqueue.setGeometry(QtCore.QRect(10, 190, 681, 171))
        self.list_terminal_cmdqueue.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed)
        self.list_terminal_cmdqueue.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.list_terminal_cmdqueue.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.list_terminal_cmdqueue.setAlternatingRowColors(False)
        self.list_terminal_cmdqueue.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.list_terminal_cmdqueue.setViewMode(QtWidgets.QListView.ListMode)
        self.list_terminal_cmdqueue.setObjectName("list_terminal_cmdqueue")
        self.btn_terminal_cmdqueue_del = QtWidgets.QPushButton(Form)
        self.btn_terminal_cmdqueue_del.setGeometry(QtCore.QRect(700, 220, 41, 23))
        self.btn_terminal_cmdqueue_del.setObjectName("btn_terminal_cmdqueue_del")
        self.chkbx_terminal_cmdqueue = QtWidgets.QCheckBox(Form)
        self.chkbx_terminal_cmdqueue.setGeometry(QtCore.QRect(700, 340, 70, 17))
        self.chkbx_terminal_cmdqueue.setObjectName("chkbx_terminal_cmdqueue")
        self.chkbx_terminal_thd = QtWidgets.QCheckBox(Form)
        self.chkbx_terminal_thd.setGeometry(QtCore.QRect(700, 320, 70, 17))
        self.chkbx_terminal_thd.setObjectName("chkbx_terminal_thd")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.label_terminal_cmdlog, self.list_terminal_cmdqueue)
        Form.setTabOrder(self.list_terminal_cmdqueue, self.linein_terminal_cmd)
        Form.setTabOrder(self.linein_terminal_cmd, self.btn_terminal_cmdlog_clear)
        Form.setTabOrder(self.btn_terminal_cmdlog_clear, self.btn_terminal_cmdqueue_clear)
        Form.setTabOrder(self.btn_terminal_cmdqueue_clear, self.btn_terminal_cmdqueue_del)
        Form.setTabOrder(self.btn_terminal_cmdqueue_del, self.chkbx_terminal_cmdqueue)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Terminal"))
        self.btn_terminal_cmdlog_clear.setText(_translate("Form", "clear"))
        self.btn_terminal_cmdqueue_clear.setText(_translate("Form", "clear"))
        self.btn_terminal_cmdqueue_del.setText(_translate("Form", "del"))
        self.chkbx_terminal_cmdqueue.setText(_translate("Form", "active"))
        self.chkbx_terminal_thd.setText(_translate("Form", "thd"))


