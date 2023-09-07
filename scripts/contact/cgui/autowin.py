# -*- coding: utf-8 -*-
# autocontact gui module
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import time
import inspect
from PyQt5.QtWidgets import QPushButton, QWidget, QGridLayout, QLabel, QLineEdit, QGroupBox, QHBoxLayout,QDoubleSpinBox, QCheckBox,QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from contact.cgui import IMG_PATH

class AutoWindows(QWidget):
    partSelection = pyqtSignal()
    contactRun = pyqtSignal(float,float,bool,bool)

    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Auto contact creation')

        layout = QGridLayout()

        #parts selection
        self.l_p = QLabel("Parts selection: ", self)
        self.le_p = QLineEdit()
        self.le_p.setReadOnly(True)
        self.le_p.setText("Please select at least 2 parts")
        self.bt_p = QPushButton()
        self.bt_p.setIcon(QIcon(os.path.join(IMG_PATH,'input.png')))

        # Adjust Gap
        self.l_gap = QLabel("Max gap between (model unit): ")
        self.sb_gap = QDoubleSpinBox()
        self.sb_gap.setDecimals(3)
        self.sb_gap.setValue(0.000)
        self.sb_gap.setSingleStep(0.001)

        # Adjust coincidcence tolerance
        self.l_ctol = QLabel("Cylinder coincidence tolerance (radian): ")
        self.sb_ctol = QDoubleSpinBox()
        self.sb_ctol.setDecimals(3)
        self.sb_ctol.setValue(0.01)
        self.sb_ctol.setSingleStep(0.001)

        # create groupbox options
        self.gp_options = QGroupBox("Options", self)

        # create checkbox merge by part
        self.cb_merge_by_part = QCheckBox("merge group by part", self)
        self.cb_merge_by_part.setChecked(True)
        # create checkbox merge by proximity
        self.cb_merge_by_proximity = QCheckBox("merge group by proximity", self)
        self.cb_merge_by_proximity.setChecked(False)

        # put the checkbox in a horizontal layout
        self.hbox_options = QHBoxLayout()
        self.hbox_options.addWidget(self.cb_merge_by_part)
        self.hbox_options.addWidget(self.cb_merge_by_proximity)
        self.gp_options.setLayout(self.hbox_options)

        # create groupbox compute
        self.gp_compute = QGroupBox("Compute", self)
        # add hroizationtal layout for compute
        self.hbox_compute = QHBoxLayout()
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        self.bt_run = QPushButton("Run", self)
        # add progress bar and run button to horizontal layout
        self.hbox_compute.addWidget(self.pbar)
        self.hbox_compute.addWidget(self.bt_run)
        self.gp_compute.setLayout(self.hbox_compute)

        # add cancel button
        self.bt_cancel = QPushButton("Cancel", self)

        # layout
        layout.addWidget(self.l_p, 1, 0)
        layout.addWidget(self.le_p, 2, 0)
        layout.addWidget(self.bt_p, 2, 1)
        layout.addWidget(self.l_gap, 3, 0)
        layout.addWidget(self.sb_gap, 3, 1)
        layout.addWidget(self.l_ctol, 4, 0)
        layout.addWidget(self.sb_ctol, 4, 1)
        layout.addWidget(self.gp_options, 5, 0, 1, 2)
        layout.addWidget(self.gp_compute, 6, 0, 1, 2)
        layout.addWidget(self.bt_cancel, 7, 1)
        self.setLayout(layout)

        # connect signals
        self.bt_p.clicked.connect(self.emit_part_selection)
        self.bt_run.clicked.connect(self.emit_run)
        self.bt_cancel.clicked.connect(self.hide)
        self.cb_merge_by_part.stateChanged.connect(self.change_merge_by_part)
        self.cb_merge_by_proximity.stateChanged.connect(self.change_merge_by_proximity)

    # signals emitters
    def emit_part_selection(self):
        self.partSelection.emit()

    def emit_run(self):
        # get the values
        gap = self.sb_gap.value()
        ctol = self.sb_ctol.value()
        merge_by_part = self.cb_merge_by_part.isChecked()
        merge_by_proximity = self.cb_merge_by_proximity.isChecked()
        self.contactRun.emit(gap,ctol,merge_by_part,merge_by_proximity)
        
    @pyqtSlot(list)
    def set_parts(self, parts):
        self.partSelected = parts
        nb_parts = len(parts)
        if nb_parts ==0 :
            msg = 'Please select at least 2 parts !'
        else:
            msg = f'{nb_parts} parts selected'
        self.le_p.setText(msg)

    @pyqtSlot(int)
    def change_merge_by_part(self):
        if self.cb_merge_by_part.isChecked():
            self.cb_merge_by_proximity.setChecked(False)
    
    @pyqtSlot(int)
    def change_merge_by_proximity(self):
        if self.cb_merge_by_proximity.isChecked():
            self.cb_merge_by_part.setChecked(False)

    @pyqtSlot(int)
    def on_progress(self, progress):
        self.pbar.setValue(progress)

    @pyqtSlot()
    def on_completed(self):
        self.pbar.setValue(0)
        self.le_p.setText("Please select at least 2 parts")