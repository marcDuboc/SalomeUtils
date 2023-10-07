# -*- coding: utf-8 -*-
# Generate Contacts between parts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import os
import sys
import inspect
import itertools
import time
import GEOM
import salome
from salome.geom import geomBuilder

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5.QtWidgets import QDockWidget

#for debbuging
from importlib import reload

# add contact module
try:
    reload(sys.modules['contact.data', 'contact.geom', 'contact.tree', 'contact.interface'])
    from common.contact.data import ContactManagement,GroupItem
    from common.contact.intersect import ParseShapesIntersection
    from common.contact.contactTree import ContactTree
    from common.contact.cgui.mainwin import ContactGUI
    from common.contact.aster.comm import MakeComm
    from common import logging
    
except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)
    from common.contact.data import ContactManagement,GroupItem
    from common.contact.intersect import ParseShapesIntersection
    from common.contact.contactTree import ContactTree
    from common.contact.cgui.mainwin import ContactGUI
    from common.contact.aster.comm import MakeComm
    from common import logging

# Detect current study
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")
salome.salome_init()

class ContactAuto(QObject):
    compound_selected = pyqtSignal(str,str)

    # auto contact signals
    parts_selected = pyqtSignal(list)
    existing_parts = pyqtSignal(list)
    progess_autocontact = pyqtSignal(int)
    autocontact_completed = pyqtSignal()

    # manual contact signals
    manual_grp_validated = pyqtSignal(int, bool,str,str)
    manual_contact_validated = pyqtSignal(bool)

    def __init__(self):
        super(ContactAuto, self).__init__()

        self.Gui = ContactGUI()
        self.Tree = ContactTree()
        self.Contact = ContactManagement()
        self.Intersect = ParseShapesIntersection()

        self.parts =[]
        self.compound_parts = []
        self.manual_selection = dict(grp1=None, grp2=None)

        self.compound_selected.connect(self.Gui.on_compound_selected)
        self.Gui.load_compound.connect(self.select_compound)
        self.existing_parts.connect(self.Gui.set_compounds_parts)
        self.Gui.export_contact.connect(self.export_contact)
        
    def __del__(self):
        del self.Tree
        del self.Contact
        del self.Gui
        del self.Intersect

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
                existing_contact = self.Tree.get_contacts()

                # emit existing parts to Gui
                self.compound_parts =[x.get_sid() for x in self.Tree.get_parts()]
                self.existing_parts.emit(self.compound_parts)

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
                self.progess_autocontact.connect(self.Gui.autoWindow.on_progress)
                self.autocontact_completed.connect(self.Gui.autoWindow.on_completed)
                self.Gui.manualWindow.select_grp.connect(self.selected_grp)
                self.manual_grp_validated.connect(self.Gui.manualWindow.on_grp_validated)
                self.Gui.manualWindow.create_contact.connect(self.create_manual_grp)
            
    
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
                if id in self.compound_parts:
                    part_ids.append(id)
                    self.parts.append(id)
            self.parts_selected.emit(part_ids)

    @pyqtSlot(float, float, bool,bool,bool)
    def process_contact(self, gap, angle, merge_by_part, merge_by_proximity, avoid_adjacent_slaves:bool=False):

        combine = list(itertools.combinations(self.parts, 2))
        nb_comb = len(combine)
        self.progess_autocontact.emit(1)

        for i in range(len(combine)):
            # emit progress
            progress = int((i)/nb_comb*100)-1
            if avoid_adjacent_slaves:
                progress = int((i)/nb_comb*100)-11
            self.progess_autocontact.emit(progress)
            
            res, candidate = self.Intersect.intersection(combine[i][0], combine[i][1],gap=gap,tol=angle,merge_by_part=merge_by_part, merge_by_proximity=merge_by_proximity)

            if res:
                # add new contacts to contactManager
                for c in candidate:
                    grp1 = GroupItem()
                    grp2 = GroupItem()
                    grp1.create(c[0][0], c[0][1])
                    grp2.create(c[1][0], c[1][1])

                    self.Contact.create_from_groupItem(grp1, grp2)

        # debug some issues with this function
        if avoid_adjacent_slaves:
            self.Contact.check_adjacent_slave_group()

        # update table
        self.Gui.set_data(self.Contact.to_table_model())

        # emit progress 
        self.progess_autocontact.emit(100)

        # emit completed
        self.autocontact_completed.emit()

        # clear parts
        self.parts.clear()

        # close auto window
        self.Gui.autoWindow.close()

    @pyqtSlot(str,str,bool)
    def export_contact(self, filename,export, bonded_regroup_master:bool=True):
        if export == "RAW":
            self.Contact.export(filename)
            
        elif export == "ASTER":
            data = []
            for c in self.Contact.get_contacts():
                data.append(c.to_dict_for_export())
            Mk = MakeComm(data)
            with open(filename, 'w') as f:
                f.write(Mk.process(bonded_regroup_master))

    # manual selection of groups
    @pyqtSlot(int)
    def selected_grp(self,index:int):
        selCount = salome.sg.SelectedCount()
        id = salome.sg.getSelected(0)
        obj = salome.IDToObject(id)
        grp = ('grp1','grp2')
        logging.debug("selected_grp: {}".format(index))
        if selCount == 1:
            if obj.GetType()==37 and obj.GetShapeType()._v== 4:
                complement = lambda x: 0 if x==1 else 1
                complement_index = complement(index)

                if self.manual_selection[grp[complement_index]] == id:
                    self.manual_grp_validated.emit(index,False,msg="Please select a different Group!",color="red")
                
                else:
                    self.manual_selection[grp[index]] = id
                    self.manual_grp_validated.emit(index,True,msg="Ok",color="green")

            else:
                self.manual_grp_validated.emit(index,False,msg="Please select one face group!",color="red")
        else:
            self.manual_grp_validated.emit(index,False,msg="Please select only one group!",color="red")

    @pyqtSlot()
    def create_manual_grp(self):
        if self.manual_selection['grp1'] is not None or self.manual_selection['grp2'] is not None:
            res = self.Contact.create_from_groupsID(self.manual_selection['grp1'], self.manual_selection['grp2'])

            for k in self.manual_selection.keys():
                self.manual_selection[k] = None

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

d = MyDockWidget()
d.setWidget(contact_auto_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle("3D Contacts")
d.setGeometry(600, 300, 400, 600)
d.widgetClosed.connect(delete_contact_auto_instance)

d.show()




     