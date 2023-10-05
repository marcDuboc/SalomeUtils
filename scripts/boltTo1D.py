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

# add contact module
try:
    reload(sys.modules['bolt.shape', 'bolt.aster', 'bolt.properties'])
    from bolt.cgui.mainwin import Bolt1DGUI
    from bolt.tree import Tree
    from bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from bolt.properties import get_properties
    from bolt.aster import MakeComm
    
except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)
    from bolt.cgui.mainwin import Bolt1DGUI
    from bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from bolt.properties import get_properties
    from bolt.aster import MakeComm


StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Geompy = geomBuilder.New()

class BoltTo1D(QObject):
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
        super(BoltTo1D, self).__init__()
        self.Gui = Bolt1DGUI()
        self.Tree = Tree()
        self.Parse= Parse()

        self.parts =[]
        self.compound_parts = []
        self.manual_selection = dict(source=None, target=None)

    def __del__(self):
        del self.Tree
        del self.Parse
        del self.Gui

    # Slot ====================================================================          
    @pyqtSlot()
    def select_compound(self):
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
    def parse_all(self):
        pass

    @pyqtSlot()
    def parse_selected(self):
        pass

    def find_existing_bolt(self):
        pass