# -*- coding: utf-8 -*-
# Generate Contacts between parts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023


import itertools
import numpy as np
import salome
from salome.geom import geomBuilder,geomtools

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtCore, QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

# Detect current study
geompy = geomBuilder.New()
gg = salome.ImportComponentGUI("GEOM")
salome.salome_init()

class AutoContact(QWidget):
    def __init__(self):
        super(AutoContact, self).__init__()
        self.initUI()
        self.selectParts()
        self.parts = list()
        
    def __del__(self):
        return
    
    # get object => IDL:SALOMEDS/SObject:1.0
    def get_SALOMEDS_SObject(self,id):
        return geomtools.IDToSObject(id)
    
    # get object => IDL:GEOM/GEOM_Object:1.0
    def get_GEOM_Object(self,id):
        return salome.myStudy.FindObjectID(id).GetObject()
    
    def createGroup(self, parentShape, subshape, name):
        try:
              group = geompy.CreateGroup(parentShape, geompy.ShapeType["FACE"])
              FaceID = geompy.GetSubShapeID(parentShape, subshape)
              geompy.AddObject(group, FaceID)
              id_group = geompy.addToStudyInFather( parentShape, group, name )
              return id_group
         
        except:
              QMessageBox.critical(None,'Error',"error in create group",QMessageBox.Abort)  

    def initUI(self):
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

        # Common open_gmsh_options        
        #self.cb_common = QCheckBox("  Compound Results",self)
        #self.cb_common.setChecked(Qt.Unchecked)

        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_parts, 1, 0)
        layout.addWidget(self.tb_parts, 2, 0)
        layout.addWidget(self.pb_loadpart, 3, 0)
        layout.addWidget(self.l_gap, 4, 0)
        layout.addWidget(self.sb_gap, 5, 0)
        layout.addWidget(self.l_ctol, 6, 0)
        layout.addWidget(self.sb_ctol, 7, 0)
        layout.addWidget(self.okbox, 8, 0)
        self.setLayout(layout)

        # Connectors:
        self.okbox.accepted.connect(self.process)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadpart.clicked.connect(self.selectParts)
        
    def selectParts(self):
        try:
          selCount = salome.sg.SelectedCount()
          selobj = list()
          self.tb_parts.clear()

          for i in range(0, selCount):
            sel_i=salome.sg.getSelected(i)
            selobj_i=salome.myStudy.FindObjectID(sel_i).GetObject()
            selobj.append(selobj_i)
            self.tb_parts.append(selobj[i].GetName())
          self.parts = selobj

        except:
            QMessageBox.critical(None,'Error',"error in selected parts",QMessageBox.Abort)

    def parseShape(self, list_shapes, kind=['PLANAR', 'PLANE','CYLINDER','CYLINDER2D','SPHERE','FACE']):
        res= list()
        for i in range(0, len(list_shapes)):
            k = geompy.KindOfShape(list_shapes[i])
            #print(k[0])
            if str(k[0]) in kind:
                res.append(list_shapes[i])
        return res
  
    def cyl_prop_to_dict(self, shape):
        """
        Convertir les proprietes en dictionnaire.
        """       
        p = geompy.KindOfShape(shape)
        if str(p[0]) in ('CYLINDER2D','CYLINDER'):
            c_prop = dict(type= str(p[0]), center=(p[1],p[2],p[3]), direction=(p[4],p[5],p[6]), diameter=p[7], length=0)
            return c_prop
        return False

    def point_to_line_distance(self,point, line_point, line_dir):
        """
        Calcule la distance d'un point à une ligne définie par un point et une direction.
        """
        point_vec = np.array(point) - np.array(line_point)
        return np.linalg.norm(point_vec - np.dot(point_vec, line_dir) * line_dir)
    
    def are_cylinders_coincident(self, shape1, shape2, gap, tolerance=0.01):
        """
        Vérifie si deux cylindres coïncident dans l'espace R^3.
        """
        cylinder1 = self.cyl_prop_to_dict(shape1)
        cylinder2 = self.cyl_prop_to_dict(shape2)

        if cylinder1 == False  or cylinder2== False:
           return False
        
        else:
          # Normaliser les vecteurs de direction
          dir1_normalized = np.array(cylinder1['direction']) / np.linalg.norm(cylinder1['direction'])
          dir2_normalized = np.array(cylinder2['direction']) / np.linalg.norm(cylinder2['direction'])
          
          # Vérifier la colinéarité des axes
          dir_diff = np.arccos(np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
          print("dir_diff: ", dir_diff)
          if not (np.isclose(dir_diff, 0, atol=tolerance) or np.isclose(dir_diff, np.pi, atol=tolerance)):
              return False
          
          # Vérifier la coïncidence des axes
          distance_centers_to_line1 = self.point_to_line_distance(cylinder2['center'], cylinder1['center'], dir1_normalized)
          distance_centers_to_line2 = self.point_to_line_distance(cylinder1['center'], cylinder2['center'], dir2_normalized)
          
          if distance_centers_to_line1 > (cylinder1['diameter'] / 2 + tolerance) or \
            distance_centers_to_line2 > (cylinder2['diameter'] / 2 + tolerance):
              return False

          # Comparer les diamètres
          if (abs(cylinder1['diameter'] - cylinder2['diameter']) > gap):
              return False
          
          return True
        
    def process(self):
      selCount=0
      num_cont = 0
      gap = eval(str(self.sb_gap.text()))
      isOk = False
      ss_isOk = False     

      try:
        selobj = self.parts
        selCount = len(selobj)
        
      except:
        QMessageBox.critical(None,'Error',"Select 2 or more parts 3D first",QMessageBox.Abort)

      if selCount > 1:
        # combine all possible solid pairs
        combine = list(itertools.combinations(selobj,2))

        for i in range(0, len(combine)):
            try:
                isOk, res1, res2 = geompy.FastIntersect(combine[i][0], combine[i][1], gap)

            except:
                isOk = False
                #QMessageBox.critical(None,'Error 1',"Unexpected error",QMessageBox.Abort)

            if isOk:
                CONT  = geompy.SubShapes(combine[i][0], res1)
                CONT2 = geompy.SubShapes(combine[i][1], res2)
                
                # check if object are planar or cylinder
                cont_valid = self.parseShape(CONT)
                cont2_valid = self.parseShape(CONT2)

                # combine all possible subshapes
                comb_sub = list(itertools.product(cont_valid, cont2_valid))

                # check if subshapes intersect
                for c in comb_sub:
                    try:
                      ss_isOk, _, _ = geompy.FastIntersect(c[0], c[1], gap)

                    except:
                       ss_isOk = False
                       
                    if ss_isOk:
                      common1 = geompy.MakeCommon(c[0], c[1])
                      props = geompy.BasicProperties(common1)
                      area_com = props[1]

                      if (area_com > 0.0) or (self.are_cylinders_coincident(c[0], c[1], gap)==True):
                        num_cont += 1
                  
                        name_group_1 = 'C' + str(num_cont) + '_A'
                        grp_id = self.createGroup(combine[i][0],c[0],name_group_1)
                        gg.setColor(grp_id, 255,0,0)

                        name_group_2 = 'C' + str(num_cont) + '_B'
                        grp_id = self.createGroup(combine[i][1],c[1],name_group_2)
                        gg.setColor(grp_id, 0,255,0)


        msg_cont = "nb contacts : " + str(num_cont)    
        QMessageBox.information(None, "Information", msg_cont, QMessageBox.Ok)
            
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
