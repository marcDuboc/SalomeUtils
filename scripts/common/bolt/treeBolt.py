# -*- coding: utf-8 -*-
# module to navigate in the salome tree strucutre  
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import salome
import GEOM

from common import logging
from common.tree import Tree, ObjectType
from common.properties import get_properties
from .shape import VirtualBolt


class TreeBolt(Tree):
    bolt_pattern = re.compile(r'_B\d{1,3}(_-?\d+(\.\d+)?)+')

    def parse_for_bolt_folder(self, folder_name:str):
        """
        if exist return the bolt folder sid
        """
        if self.objects is None:
            self.parse_tree_objects(self.root)

        for obj in self.objects:
            if obj.name == folder_name:
                return obj.get_sid()
            
        return None
    

    def parse_for_bolt(self):
        """
        return a list of virtual bolt
        """
        bolts = []
        if self.objects is None:
            self.parse_tree_objects(self.root)
        
        for obj in self.objects:
            if self.bolt_pattern.search(obj.name):
                name = obj.name
                sid = obj.get_sid()

                isValid, otype = self._check_type(sid)

                if isValid and otype == ObjectType.SEGMENT:
                    prop = get_properties(salome.IDToObject(sid))
                    data= name.split('_')
                    data= data[1:]
                    id = int(data[0][1:])
                    bolt_properties = { 
                                        'start': prop.p1,
                                        'end': prop.p2,
                                        'radius': float(data[1]),
                                        'start_radius': float(data[2]),
                                        'start_height': float(data[3]),
                                        'end_radius': float(data[4]),
                                        'end_height': float(data[5]),
                                        'preload': float(data[6]),
                                    }
                    bolts.append(VirtualBolt(id=id, **bolt_properties))

        return bolts
                    




