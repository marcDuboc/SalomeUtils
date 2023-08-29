# -*- coding: utf-8 -*-
# function to detect contact between two objects 
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023


import re
import itertools
import salome
import GEOM
from salome.geom import geomBuilder, geomtools

geompy = geomBuilder.New()

class ShapeProperties():

    # get from KindOfShape
    PLANAR= dict(center=(0,0,0), normal=(0,0,1))
    CYLINDER = dict(center=(0,0,0), axis=(0,0,1), radius=1, height=1)
    SPHERE = dict(center=(0,0,0), radius=1)
    CONE = dict(center=(0,0,0), axis=(0,0,1), radius1=1, radius2=0, height=1)
    TORUS = dict(center=(0,0,0), axis=(0,0,1), radius1=1, radius2=0)

    CYLINDER_2D = CYLINDER
    CONE2D = CONE
    POLYGON = PLANAR

    # get from basic properties
    FACE = dict()

    # TODO check if face are canonical and get properties
    # use geompy tesselate + alogrithm to get is planar or not

 



class ParseShapesIntersection():
    """
    Class to parse the intersection between two shapes
    """

    cannonical_types = ['FACE', 'EDGE', 'VERTEX']
    
    def __init__(self, obj1, obj2, tol):
        self.obj1 = obj1
        self.obj2 = obj2
        self.tol = tol



    

