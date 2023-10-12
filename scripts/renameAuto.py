# -*- coding: utf-8 -*-
# rename parts and create groups
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import salome
from salome.geom import geomBuilder,geomtools

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtCore, QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QGridLayout, QLabel, QTextBrowser, QPushButton, QDialogButtonBox, QDockWidget
from PyQt5.QtCore import Qt

geompy = geomBuilder.New()
salome.salome_init()

class Rename(QWidget):
    def __init__(self):
        super(Rename, self).__init__()
        self.initUI()
        self.selectParts()
        self.partsID = list()
        self.study = geomtools.GeomStudyTools()
        
    def __del__(self):
        return
    
    def renameObject(self, id, name):
        obj = salome.IDToObject(id)
        sobj=salome.IDToSObject(id)
        obj.SetName(name)
        self.study.editor.setName(sobj, name)
        
    def getPartsName(self,id):
        sobj=salome.IDToSObject(id)
        return sobj.GetName()
    
    def initUI(self):
        # parts selected 
        self.l_parts = QLabel("Parts selected: ", self)
        self.tb_parts = QTextBrowser()
        self.pb_loadpart = QPushButton()
        self.pb_loadpart.setText("Load selected")
        self.tb_parts.clear()

        # Adjust Gap
        self.l_prefix = QLabel("prefix: ")
        self.prefix  = QLineEdit()
        self.prefix.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[A-Za-z0-9_]+")))
        self.prefix.setText("P")

        # create group option        
        self.make_grp = QCheckBox("  create Group ",self)
        self.make_grp.setChecked(Qt.Checked)

        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_parts, 1, 0)
        layout.addWidget(self.tb_parts, 2, 0)
        layout.addWidget(self.pb_loadpart, 3, 0)
        layout.addWidget(self.l_prefix, 4, 0)
        layout.addWidget(self.prefix, 5, 0)
        layout.addWidget(self.make_grp, 6, 0)
        layout.addWidget(self.okbox, 8, 0)
        self.setLayout(layout)

        # Connectors:
        self.okbox.accepted.connect(self.rename)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadpart.clicked.connect(self.selectParts)
        
    def selectParts(self):
        self.tb_parts.clear()
        selCount = salome.sg.SelectedCount()
        selID = list()

        try:
          for i in range(0, selCount):
            id=salome.sg.getSelected(i)
            selID.append(id)
            self.tb_parts.append(self.getPartsName(id))
          self.partsID = selID

        except:
            QMessageBox.critical(None,'Error',"error in selected parts",QMessageBox.Abort)

          
    def rename(self):
      # check if parts are selected
      if len(self.partsID) == 0:
        QMessageBox.critical(None,'Error',"No parts selected",QMessageBox.Ok)
        return

      # get the prefix
      prefix = self.prefix.text()
      if prefix == "":
        prefix = "P"

      # rename parts
      for i in range(0, len(self.partsID)):
        name = prefix+str(i+1)
        self.renameObject(self.partsID[i], name)
        
        # create group
        if self.make_grp.isChecked():
          try:
            goemObj = salome.IDToObject(self.partsID[i])
            solid_grp = geompy.SubShapeAll(goemObj, geompy.ShapeType["SOLID"])

            if len(solid_grp)>0:
              group = geompy.CreateGroup(goemObj, geompy.ShapeType["SOLID"])
              SolidID = geompy.GetSubShapeID(goemObj, solid_grp[0])
              geompy.AddObject(group, SolidID)
              geompy.addToStudyInFather( goemObj, group, name )

          except:
            QMessageBox.critical(None,'Error',"error creating group",QMessageBox.Ok)

      if salome.sg.hasDesktop():
        salome.sg.updateObjBrowser()
        QMessageBox.information(None,'Information',str(len(self.partsID))+" parts renamed",QMessageBox.Ok)
        self.close()


    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(Rename())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Parts Rename ")
d.setGeometry(600, 300, 400, 400)
d.show()
