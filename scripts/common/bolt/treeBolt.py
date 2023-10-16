# -*- coding: utf-8 -*-
# Specialize class Tree for bolt 
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 16/10/2023

import re
import salome
import GEOM

from common import logging
from common.tree import Tree, ObjectType
from common.properties import get_properties
from common.bolt.shape import VirtualBolt


class TreeBolt(Tree):
    bolt_pattern = re.compile(r'_B\d{1,3}(_-?\d+(\.\d+)?)+')

    def get_bolt_folder(self,root, folder_name:str):
        """
        if exist return the bolt folder sid
        """
        self.root=root
        if self.objects is None:
            self.parse_tree_objects(self.root)

        for obj in self.study_objects:
            if obj.name == folder_name:
                return obj.get_sid()
            
        return None
    
    def parse_for_bolt(self,root):
        """
        return a list of virtual bolt
        """
        self.root=root
        bolts = []
        if self.objects is None:
            self.parse_tree_objects(self.root)

        for obj in self.objects:
            
            if self.bolt_pattern.search(obj.name):
                name = obj.name
                sid = obj.get_sid()

                isValid, gtype = self._check_type(sid)
                
                if isValid and gtype == GEOM.EDGE:
                    prop = get_properties(salome.IDToObject(sid))
                    data= name.split('_')
                    data= data[1:]
                    id = int(data[0][1:])
                    bolt_properties = { 
                                        'sid': sid,
                                        'start': prop.p1,
                                        'end': prop.p2,
                                        'radius': float(data[1]),
                                        'start_radius': float(data[2]),
                                        'end_radius': float(data[3]),
                                        'start_height': float(data[4]),
                                        'end_height': float(data[5]),
                                        'preload': float(data[6]),
                                    }
                    bolts.append(dict(id=id, prop=bolt_properties))


        return bolts
                    




