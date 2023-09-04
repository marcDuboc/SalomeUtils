# -*- coding: utf-8 -*-
# Generate Contacts between parts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import os
import inspect
import sys
import itertools
import re
import json
import time
import numpy as np
import GEOM
import salome
from salome.geom import geomBuilder, geomtools

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5.QtWidgets import QDockWidget

#for debbuging
from importlib import reload

# add contact module
try:
    reload(sys.modules['contact.data', 'contact.geom', 'contact.tree', 'contact.interface'])
    from contact.data import ContactManagement
    from contact.geom import ParseShapesIntersection
    from contact.tree import Tree
    from contact.interface import ContactGUI
    
except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)
    from contact.data import ContactManagement
    from contact.geom import ParseShapesIntersection
    from contact.tree import Tree
    from contact.interface import ContactGUI

# Detect current study
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")
salome.salome_init()

DEBUG_FILE = 'E:\GitRepo\SalomeUtils\debug\d.txt'

class ContactAuto(QObject):
    compound_selected = pyqtSignal(str)
    parts_selected = pyqtSignal(list)

    def __init__(self):
        super(ContactAuto, self).__init__()

        self.Gui = ContactGUI()
        self.Tree = Tree()
        self.Contact = ContactManagement()
        self.Intersect = ParseShapesIntersection()

        self.parts =[]

        self.compound_selected.connect(self.Gui.on_compound_selected)
        self.Gui.load_compound.connect(self.select_compound)
        
    def __del__(self):
        del self.Tree
        del self.Contact
        del self.Gui
              
    @pyqtSlot()
    def select_compound(self):
        selCount = salome.sg.SelectedCount()
        if selCount == 0:
            self.compound_selected.emit("No compound selected!")
            return
        elif selCount > 1:
            self.compound_selected.emit("Select only one compound!")
            return
        else:
            id = salome.sg.getSelected(0)
            name = salome.IDToObject(id).GetName()
            self.compound_selected.emit(name+ '\t'+ id)

            # parse for existing contacts
            self.Tree.get_objects(id)
            existing_contact = self.Tree.parse_for_contact()
            print('existing contact',existing_contact)

            with open(DEBUG_FILE, 'a') as f:
                f.write(time.ctime())
                f.write(str(existing_contact))
                f.write('\n')
                
            # add existing contacts to contactManager
            self.Contact.create_from_tree(existing_contact)

            # update table
            self.Gui.set_data(self.Contact.to_table_model())

            #connect signals
            self.Gui.swapItem.swap.connect(self.Contact.swap_master_slave_by_id)
            self.Gui.hideShowItem.hideShow.connect(self.Contact.hideshow_by_id)
            self.Gui.deleteItem.delContact.connect(self.Contact.delete_by_id)
            self.Gui.typeItem.changeType.connect(self.Contact.change_type_by_id)
            self.Gui.autoWindow.partSelection.connect(self.select_parts)
            self.parts_selected.connect(self.Gui.autoWindow.set_parts)
            self.Gui.autoWindow.contactRun.connect(self.process_contact)

    @pyqtSlot()
    def select_parts(self):
        self.parts =[]
        selCount = salome.sg.SelectedCount()
        part_ids=[]
        if selCount < 2:
            self.parts_selected.emit([])

        elif selCount > 1:
            for i in range(selCount):
                id = salome.sg.getSelected(i)
                part_ids.append(id)
                self.parts.append(id)
            self.parts_selected.emit(part_ids)
        with open(DEBUG_FILE, 'a') as f:
            f.write(time.ctime())
            f.write("select_parts\t")
            f.write(str(self.parts))
            f.write('\n')

    @pyqtSlot(float, float, bool)
    def process_contact(self, tol, angle, isAuto):
        contact_pairs = []
        combine = list(itertools.combinations(self.parts, 2))

        for i in range(len(combine)):
            res, candidate = self.Intersect.intersection(combine[i][0], combine[i][1],gap=tol)
            if res:
                for c in candidate:
                    contact_pairs.append(c)

        # add new contacts to contactManager
        for i in range(len(contact_pairs)):
            self.Contact.create_from_intersection(contact_pairs[i][0][0], contact_pairs[i][0][1],contact_pairs[i][1][0], contact_pairs[i][1][1])

        # update table
        self.Gui.set_data(self.Contact.to_table_model())

    
class MyDockWidget(QDockWidget):
    widgetClosed = pyqtSignal()

    def closeEvent(self, event):
        self.widgetClosed.emit()
        super(MyDockWidget, self).closeEvent(event)

contact_auto_instance = ContactAuto()

def delete_contact_auto_instance():
    global contact_auto_instance
    del contact_auto_instance 
    print("ContactAuto instance deleted.")

d = MyDockWidget()
d.setWidget(contact_auto_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle("3D Contacts")
d.setGeometry(600, 300, 400, 400)
d.widgetClosed.connect(delete_contact_auto_instance)

d.show()




     