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

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtCore, QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

# add contact module
try:
    from contact.dataclass import ContactItem
    from contact.utils import get_GEOM_Object, get_SALOMEDS_SObject

except:
    script_directory = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(script_directory)
    from contact.dataclass import ContactItem
    from contact.utils import get_GEOM_Object, get_SALOMEDS_SObject

# Detect current study
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")
salome.salome_init()

# contact name regex
re_name = re.compile(r'_C\d+(.+?)')

DEBUG_FILE = 'E:\GIT_REPO\SalomeUtils\debug\d.txt'
JSON_FILE = 'E://GIT_REPO/SalomeUtils//debug//contact.json'

class AutoContact(QWidget):
    def __init__(self):
        super(AutoContact, self).__init__()
        self.compound_id = None
        self.root_tree_id = ('0:1:1')
        self.compound_child = list()
        self.contacts = dict()
        self.parts = list()
        self.initUI()

    def __del__(self):
        return

    # parse tree for contacts
    def parseContact(self, root_tree_id, compound_id, pattern=re.compile(r'_C\d+(.+?)')):

        contact_id_list = list()
        root_tree = salome.myStudy.FindComponentID(root_tree_id)
        iter = salome.myStudy.NewChildIterator(root_tree)
        iter.InitEx(True)

        test_id = compound_id.split(":")
        length_id = len(test_id)

        #with open(DEBUG_FILE, 'w') as f:
        #    f.write('ref test \t'+str(test_id)+'\t'+str(length_id)+'\n')

        while iter.More():
            c = iter.Value()
            c_id = c.GetID().split(":")
            test_c_id = c_id[:length_id]

            #with open(DEBUG_FILE, 'a') as f:
            #    f.write(str(c_id)+'\t'+str(len(c_id))+'\n'+str(test_id == test_c_id)+'\n')

            # check if the surface id is part of the compound id
            # check id the group name is not directly under the compound (shout be a level 2 chilf of the compound)
            if test_id == test_c_id and (length_id-len(c_id))>  1:
                c_name = c.GetName()
                if pattern.match(c_name):

                    pc = geomtools.IDToSObject(c.GetID()).GetFather()
                    pc_name = pc.GetName()
                    pc_id = get_GEOM_Object(pc.GetID()).GetSubShapeIndices()[0]
                    c_id = get_GEOM_Object(c.GetID()).GetSubShapeIndices()[0]
                    id = re.findall(r'\d+', c_name)[0]

                    # check if id exist in contact list
                    if id not in self.contacts.keys():
                        new_contact = ContactItem(
                            id, pc_name, pc_id, c_name, c_id)
                        self.contacts[id] = new_contact
                        contact_id_list.append(id)

                    elif id in self.contacts.keys() and self.contacts[id].completed == False:
                        self.contacts[id].add(pc_name, pc_id, c_name, c_id)

            iter.Next()

        self.exportContact(JSON_FILE)

    # export contact list to json file
    def exportContact(self, filename):
        lct = list()
        for _, v in self.contacts.items():
            lct.append(v.to_dict())
        with open(filename, 'w') as f:
            json.dump(lct, f, indent=4)

    # create group
    def createGroup(self, parentShape, subshape, name):
        try:
            group = geompy.CreateGroup(parentShape, geompy.ShapeType["FACE"])
            FaceID = geompy.GetSubShapeID(parentShape, subshape)
            geompy.AddObject(group, FaceID)
            id_group = geompy.addToStudyInFather(parentShape, group, name)
            return id_group

        except:
            QMessageBox.critical(
                None, 'Error', "error in create group", QMessageBox.Abort)

    def initUI(self):
        # select root component
        self.l_root = QLabel("Root component: ", self)
        self.lb_root = QLineEdit()
        self.bt_root = QPushButton()
        self.bt_root.setText("Load root")

        # 3D parts selected
        self.l_parts = QLabel("3D Parts for contact analysis: ", self)
        self.tb_parts = QTextBrowser()
        self.pb_loadpart = QPushButton()
        self.pb_loadpart.setText("Load selected")
        self.tb_parts.clear()

        # Adjust Gap
        self.l_gap = QLabel("Max gap between (model unit): ")
        self.sb_gap = QDoubleSpinBox()
        self.sb_gap.setDecimals(3)
        self.sb_gap.setValue(0.000)
        self.sb_gap.setSingleStep(0.001)

        # Adjust coincidcence tolerance
        self.l_ctol = QLabel("Cylinder coincidence tolerance (radian): ")
        self.sb_ctol = QDoubleSpinBox()
        self.sb_ctol.setDecimals(3)
        self.sb_ctol.setValue(0.01)
        self.sb_ctol.setSingleStep(0.001)

        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_root, 1, 0)
        layout.addWidget(self.lb_root, 2, 0)
        layout.addWidget(self.bt_root, 2, 1)
        layout.addWidget(self.l_parts, 3, 0)
        layout.addWidget(self.tb_parts, 4, 0)
        layout.addWidget(self.pb_loadpart, 5, 0)
        layout.addWidget(self.l_gap, 6, 0)
        layout.addWidget(self.sb_gap, 7, 0)
        layout.addWidget(self.l_ctol, 8, 0)
        layout.addWidget(self.sb_ctol, 9, 0)
        layout.addWidget(self.okbox, 10, 0)
        self.setLayout(layout)

        # Connectors:
        self.okbox.accepted.connect(self.process)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadpart.clicked.connect(self.selectParts)
        self.bt_root.clicked.connect(self.selectCompound)

    def selectCompound(self):
        try:
            selCount = salome.sg.SelectedCount()
            if selCount > 1:
                QMessageBox.critical(
                    None, 'Error', "Select only one root component", QMessageBox.Abort)
            else:
                self.compound_id = salome.sg.getSelected(0)
                self.compound = get_GEOM_Object(self.compound_id)
                self.lb_root.setText(self.compound.GetName())

                # get all the solid child of the root
                self.compound_child = geompy.GetExistingSubObjects(
                    self.compound)
                # pritn to debug file
                # with open(DEBUG_FILE, 'w') as f:
                # f.write(str(self.compound_id))
                self.parseContact(self.root_tree_id, self.compound_id)

        except:
            QMessageBox.critical(
                None, 'Error', "Please select a component with solid", QMessageBox.Abort)

    def selectParts(self):
        try:
            if self.compound_id != None:
                selCount = salome.sg.SelectedCount()
                selobj = list()
                self.tb_parts.clear()

                for i in range(0, selCount):
                    sel_i = salome.sg.getSelected(i)
                    selobj_i = get_GEOM_Object(sel_i)
                    selobj.append(selobj_i)
                    self.tb_parts.append(selobj[i].GetName())
                self.parts = selobj

        except:
            QMessageBox.critical(
                None, 'Error', "error in selected parts", QMessageBox.Abort)

    def getSlaveMasterIndex(self,surfaces, pattern=re.compile(".*S$")):
        # return the postion of the slave
        index = next((i for i, string in enumerate(
            surfaces) if pattern.match(string)), None)
        return index

    def parseShape(self, list_shapes, kind=['PLANAR', 'PLANE', 'CYLINDER', 'CYLINDER2D', 'SPHERE', 'FACE']):
        res = list()
        for i in range(0, len(list_shapes)):
            k = geompy.KindOfShape(list_shapes[i])
            # print(k[0])
            if str(k[0]) in kind:
                res.append(list_shapes[i])
        return res

    def cyl_prop_to_dict(self, shape):
        """
        Convertir les proprietes en dictionnaire.
        """
        p = geompy.KindOfShape(shape)
        if str(p[0]) in ('CYLINDER2D', 'CYLINDER'):
            c_prop = dict(type=str(p[0]), center=(p[1], p[2], p[3]), direction=(
                p[4], p[5], p[6]), diameter=p[7], length=p[8])
            return c_prop
        return False

    def point_to_line_distance(self, point, line_point, line_dir):
        """
        Calcule la distance d'un point à une ligne définie par un point et une direction.
        """
        point_vec = np.array(point) - np.array(line_point)
        return np.linalg.norm(point_vec - np.dot(point_vec, line_dir) * line_dir)

    def point_to_point_distance(self, point1, point2):
        """
        Calcule la distance entre deux points.
        """
        return np.linalg.norm(np.array(point1) - np.array(point2))

    def are_cylinders_coincident(self, shape1, shape2, gap, tolerance=0.01):
        """
        Vérifie si deux cylindres coïncident dans l'espace R^3.
        """
        cylinder1 = self.cyl_prop_to_dict(shape1)
        cylinder2 = self.cyl_prop_to_dict(shape2)

        if cylinder1 == False or cylinder2 == False:
            return False

        else:
            # Normaliser les vecteurs de direction
            dir1_normalized = np.array(
                cylinder1['direction']) / np.linalg.norm(cylinder1['direction'])
            dir2_normalized = np.array(
                cylinder2['direction']) / np.linalg.norm(cylinder2['direction'])

            # Vérifier la colinéarité des axes
            dir_diff = np.arccos(
                np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
            if not (np.isclose(dir_diff, 0, atol=tolerance) or np.isclose(dir_diff, np.pi, atol=tolerance)):
                return False

            # Vérifier la coïncidence des axes
            distance_centers_to_line1 = self.point_to_line_distance(
                cylinder2['center'], cylinder1['center'], dir1_normalized)
            distance_centers_to_line2 = self.point_to_line_distance(
                cylinder1['center'], cylinder2['center'], dir2_normalized)

            if distance_centers_to_line1 > (cylinder1['diameter'] / 2 + tolerance) or \
                    distance_centers_to_line2 > (cylinder2['diameter'] / 2 + tolerance):
                return False

            # Check if overlap between cylinders along the axis
            distance_centers = self.point_to_point_distance(
                cylinder1['center'], cylinder2['center'])
            # 1% of the smallest length
            gap_mini = min(cylinder1['length'], cylinder2['length'])*0.01
            if (distance_centers + gap_mini) > (cylinder1['length'] / 2 + cylinder2['length'] / 2):
                return False

            # check if diameter are equal and area contact is not null
            if cylinder1['diameter'] == cylinder2['diameter']:
                common = geompy.MakeCommon(shape1, shape2)
                props = geompy.BasicProperties(common)
                area_com = props[1]
                if area_com == 0.0:
                    return False

            # Comparer les diamètres
            if (abs(cylinder1['diameter'] - cylinder2['diameter']) > gap):
                return False

            return True

    def is_slave_candidate_adjacent_to_other(self, part_id, surface_candidate):
        # lookup contact other contact surface on the same part
        surface_slave = None
        for _, v in self.contacts.items():        
            if v.completed:
                if part_id in v.parts_id:
                    # get the index of the slave surface
                    slave_index = self.getSlaveMasterIndex(v.surfaces, re.compile(".*S$"))

                    with open(DEBUG_FILE, 'a') as f:
                        f.write(str(v.surfaces) + '\t'+ str(slave_index) + '\t' + str(v.parts_id.index(part_id) == slave_index) + '\n')

                    if v.parts_id.index(part_id) == slave_index:

                        # lookup the compound child list to find the part
                        for p in self.compound_child:
                            if p.GetSubShapeIndices()[0] == v.parts_id[slave_index]:

                                # check all face of the parts to find the surface
                                for s in geompy.SubShapeAll(p, geompy.ShapeType["FACE"]):

                                    # lookup all the surface of the part to find the slave surface
                                    if s.GetSubShapeIndices()[0] == v.surfaces_id[slave_index]:
                                        surface_slave = s
                                        break
                                else:
                                    continue
                                break

                    # check if the surfaces are adjacent
                    if surface_slave != None:
                        try:
                            isadjacent, _, _ = geompy.FastIntersect(surface_slave, surface_candidate, 0.0)
                            if isadjacent:
                                return True
                        except:
                            return False
        return False

    def process(self):
        selCount = 0
        num_cont = 0
        gap = eval(str(self.sb_gap.text()))
        isOk = False
        ss_isOk = False

        try:
            selobj = self.parts
            selCount = len(selobj)

        except:
            QMessageBox.critical(
                None, 'Error', "Select 2 or more parts 3D first", QMessageBox.Abort)

        if selCount > 1:
            # combine all possible solid pairs
            combine = list(itertools.combinations(selobj, 2))

            for i in range(0, len(combine)):
                try:
                    isOk, res1, res2 = geompy.FastIntersect(
                        combine[i][0], combine[i][1], gap)

                except:
                    isOk = False
                    #QMessageBox.critical(None,'Error 1',"Unexpected error",QMessageBox.Abort)

                if isOk:
                    CONT = geompy.SubShapes(combine[i][0], res1)
                    CONT2 = geompy.SubShapes(combine[i][1], res2)

                    # check if object are planar or cylinder
                    cont_valid = self.parseShape(CONT)
                    cont2_valid = self.parseShape(CONT2)

                    # combine all possible subshapes
                    comb_sub = list(itertools.product(cont_valid, cont2_valid))

                    # check if subshapes intersect
                    for c in comb_sub:
                        try:
                            ss_isOk, _, _ = geompy.FastIntersect(
                                c[0], c[1], gap)

                        except:
                            ss_isOk = False

                        if ss_isOk:
                            common = geompy.MakeCommon(c[0], c[1])
                            props = geompy.BasicProperties(common)
                            area_com = props[1]

                            if (area_com > 0.0) or (self.are_cylinders_coincident(c[0], c[1], gap) == True):
                                num_cont += 1
                                contacts_list = [int(x)
                                                 for x in self.contacts.keys()]
                                if len(contacts_list) == 0:
                                    id = 1
                                else:
                                    id = max(contacts_list)+1

                                # first check with the area: the smallest area is the salve
                                # define the smallest area as slave
                                area = (geompy.BasicProperties(c[0])[1], geompy.BasicProperties(c[1])[1])
                                smallest_area_index = area.index(min(area))

                                master_surface=0

                                if smallest_area_index==0:
                                    master_surface = 1

                                #with open(DEBUG_FILE, 'a') as f:
                                #    f.write(str(area) + '\t'+ str(smallest_area_index) + '\n')

                                if self.is_slave_candidate_adjacent_to_other(combine[i][smallest_area_index].GetSubShapeIndices()[0], c[smallest_area_index]):
                                    if master_surface == 0:
                                        master_surface = 1
                                    else:
                                        master_surface = 0

                                # second check is there adajent slave surface on the slave surface
                                if master_surface == 0:
                                    name_group_1 = '_C' + str(id) + 'M'
                                    name_group_2 = '_C' + str(id) + 'S'
                                    color_1 = (255, 0, 0)
                                    color_2 = (0, 0, 255)

                                elif master_surface == 1:
                                    name_group_1 = '_C' + str(id) + 'S'
                                    name_group_2 = '_C' + str(id) + 'M'
                                    color_1 = (0, 0, 255)
                                    color_2 = (255, 0, 0)

                                grp_id = self.createGroup(
                                    combine[i][0], c[0], name_group_1)
                                gg.setColor(
                                    grp_id, color_1[0], color_1[1], color_1[2])

                                grp_id = self.createGroup(
                                    combine[i][1], c[1], name_group_2)
                                gg.setColor(
                                    grp_id, color_2[0], color_2[1], color_2[2])

                                # create contact
                                pc0_id = combine[i][0].GetSubShapeIndices()[0]
                                pc1_id = combine[i][1].GetSubShapeIndices()[0]
                                c0_id = c[0].GetSubShapeIndices()[0]
                                c1_id = c[1].GetSubShapeIndices()[0]

                                new_contact = ContactItem(id, combine[i][0].GetName(), pc0_id, name_group_1, c0_id)
                                new_contact.add(combine[i][1].GetName(), pc1_id, name_group_2, c1_id)
                                self.contacts[str(id)] = new_contact
                                
                                
                                #with open(DEBUG_FILE, 'a') as f:
                                #    f.write(str(pc0_id)+'\t'+str(pc1_id)+'\t'+str(c0_id)+'\t'+str(c1_id)+ '\n')
                                #    f.write("new contact => " + str(self.contacts[str(id)].__repr__) + '\n')

            msg_cont = "nb contacts : " + str(num_cont)
            QMessageBox.information(
                None, "Information", msg_cont, QMessageBox.Ok)

        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    # cancel function
    def cancel(self):
        self.close()
        d.close()


d = QDockWidget()
d.setWidget(AutoContact())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" 3D Contacts ")
d.setGeometry(600, 300, 400, 400)
d.show()
