# -*- coding: utf-8 -*-
# Generate virtual bolt from geometry
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 05/10/2023

import os
import sys
import inspect
import re
import json
import GEOM
import salome
from salome.kernel.studyedit import getStudyEditor
from salome.geom import geomtools, geomBuilder

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt, QVariant
from PyQt5.QtWidgets import QDockWidget,QMessageBox

#for debbuging
DEBUG = False

try:
    if DEBUG:
        from importlib import reload 
        modules = ['common.tree','common.bolt.shape', 'common.bolt.treeBolt', 'common.properties','common.bolt.aster','common.bolt.data','common.bolt.bgui.mainwin','common']
        for m in modules:
            if m in sys.modules:
                reload(sys.modules[m])

    from common.bolt.bgui.mainwin import BoltGUI
    from common.tree import id_to_tuple
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.data import BoltsManager,VirtualBolt
    from common.bolt.shape import Method, Parse, Nut, Screw, Thread, pair_screw_nut_threads, pair_holes,create_virtual_bolt,create_virtual_bolt_from_thread
    from common.properties import *
    from common.bolt.aster import MakeComm
    from common import logging

except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)

    from common.bolt.bgui.mainwin import BoltGUI
    from common.tree import id_to_tuple
    from common.bolt.treeBolt import TreeBolt
    from common.bolt.data import BoltsManager, VirtualBolt
    from common.bolt.shape import Method, Parse, Nut, Screw, Thread, pair_screw_nut_threads, pair_holes,create_virtual_bolt,create_virtual_bolt_from_thread
    from common.properties import *
    from common.bolt.aster import MakeComm
    from common import logging

StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Gg = salome.ImportComponentGUI("GEOM")
Geompy = geomBuilder.New()
Builder = salome.myStudy.NewBuilder()


