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
import numpy as np
import GEOM
import salome
from salome.geom import geomBuilder, geomtools

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


class ContactAuto(QObject):
    compound_selected = pyqtSignal(str)

    def __init__(self):
        super(ContactAuto, self).__init__()

        self.Gui = ContactGUI()
        self.Tree = Tree()
        self.Contact = ContactManagement()

        self.compound_selected.connect(self.Gui.on_compound_selected)
        self.Gui.load_compound.connect(self.select_compound)

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
            self.Tree.parse_for_contact()

            # add existing contacts to contactManager
            contacts = self.Tree.contacts
            for _,v in contacts.items():
                # get the id of the contact
                v[0]
                self.Contact.create_from_tree(v[0],v[1])

            # update table
            self.contact_pairs_to_tabelmodel(self.Contact.get_pairs())
    
    def contact_pairs_to_tabelmodel(self, contact_pairs:list()):
        model=[]

            
contact_auto_instance = ContactAuto()

d = QDockWidget()
d.setWidget(contact_auto_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
#d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" 3D Contacts ")
d.setGeometry(600, 300, 400, 400)
d.show()


     