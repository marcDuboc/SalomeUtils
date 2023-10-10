# -*- coding: utf-8 -*-
# module to navigate in the salome tree strucutre  
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import salome
import GEOM
from common import logging

def id_to_tuple(id):
    """
    convert a string id to a tuple of integers
    """
    return tuple([int(i) for i in id.split(':')])

def tuple_to_id(tuple):
    """
    convert a tuple of integers to a string id
    """
    return ':'.join([str(i) for i in tuple])

class ObjectType():
    """reference 
    https://docs.salome-platform.org/latest/gui/GEOM/geometrical_obj_prop_page.html"""

    COPY= 0
    IMPORT= 1
    POINT= 2
    VECTOR= 3
    PLANE= 4
    LINE= 5
    TORUS= 6
    BOX= 7
    CYLINDER= 8
    CONE= 9
    SPHERE= 10
    PRISM= 11
    REVOLUTION= 12
    BOOLEAN= 13
    PARTITION= 14
    POLYLINE= 15
    CIRCLE= 16
    SPLINE= 17
    ELLIPSE= 18
    CIRC_ARC= 19
    FILLET= 20
    CHAMFER= 21
    EDGE= 22
    WIRE= 23
    FACE= 24
    SHELL= 25
    SOLID= 26
    COMPOUND= 27
    SUBSHAPE= 28
    PIPE= 29
    ARCHIMEDE= 30
    FILLING= 31
    EXPLODE= 32
    GLUED= 33
    SKETCHER= 34
    CDG= 35
    FREE_BOUNDS= 36
    GROUP= 37
    BLOCK= 38
    MARKER= 39
    THRUSECTIONS= 40
    COMPOUNDFILTER= 41
    SHAPES_ON_SHAPE= 42
    ELLIPSE_ARC= 43
    SKETCHER= 44
    FILLET_2D= 45
    FILLET_1D= 46
    PIPETSHAPE= 201

class TreeItem():
    def __init__(self,id:tuple,name:str,type):
        self.id = id
        self.name = name
        self.type = type
        self.is_group = False

    def parent_id(self):
        return self.id[:-1]
    
    def get_sid(self):
        return tuple_to_id(self.id)
    
    def __repr__(self):
        return f"TreeItem(id={self.id},name={self.name},type={self.type},is_group={self.is_group})"

class Tree:

    def __init__(self) -> None:
        self.root = '0:1:2'
        self.objects = None
        #self.contact_pattern = re.compile(r"^_C[A-D]\d{1,4}[MS]$")

    def _check_type(self, obj_sid:str):
        """
        return the GEOM object type
        """
        obj=salome.IDToObject(obj_sid)
        try:
            return True,obj.GetShapeType()

        except:
            return False,None
        
    def _is_group(self, obj_sid:str):	
        """
        return True if the object is a group
        """
        obj=salome.IDToObject(obj_sid)
        try:
            return obj.GetType()==ObjectType.GROUP

        except:
            return False

    def parse_tree_objects(self, compound_id:str() , component=None):
        """
        retrun a list of tree items within the compound_id
        """

        if component is not None:
            self.root=component

        compound_id = id_to_tuple(compound_id)
        length_compound_id = len(compound_id)

        objects = list()
        component= salome.myStudy.FindComponentID(self.root)
        iter = salome.myStudy.NewChildIterator(component)
        iter.InitEx(True) # init recursive mode

        while iter.More():
            sobj = iter.Value()
            id = id_to_tuple(sobj.GetID()) 

            # check if the object is whithin the main object
            test_id = id[:length_compound_id]

            if test_id == compound_id:
                ok, obj_type = self._check_type(sobj.GetID())
                if ok:
                    item=TreeItem(id,sobj.GetName(),obj_type)
                    item.is_group = self._is_group(sobj.GetID())
                    objects.append(item)
            iter.Next()
            
        self.objects = objects
        return objects
    
    def get_parts(self,type=[GEOM.SOLID,GEOM.SHELL], include_groups=False):
        """
        return a list of parts
        """
        parts = list()
        for obj in self.objects:
            if obj.type in type:
                if not include_groups and not obj.is_group:
                    parts.append(obj)
        return parts
    
    def get_groups(self, filter=[]):
        """
        return a list of groups
        """
        groups = list()
        for obj in self.objects:
            if obj.is_group:
                if not filter:
                    groups.append(obj)
                elif obj.type in filter:
                    groups.append(obj)
        return groups


