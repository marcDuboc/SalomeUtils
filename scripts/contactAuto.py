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
        self.compound_selected.connect(self.Gui.on_compound_selected)
        self.Gui.load_compound.connect(self.select_compound)

    @pyqtSlot()
    def select_compound(self):
        self.compound_selected.emit("Example")


contact_auto_instance = ContactAuto()

d = QDockWidget()
d.setWidget(contact_auto_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
#d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" 3D Contacts ")
d.setGeometry(600, 300, 400, 400)
d.show()


     