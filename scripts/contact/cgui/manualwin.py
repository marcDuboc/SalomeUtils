# -*- coding: utf-8 -*-
# manualcontact gui module
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit,QGroupBox, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from contact.cgui import IMG_PATH

class ManualWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Manual Contact creation')
        # create groupbox group 1
        self.gp_grp1 = QGroupBox("Group 1", self)
        # create lidedit for group name
        self.le_grp1 = QLineEdit()
        self.le_grp1.setReadOnly(True)
        self.le_grp1.setText("Please select a group")
        # create button for group selection
        self.bt_grp1 = QPushButton()
        self.bt_grp1.setIcon(QIcon(os.path.join(IMG_PATH,'input.png')))

        self.hbox_grp1 = QHBoxLayout()
        self.hbox_grp1.addWidget(self.le_grp1)
        self.hbox_grp1.addWidget(self.bt_grp1)
        self.gp_grp1.setLayout(self.hbox_grp1)

        # create groupbox group 2
        self.gp_grp2 = QGroupBox("Group 2", self)
        # create lidedit for group name
        self.le_grp2 = QLineEdit()
        self.le_grp2.setReadOnly(True)
        self.le_grp2.setText("Please select a group")
        # create button for group selection
        self.bt_grp2 = QPushButton()
        self.bt_grp2.setIcon(QIcon(os.path.join(IMG_PATH,'input.png')))
        self.hbox_grp2 = QHBoxLayout()
        self.hbox_grp2.addWidget(self.le_grp2)
        self.hbox_grp2.addWidget(self.bt_grp2)
        self.gp_grp2.setLayout(self.hbox_grp2)

        # create button OK
        self.btnOK = QPushButton('Ok')
        # crate button cancel
        self.btnCancel = QPushButton('Cancel')
        # add horizontal layout for buttons
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.btnCancel)
        self.hbox.addWidget(self.btnOK)

        # layout
        layout = QGridLayout()
        layout.addWidget(self.gp_grp1, 1, 0, 1, 2)
        layout.addWidget(self.gp_grp2, 2, 0, 1, 2)
        layout.addLayout(self.hbox, 3, 1)
        self.setLayout(layout)

        #signal connection
        self.btnCancel.clicked.connect(self.hide)