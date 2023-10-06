# -*- coding: utf-8 -*-
# Generate Contacts between parts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 05/10/2023

import os
import sys
import inspect
import re
import itertools
import time
import GEOM
import salome
from salome.kernel.studyedit import getStudyEditor
from salome.geom import geomtools, geomBuilder

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5.QtWidgets import QDockWidget

#for debbuging
from importlib import reload

try:
    modules = ['common.bolt.shape', 'common.bolt.treeBolt', 'common.properties','common.bolt.aster','common.bolt.bgui.mainwin']
    for m in modules:
        if m in sys.modules:
            reload(sys.modules[m])

    from common.bolt.bgui.mainwin import BoltGUI
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from common.properties import get_properties
    from common.bolt.aster import MakeComm
    from common import logging
    
except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)

    from common.bolt.bgui.mainwin import BoltGUI
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from common.properties import get_properties
    from common.bolt.aster import MakeComm
    from common import logging

StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Geompy = geomBuilder.New()

class Bolt1D(QObject):
    pattern_bolt = re.compile(r'_B\d{1,3}(_-?\d+(\.\d+)?)+')

    compound_selected = pyqtSignal(str,str)

    # auto parts signals
    parts_selected = pyqtSignal(list)
    existing_parts = pyqtSignal(list)

    parse_progess = pyqtSignal(int)
    parse_completed = pyqtSignal()

    # manual contact signals
    manual_bolt_selected= pyqtSignal(int, bool,str,str)
    manual_bolt_validated = pyqtSignal(bool)

    def __init__(self):
        super(Bolt1D, self).__init__()
        self.Gui = BoltGUI()
        self.Tree = TreeBolt()
        self.Parse= Parse()
        self.roots ="0:1:1"

        self.parts =[]
        self.compound_parts = []
        self.manual_selection = dict(source=None, target=None)

        # get the existing virtual bolts
        self.bolts = self.Tree.parse_for_bolt()
        if self.bolts:
            b_list = self.virtual_bolt_to_table()
            self.Gui.set_data(b_list)

    def __del__(self):
        del self.Tree
        del self.Parse
        del self.Gui
    
    # Slot ==================================================================== 
    
    def virtual_bolt_to_table(self):
        bolt_array= []
        for b in self.bolts:
            logging.info(b)
            bolt_array.append([b.id_instance,
                               b.radius,
                               b.start_radius,
                               b.end_radius,
                               b.start_height,
                               b.end_height,
                               b.preload])

        return bolt_array
             
    @pyqtSlot()
    def select(self):
        selCount = salome.sg.SelectedCount()
        if selCount == 0:
            self.compound_selected.emit("No compound selected!","red")
            return
        
        elif selCount > 1:
            self.compound_selected.emit("Select only one compound!","red")
            return
        
        else:
            id = salome.sg.getSelected(0)
            obj = salome.IDToObject(id)

            try :
                otype = obj.GetType()
                name = salome.IDToObject(id).GetName()

            except:
                self.compound_selected.emit("Please Select a compound!","red")
                return
            
            if otype not in (27,1,):
                self.compound_selected.emit("Please Select a compound!","red")
                return
            
            else:
                self.compound_selected.emit(name+ '\t'+ id,"green")

                # parse for existing contacts
                self.Tree.parse_tree_objects(id)

                # emit existing parts to Gui
                self.compound_parts =[x.get_sid() for x in self.Tree.get_parts()]
                self.existing_parts.emit(self.compound_parts)

                # update table
                self.Gui.set_data(self.Contact.to_table_model())

    @pyqtSlot()
    def parse_selected(self):
        pass

class MyDockWidget(QDockWidget):
    widgetClosed = pyqtSignal()

    def closeEvent(self, event):
        self.widgetClosed.emit()
        super(MyDockWidget, self).closeEvent(event)

bolt_instance = Bolt1D()

def delete_bolt_instance():
    global bolt_instance
    del bolt_instance

d = MyDockWidget()
d.setWidget(bolt_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle("Bolt 1D")
d.setGeometry(600, 300, 400, 600)
d.widgetClosed.connect(delete_bolt_instance)

d.show()