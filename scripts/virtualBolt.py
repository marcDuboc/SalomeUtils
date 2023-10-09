# -*- coding: utf-8 -*-
# Generate virtual bolt from geometry
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

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt, QVariant
from PyQt5.QtWidgets import QDockWidget,QMessageBox

#for debbuging
from importlib import reload

try:
    modules = ['common.bolt.shape', 'common.bolt.treeBolt', 'common.properties','common.bolt.aster','common.bolt.bgui.mainwin']
    for m in modules:
        if m in sys.modules:
            reload(sys.modules[m])

    from common.bolt.bgui.mainwin import BoltGUI
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.shape import Method, Parse, Nut, Screw, Thread, pair_screw_nut_threads,pair_holes , create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from common.properties import get_properties
    from common.bolt.aster import MakeComm
    from common import logging

except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)

    from common.bolt.bgui.mainwin import BoltGUI
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.shape import Method, Parse, Nut, Screw, Thread, pair_screw_nut_threads, pair_holes,create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
    from common.properties import get_properties
    from common.bolt.aster import MakeComm
    from common import logging

StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Geompy = geomBuilder.New()

class Bolt1D(QObject):
    pattern_bolt = re.compile(r'_B\d{1,3}(_-?\d+(\.\d+)?)+')

    parts_selected = pyqtSignal(str,str)

    parse_progess = pyqtSignal(int)
    parse_completed = pyqtSignal()

    def __init__(self):
        super(Bolt1D, self).__init__()
        self.Gui = BoltGUI()
        self.Tree = TreeBolt()
        self.Parse= Parse()
        self.roots ="0:1:1"

        self.parts_id =[]
        self.compound_id = None

        self.connect()

        # get the existing virtual bolts
        self.bolts = self.Tree.parse_for_bolt()
        if self.bolts:
            b_list = self.virtual_bolt_to_table()
            self.Gui.set_data(b_list)

    def __del__(self):
        del self.Tree
        del self.Parse
        del self.Gui
    
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

    # signal slots connection =================================================
    def connect(self):
        self.Gui.select.connect(self.select)
        self.parts_selected.connect(self.Gui.on_selection)
        self.Gui.parse.connect(self.parse_selected)
        self.parse_progess.connect(self.Gui.on_progress)

    # Slot ====================================================================          
    @pyqtSlot()
    def select(self):
        self.parts=[]
        self.compound_id = None
        selCount = salome.sg.SelectedCount()
        #logging.info(f"selected count: {selCount}") 

        if selCount == 0:
            self.parts_selected.emit("No compound or parts selected!","red")
            return
        
        elif selCount == 1:
            id = salome.sg.getSelected(0)
            obj = salome.IDToObject(id)
            otype = obj.GetShapeType()

            if otype == GEOM.COMPOUND:
                self.parts_selected.emit(obj.GetName()+ '\t'+ id,"green")
                self.compound_id = id
              
            elif otype in (GEOM.SOLID, GEOM.SHELL):
                self.parts_selected.emit("select at least 2 parts (solid or shell) or a compound","red")

        elif selCount > 1:
            parts_id =[]
            for s in range(selCount):
                id = salome.sg.getSelected(s)
                obj = salome.IDToObject(id)
                otype = obj.GetShapeType()

                if otype in (GEOM.SOLID, GEOM.SHELL):
                    parts_id.append(id)
                
            if parts_id:
                self.parts_id = parts_id
                self.parts_selected.emit(f"{len(parts_id)} parts selected","green")

            else:
                self.parts_selected.emit("select at least 2 parts (solid or shell) or a compound","red")
                
    @pyqtSlot(QVariant,float,float,float,float)
    def parse_selected(self,method:Method=Method.SCREW,d_min=3,d_max=36,tol_axis=0.01,tol_dist=0.01):
        nuts=[]
        screws=[]
        threads=[]
        v_bolts = []
        parts_to_delete = []
        lines_ids = []

        self.parse_progess.emit(0)
        #logging.info(f"compound_id: {self.compound_id}")
        if self.compound_id:
            #get the parts from the compound
            self.Tree.parse_tree_objects(self.compound_id)
            solids = self.Tree.get_parts(type=[GEOM.SOLID,GEOM.SHELL])
            #logging.info(solids)
            self.parts_id = [p.get_sid() for p in solids]
            self.compound_id = None

        if self.parts_id:
            progress = 5
            self.parse_progess.emit(5)
            for p in self.parts_id:
                progress += 80/len(self.parts_id)
                o = self.Parse.parse_obj(p,min_diameter=d_min,max_diameter=d_max)
                
                if type(o) == Nut:
                    nuts.append(o)

                elif type(o) == Screw:
                    screws.append(o)

                elif type(o) == list:
                    for e in o:
                        if type(e) == Thread:
                            threads.append(e)

                self.parse_progess.emit(progress)

            if Method.SCREW == method:
                connections = pair_screw_nut_threads(screws,nuts,threads,tol_angle=tol_axis, tol_dist=tol_dist)

            elif Method.HOLE == method:
                connections = pair_holes(threads,tol_angle=tol_axis, tol_dist=tol_dist)
            
            #logging.info(connections)

            # create virtual bolts
            for bolt in connections['bolts']:
                v_bolt = create_virtual_bolt(bolt)

                if not v_bolt is None:
                    v_bolts.append(v_bolt)    
                    for p in bolt:
                        parts_to_delete.append(p.part_id)

            for threads in connections['threads']:
                v_bolt = create_virtual_bolt_from_thread(threads)

                if not v_bolt is None:
                    v_bolts.append(v_bolt)
                    for p in threads:
                        if type(p) == Screw:
                                parts_to_delete.append(p.part_id)

            # build geom in salome
            for v_bolt in v_bolts:
                lines_ids.append(create_salome_line(v_bolt))

            vbf= Geompy.NewFolder('Virtual Bolts')
            Geompy.PutListToFolder(lines_ids, vbf)

            # add virtual bolts to table
            for v_bolt in v_bolts:
                self.bolts.append(v_bolt)

            b_list = self.virtual_bolt_to_table()
            self.Gui.set_data(b_list)

            # delete parts
            delete=True
            if delete:
                for grp in parts_to_delete:
                    Gst.removeFromStudy(grp)
                    Gst.eraseShapeByEntry(grp)

            self.parse_progess.emit(100)    

            # refresh viewer
            salome.sg.updateObjBrowser()

            # display message box with number of virtaul bolt created. On Ok, emit signal to reset the GUI
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText(f"{len(v_bolts)} virtual bolts created")
            msg.setWindowTitle("Virtual Bolt")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self.parse_progess.emit(0)
            self.parts_id =[]
            self.compound_id = None
            self.parts_selected.emit("select a compound or several parts","black")
  
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