# -*- coding: utf-8 -*-
# GUI module for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import time
import inspect
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout,QLabel, QLineEdit,QTableView, QGroupBox, QHBoxLayout,QCheckBox,QSlider,QFileDialog,QHeaderView, QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from common.bolt.bgui.abstract import TypeDelegate, DeleteDelegate, SwapDelegate, HideShowDelegate, TableModel

#from common.bolt.bgui.manualwin import ManualWindows
#from common.bolt.bgui.autowin import AutoWindows
from common import IMG_PATH

import salome
salome.salome_init()
gg = salome.ImportComponentGUI("GEOM")

class BoltGUI(QWidget):

    # define custom signals
    select = pyqtSignal()
    parse = pyqtSignal()

    closing = pyqtSignal()
    export_contact = pyqtSignal(str,str,bool)

    def __init__(self):
        super(BoltGUI, self).__init__()
        self._data = []
        self.init_UI()
        self.file_name = ''

    def init_UI(self):
        # Table model
        self.model = TableModel(self._data)
        #self.typeItem = TypeDelegate()
        self.deleteItem = DeleteDelegate()
        #self.swapItem = SwapDelegate()
        #self.hideShowItem = HideShowDelegate()

        self.table_view = QTableView(self)
        #self.table_view.setItemDelegateForColumn(2, self.typeItem)
        self.table_view.setItemDelegateForColumn(7, self.deleteItem)
        #self.table_view.setItemDelegateForColumn(6, self.swapItem)
        #self.table_view.setItemDelegateForColumn(5, self.hideShowItem)
                
        #=======================
        # group for contact creation
        self.gp_bolt = QGroupBox("Search Bolt", self)

        #create options for bolt search
        self.cb_screw = QCheckBox("screw <-> [hole | nut]", self)
        self.cb_screw.setChecked(True)
        self.cb_hole= QCheckBox("hole <-> hole", self)

        # add label options 
        self.gp_options = QGroupBox("Options", self)
        #self.lb_options.setAlignment(Qt.AlignCenter)

        #create vbox for bolt options
        self.vbox_0 = QVBoxLayout()
        self.vbox_0.addWidget(self.cb_screw)
        self.vbox_0.addWidget(self.cb_hole)

        #add  bolt options to groupbox
        self.gp_options.setLayout(self.vbox_0)
        
        self.le_input = QLineEdit()    
        self.le_input.setReadOnly(True)
        self.le_input.setText("select a compound or several parts")
        self.bt_input = QPushButton()
        self.bt_input.setIcon(QIcon(os.path.join(IMG_PATH,'input.png')))

        self.hbox_1 = QHBoxLayout()
        self.hbox_1.addWidget(self.bt_input)
        self.hbox_1.addWidget(self.le_input)

        #create process button
        self.bt_search = QPushButton("Search", self)

        # creater progress bar
        self.pb_search = QProgressBar(self)
        self.pb_search.setMinimum(0)
        self.pb_search.setMaximum(100)
        self.pb_search.setValue(0)
        self.pb_search.setTextVisible(True)

        #create hbox for progress bar and button
        self.searchbox = QHBoxLayout()
        self.searchbox.addWidget(self.bt_search)
        self.searchbox.addWidget(self.pb_search)

        self.vbox_1 = QVBoxLayout()
        self.vbox_1.addLayout(self.hbox_1)
        self.vbox_1.addWidget(self.gp_options)
        self.vbox_1.addLayout(self.searchbox)
        
        #self.vbox_1.addWidget(self.searchbox)
        self.gp_bolt.setLayout(self.vbox_1)

        #=======================
        # add groupbox for export
        self.gp_export = QGroupBox("Export", self)
        # create lidedit for export path
        self.le_export = QLineEdit()    
        self.le_export.setReadOnly(True)
        self.le_export.setText("Please select a path")

        # create button for export
        self.bt_export = QPushButton()
        self.bt_export.setIcon(QIcon(os.path.join(IMG_PATH,'save.png')))
        # create checkbox for export file json
        self.cb_export_json = QCheckBox("Raw format (*.json)", self)
        self.cb_export_json.setChecked(False)

        #create groupbox for export ASTER comm
        self.gp_export_comm = QGroupBox("Aster format (*.comm)", self)
        self.gp_export_comm.setCheckable(True)
        self.gp_export_comm.setChecked(True)

        #create checkbox for options exports ASTER
        self.cb_export_aster_regroup= QCheckBox("Regroup masters on same slave (LIAISON_MAIL)", self)
        self.cb_export_aster_regroup.setChecked(True)

        #create hbox for aster options
        self.hbox_2 = QHBoxLayout()
        self.hbox_2.addWidget(self.cb_export_aster_regroup)
        self.gp_export_comm.setLayout(self.hbox_2)

        #add checkbox in a horizontal layout
        self.hbox_3 = QVBoxLayout()
        self.hbox_3.addWidget(self.cb_export_json)
        self.hbox_3.addWidget(self.gp_export_comm)

        # put the bouton in a horizontal layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.le_export)
        self.hbox.addWidget(self.bt_export)

        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox_3)
        self.vbox.addLayout(self.hbox)
        self.gp_export.setLayout(self.vbox)

        #=======================
        # create button OK	
        btnQuit = QPushButton('Quit')


        #=======================
        # layout
        layout = QGridLayout()
        layout.addWidget(self.table_view, 1, 0, 1, 2)
        layout.addWidget(self.gp_bolt, 3, 0, 1, 2)
        layout.addWidget(self.gp_export, 4, 0, 1, 2)
        layout.addWidget(btnQuit, 5, 1)
        self.setLayout(layout)

        # connect signals
        self.bt_input.clicked.connect(self.select.emit)
        self.bt_search.clicked.connect(self.parse.emit)

        self.bt_export.clicked.connect(self.select_file)
        self.cb_export_json.stateChanged.connect(self.on_change_export_json)
        self.gp_export_comm.toggled.connect(self.on_change_export_comm)
        btnQuit.clicked.connect(self.close)

        
    # slots
    @pyqtSlot(str,str)
    def on_selection(self, master_compound_name, color='black'):
        self.le_input.setText(master_compound_name)
        self.le_input.setStyleSheet(f"color: {color};")

    @pyqtSlot(int)
    def on_progress(self, value):
        self.pb_search.setValue(value)
        self.pb_search.setFormat(f"{value}%")

    @pyqtSlot()
    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        name, _ = QFileDialog.getSaveFileName(self, "Export file","","Json (*.json);Comm (*.comm)", options=options)
        if name:
            if self.gp_export_comm.isChecked():
                export = 'ASTER'
                format = '.comm'
            else:
                export = 'RAW'
                format = '.json'

            # chck if the file has the right extension
            if not name.endswith(format):
                name.split('.')[0]
                name = name+format
            
            self.le_export.setText(name)
            self.file_name = name
            
            if self.gp_export_comm.isChecked():
                export = 'ASTER'
            else:
                export = 'RAW'
                
            self.export_contact.emit(name,export,self.cb_export_aster_regroup.isChecked())

    @pyqtSlot(int)
    def on_change_export_json(self):
        if self.cb_export_json.isChecked():
            self.gp_export_comm.setChecked(False)
        else:
            self.gp_export_comm.setChecked(True)

    @pyqtSlot(bool)
    def on_change_export_comm(self):
        if self.gp_export_comm.isChecked():
            self.cb_export_json.setChecked(False)
        else:
            self.cb_export_json.setChecked(True)

    #def resizeEvent(self, event):
    #     self.table_view.resizeColumnsToContents()

    def closeEvent(self, event):
        print("Fermeture de la fenetre, suppression des instances...")
        self.closing.emit()
        event.accept()  # Ferme la fenêtre """

    # signals emitters
    def emit_load_compound(self):
        self.load_compound.emit()

    def set_data(self, data):
        # add 2 extra columns for the button (delete)
        for d in range(len(data)):
            data[d].append('')

        if len(data) > 0:
            self.model = TableModel(data)
            self.table_view.setModel(self.model)  

            header = self.table_view.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.Stretch)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

    #def openAutoWindow(self):
    #    self.autoWindow.show()

    #def openManualWindow(self):
    #    self.manualWindow.show()

          
    
