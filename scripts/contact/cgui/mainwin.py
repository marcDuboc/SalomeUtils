# -*- coding: utf-8 -*-
# GUI module for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import time
import inspect
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout,QLabel, QLineEdit,QTableView, QGroupBox, QHBoxLayout,QCheckBox,QSlider,QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from contact.cgui.abstract import TypeDelegate, DeleteDelegate, SwapDelegate, HideShowDelegate, TableModel
from contact.cgui.manualwin import ManualWindows
from contact.cgui.autowin import AutoWindows
from contact.cgui import IMG_PATH

import salome
salome.salome_init()
gg = salome.ImportComponentGUI("GEOM")

class ContactGUI(QWidget):

    # define custom signals
    load_compound = pyqtSignal()
    closing = pyqtSignal()
    export_contact = pyqtSignal(str,str)

    def __init__(self):
        super(ContactGUI, self).__init__()
        self._data = []
        self.init_UI()
        self.autoWindow = AutoWindows()
        self.autoWindow.setWindowFlags(self.autoWindow.windowFlags() | Qt.WindowStaysOnTopHint)
        self.autoWindow.hide()
        self.manualWindow = ManualWindows()
        self.manualWindow.setWindowFlags(self.manualWindow.windowFlags() | Qt.WindowStaysOnTopHint)
        self.manualWindow.hide()
        self.compound_parts = []
        self.file_name = ''


    def init_UI(self):
        # Table model
        self.model = TableModel(self._data)
        self.typeItem = TypeDelegate()
        self.deleteItem = DeleteDelegate()
        self.swapItem = SwapDelegate()
        self.hideShowItem = HideShowDelegate()

        self.table_view = QTableView(self)
        self.table_view.setItemDelegateForColumn(2, self.typeItem)
        self.table_view.setItemDelegateForColumn(5, self.deleteItem)
        self.table_view.setItemDelegateForColumn(4, self.swapItem)
        self.table_view.setItemDelegateForColumn(3, self.hideShowItem)
        self.table_view.setSizeAdjustPolicy(QTableView.AdjustToContents)
        self.table_view.resizeColumnsToContents()

        #=======================
        # select root component
        self.l_root = QLabel("Root compound: ", self)
        self.lb_root = QLineEdit()
        self.lb_root.setReadOnly(True)
        self.lb_root.setText("Please select a compound")
        self.bt_root = QPushButton()
        self.bt_root.setIcon(QIcon(os.path.join(IMG_PATH,'input.png')))
        

        #=======================
        # create groupbox for parts
        self.gp_parts = QGroupBox("Parts", self)
        # add checkbox for parts display
        self.cb_parts = QCheckBox("Display", self)
        self.cb_parts.setChecked(True)
        # add slider for parts transparency
        self.l_transparency = QLabel("Transparency: ", self)
        self.sl_transparency = QSlider(Qt.Horizontal)
        self.sl_transparency.setMinimum(0)
        self.sl_transparency.setMaximum(100)
        self.sl_transparency.setValue(80)
        self.sl_transparency.setTickPosition(QSlider.TicksBelow)
        self.sl_transparency.setTickInterval(10)
        # put the checkbox in a vertical layout
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.cb_parts)
        self.vbox.addWidget(self.l_transparency)
        self.vbox.addWidget(self.sl_transparency)
        self.gp_parts.setLayout(self.vbox)

        #=======================
        # group for contact creation
        self.gp_contact = QGroupBox("Create contact", self)
        # create buttons for contact creation
        self.bt_contact_auto = QPushButton("Auto", self)
        self.bt_contact_manual = QPushButton("Manual", self)
        # put the bouton in a horizontal layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.bt_contact_auto)
        self.hbox.addWidget(self.bt_contact_manual)
        self.gp_contact.setLayout(self.hbox)
        # create button OK	
        btnOK = QPushButton('Quit')

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
        self.cb_export_json.setChecked(True)
        #create checkbox for export file comm
        self.cb_export_comm = QCheckBox("Aster format (*.comm)", self)
        self.cb_export_comm.setChecked(False)

        #add checkbox in a horizontal layout
        self.hbox_0 = QHBoxLayout()
        self.hbox_0.addWidget(self.cb_export_json)
        self.hbox_0.addWidget(self.cb_export_comm)

        # put the bouton in a horizontal layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.le_export)
        self.hbox.addWidget(self.bt_export)

        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox_0)
        self.vbox.addLayout(self.hbox)
        self.gp_export.setLayout(self.vbox)

        #=======================
        # layout
        layout = QGridLayout()
        layout.addWidget(self.l_root, 1, 0)
        layout.addWidget(self.lb_root, 2, 0)
        layout.addWidget(self.bt_root, 2, 1)
        layout.addWidget(self.table_view, 3, 0, 1, 2)
        layout.addWidget(self.gp_parts, 4, 0, 1, 2)
        layout.addWidget(self.gp_contact, 5, 0, 1, 2)
        layout.addWidget(self.gp_export, 6, 0, 1, 2)
        layout.addWidget(btnOK, 7, 1)
        self.setLayout(layout)

        # connect signals
        self.bt_root.clicked.connect(self.emit_load_compound)
        self.bt_contact_auto.clicked.connect(self.openAutoWindow)
        self.bt_contact_manual.clicked.connect(self.openManualWindow)
        btnOK.clicked.connect(self.close)
        self.cb_parts.stateChanged.connect(self.display_compound_part)
        self.sl_transparency.valueChanged.connect(self.set_compound_part_transparency)
        self.bt_export.clicked.connect(self.select_file)
        self.cb_export_json.stateChanged.connect(self.on_change_export_json)
        self.cb_export_comm.stateChanged.connect(self.on_change_export_comm)
        
    # slots
    @pyqtSlot(str)
    def on_compound_selected(self, master_compound_name):
        self.lb_root.setText(master_compound_name)

    @pyqtSlot(list)
    def set_compounds_parts(self, parts):
        self.compound_parts = parts 
        for p in parts:
            salome.sg.Display(p)
            gg.setTransparency(p,0.8)

    @pyqtSlot(int)
    def set_compound_part_transparency(self, transparency):
        for p in self.compound_parts:
            gg.setTransparency(p,transparency/100)

    @pyqtSlot(int)
    def display_compound_part(self, display):
        for p in self.compound_parts:
            if display>0:
                salome.sg.Display(p)
                gg.setTransparency(p,self.sl_transparency.value()/100)
            else:
                gg.eraseGO(p)

    @pyqtSlot()
    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        name, _ = QFileDialog.getSaveFileName(self, "Export file","","Json (*.json);Comm (*.comm)", options=options)
        if name:
            if self.cb_export_comm.isChecked():
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
            
            if self.cb_export_comm.isChecked():
                export = 'ASTER'
            else:
                export = 'RAW'
            self.export_contact.emit(name,export)

    @pyqtSlot(int)
    def on_change_export_json(self):
        if self.cb_export_json.isChecked():
            self.cb_export_comm.setChecked(False)
        else:
            self.cb_export_comm.setChecked(True)

    @pyqtSlot(int)
    def on_change_export_comm(self):
        if self.cb_export_comm.isChecked():
            self.cb_export_json.setChecked(False)
        else:
            self.cb_export_json.setChecked(True)

    def resizeEvent(self, event):
         self.table_view.resizeColumnsToContents()

    def closeEvent(self, event):
        print("Fermeture de la fenêtre, suppression des instances...")
        self.closing.emit()
        event.accept()  # Ferme la fenêtre """

    # signals emitters
    def emit_load_compound(self):
        self.load_compound.emit()

    def set_data(self, data):
        # add 2 extra columns for the button (delete)
        for d in range(len(data)):
            data[d].append('')
            data[d].append('')
        if len(data) > 0:
            self.model = TableModel(data)
            self.table_view.setModel(self.model)  

    def openAutoWindow(self):
        self.autoWindow.show()

    def openManualWindow(self):
        self.manualWindow.show()

          
    