class Bolt1D(QObject):
    pattern_bolt = re.compile(r'_B\d{1,3}(_-?\d+(\.\d+)?)+')
    vb_folder_name = "Virtual Bolts"

    parts_selected = pyqtSignal(str,str)
    root_selected = pyqtSignal(str,str)
    parse_progess = pyqtSignal(int)
    parse_completed = pyqtSignal()

    def __init__(self):
        super(Bolt1D, self).__init__()
        self.Gui = BoltGUI()
        self.Tree = TreeBolt()
        self.Parse= Parse()
        self.roots =None
        self.vb_folder_sid = None
        self.BoltsMgt = BoltsManager()

        self.parts_id =[]
        self.compound_id = None

        self.connect()

    def __del__(self):
        del self.BoltsMgt
        del self.Tree
        del self.Parse
        del self.Gui
        
    def virtual_bolt_to_table(self):
        bolt_array= []
        for b in self.BoltsMgt.bolts:
            logging.info(b)
            bolt_array.append([b.id_instance,
                               b.radius,
                               b.start_radius,
                               b.end_radius,
                               b.start_height,
                               b.end_height,
                               b.preload])

        return bolt_array

    def get_existing_bolt(self,roots):
        # get the existing virtual bolts
        bolts_prop =   self.Tree.parse_for_bolt(roots)
        for b in bolts_prop:
            self.BoltsMgt.add_bolt(b['prop'],b['id'])

        # add virtual bolts to table
        if bolts_prop:
            b_list = self.virtual_bolt_to_table()
            self.Gui.set_data(b_list)
            self.Gui.model.updateBolt.connect(self.update_bolt)


    def create_salome_line(self, bolt:VirtualBolt) -> str:
        """function to create a salome line from a virtual bolt"""
        p0_val = bolt.start.get_coordinate().tolist()
        p1_val = bolt.end.get_coordinate().tolist()
        p0 = Geompy.MakeVertex(*p0_val)
        p1 = Geompy.MakeVertex(*p1_val)
        l= Geompy.MakeLineTwoPnt(p0,p1)
        ld= Geompy.addToStudy(l,bolt.get_detail_name())
        Gg.setColor(ld,0,255,0)

        #create group for line and points
        grp_l = Geompy.CreateGroup(l, Geompy.ShapeType["EDGE"])
        grp_e0 = Geompy.CreateGroup(l, Geompy.ShapeType["VERTEX"])
        grp_e1 = Geompy.CreateGroup(l, Geompy.ShapeType["VERTEX"])

        # get the vertex of the line
        li = Geompy.SubShapeAll(l,Geompy.ShapeType["EDGE"])
        lid = Geompy.GetSubShapeID(l,li[0])
        Geompy.AddObject(grp_l,lid)

        vi = Geompy.SubShapeAll(l,Geompy.ShapeType["VERTEX"])
        vid = [Geompy.GetSubShapeID(l,v) for v in vi]
        Geompy.AddObject(grp_e0,vid[0])
        Geompy.AddObject(grp_e1,vid[1])

        #add the line and points to the group
        Geompy.addToStudyInFather(salome.IDToObject(ld),grp_l,bolt.get_bolt_name())
        Geompy.addToStudyInFather(salome.IDToObject(ld),grp_e0,bolt.get_start_name())
        Geompy.addToStudyInFather(salome.IDToObject(ld),grp_e1,bolt.get_end_name())
        
        return l

    # signal slots connection =================================================
    def connect(self):
        # GUI => APP
        self.Gui.select.connect(self.select)
        self.Gui.parse.connect(self.parse_selected)
        self.Gui.select_root.connect(self.on_root_select)
        self.Gui.export_bolt.connect(self.write_files)
        self.Gui.deleteItem.delBolt.connect(self.delete_bolt)
        self.Gui.model.updateBolt.connect(self.update_bolt)

        # APP => GUI
        self.parts_selected.connect(self.Gui.on_selection)
        self.parse_progess.connect(self.Gui.on_progress)
        self.root_selected.connect(self.Gui.on_root_selection)
        
    # Slot ====================================================================
    @pyqtSlot()
    def on_root_select(self):
        logging.info("on_root_select")
        selCount = salome.sg.SelectedCount()
        if selCount != 1:
            self.root_selected.emit("Selected a component !","red")
        else:
            id = salome.sg.getSelected(0)
            logging.info(f"selected id: {id}")
            if len(id_to_tuple(id)) == 3:
                self.roots = id
                name = salome.IDToSObject(self.roots).GetName()
                self.root_selected.emit(f"{name} {id}","green")
                self.get_existing_bolt(self.roots)

                #get the virtual bolt folder sid
                self.vb_folder_sid = self.Tree.get_bolt_folder(self.roots,self.vb_folder_name)
            else:
                self.root_selected.emit("Selected a component !","red")
                
    @pyqtSlot()
    def select(self):
        self.parts=[]
        self.compound_id = None
        selCount = salome.sg.SelectedCount()

        if selCount == 0:
            self.parts_selected.emit("No compound or parts selected!","red")
            return
        
        elif selCount == 1:
            id = salome.sg.getSelected(0)
            obj = salome.IDToObject(id)

            if "GetShapeType" in dir(obj):
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

                if "GetShapeType" in dir(obj):
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
        new_bolts_id=[]
        parts_to_delete = []
        lines_ids = []

        self.parse_progess.emit(0)
        logging.info(f"compound_id: {self.compound_id}")
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
                logging.info(f"part id: {p}")
                progress += 80/len(self.parts_id)
                o = self.Parse.parse_obj(p,min_diameter=d_min,max_diameter=d_max)
                logging.info(f"o: {o}")
                
                if isinstance(o,Nut):
                    nuts.append(o)

                elif isinstance(o,Screw):
                    screws.append(o)

                elif isinstance(o,list):
                    for e in o:
                        if isinstance(e,Thread):
                            threads.append(e)

                self.parse_progess.emit(progress)

                logging.info(f"nuts: {nuts}")
                logging.info(f"screws: {screws}")
                logging.info(f"threads: {threads}")

            if Method.SCREW == method:
                connections = pair_screw_nut_threads(screws,nuts,threads,tol_angle=tol_axis, tol_dist=tol_dist)

            elif Method.HOLE == method:
                connections = pair_holes(threads,tol_angle=tol_axis, tol_dist=tol_dist)
            
            #logging.info(connections)

            # create virtual bolts
            for bolt in connections['bolts']:
                bolt_prop = create_virtual_bolt(bolt)
                if bolt_prop: 
                    new_id = self.BoltsMgt.add_bolt(bolt_prop)
                    new_bolts_id.append(new_id)  
                    for p in bolt:
                        parts_to_delete.append(p.part_id)

            for threads in connections['threads']:
                bolt_prop = create_virtual_bolt_from_thread(threads)
                if bolt_prop:
                    new_id=self.BoltsMgt.add_bolt(bolt_prop)
                    new_bolts_id.append(new_id)
                    for p in threads:
                        if isinstance(p,Screw):
                                parts_to_delete.append(p.part_id)

            # build geom in salome
            for id in new_bolts_id:
                b = self.BoltsMgt.get_bolt(id)
                sbolt = self.create_salome_line(b)
                logging.debug(f"sbolt: {dir(sbolt)}")
                b.sid= sbolt.GetStudyEntry()
                lines_ids.append(sbolt)

            if self.vb_folder_sid is None:
                vbf= Geompy.NewFolder(self.vb_folder_name)
                self.vb_folder_sid = vbf.GetID()
            else:
                vbf = salome.IDToSObject(self.vb_folder_sid)
            Geompy.PutListToFolder(lines_ids, vbf)

            # add virtual bolts to table
            b_list = self.virtual_bolt_to_table()
            self.Gui.set_data(b_list)
            self.Gui.model.updateBolt.connect(self.update_bolt)

            # delete parts
            delete=False
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
            msg.setText(f"{len(new_bolts_id)} virtual bolts created")
            msg.setWindowTitle("Virtual Bolt")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self.parse_progess.emit(0)
            self.parts_id =[]
            self.compound_id = None
            self.parts_selected.emit("select a compound or several parts","black")
  
    @pyqtSlot(int,float,float,float,float,float,float)
    def update_bolt(self, id:int, 
                    radius:float,
                    radius_start:float,
                    radius_end:float, 
                    start_height:float,
                    end_height:float, 
                    preload:float):
        
        bolt_prop = dict(radius=radius,
                         radius_start=radius_start,
                         radius_end=radius_end,
                         start_height=start_height,
                         end_height=end_height,
                         preload=preload)

        # update bolt properties
        name = self.BoltsMgt.update_bolt(id, bolt_prop)
        sid = self.BoltsMgt.get_bolt(id).sid

        # update salome name
        obj = salome.IDToObject(sid)
        obj.SetName(name)

        # update salome study attribute
        sobj = salome.IDToSObject(sid)
        sobjattr = Builder.FindOrCreateAttribute(sobj, "AttributeName")
        sobjattr.SetValue(name)

        #update viewer
        salome.sg.updateObjBrowser()


    @pyqtSlot(int)
    def delete_bolt(self, id:int):
        sid = self.BoltsMgt.remove_bolt(id)

        # delete from salome
        if sid:
            logging.info(f"deleting bolt {id} {str(sid)}")
            Gst.removeFromStudy(sid)
            Gst.eraseShapeByEntry(sid)

    @pyqtSlot(str,str)
    def write_files(self,file:str,export:str):
        if self.bolts:
            if export=="ASTER":
                comm = MakeComm()
                data = comm.process(self.bolts)
                str_data = comm.to_str(data)
                with open(file, 'w') as f:
                    f.write(str_data)
                
            elif export=="RAW":
                with open(file, 'w') as f:
                    json.dump(self.bolts, f, default=lambda o: o.__dict__, indent=4)

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