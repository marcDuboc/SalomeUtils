# -*- coding: utf-8 -*-
# container to store the virtual bolt properties 
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 16/10/2023

import numpy as np
from common import logging

class VirtualBoltMaterial():
    E  = 2.1e5 # N/mm2
    nu = 0.3
    rho = 7.85e-6 # kg/mm3
    alpha = 1.2e-5 # 1/°C

class VirtualBolt():
    """
    Virtual bolt class to store the virtual bolt properties

    attributes:
        id_instance: int
        start: Point
        end: Point
        radius: float
        start_radius: float
        start_height: float
        end_radius: float
        end_height: float
        preload: float
    """
    # ids management
    ids_counter = 0
    ids_used=set()
    ids_available=[x for x in range(1,1000)]

    def __init__(self,id=None ,*args, **kwargs):
        setattr(self,'sid', None)

        if id in VirtualBolt.ids_available:
            setattr(self,'id_instance',id)
            VirtualBolt.ids_available.remove(self.id_instance)
        else:
            setattr(self,'id_instance', VirtualBolt.ids_available.pop(0))

        VirtualBolt.ids_used.add(self.id_instance)
        VirtualBolt.ids_counter += 1

        # add preload
        setattr(self,'preload', 0.0)
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    # eq operator to compare two bolts by checking if start and end points are the same
    def __eq__(self, other):
        if isinstance(other, VirtualBolt):
            return (self.start == other.start and self.end == other.end) or (self.start == other.end and self.end == other.start)
        return False

    def __del__(self):
        logging.debug(f"deleting bolt {self.id_instance}")
        VirtualBolt.ids_used.remove(self.id_instance)
        logging.debug(f"ids used: {VirtualBolt.ids_used}")
        VirtualBolt.ids_available.append(self.id_instance)
        

    def __repr__(self) -> str:
        return f"VirtualBolt({self.id_instance}, {self.start}, {self.end}, {self.radius}, {self.start_radius}, {self.start_height}, {self.end_radius}, {self.end_height}, {self.preload})"
    
    def get_start_name(self):
        return f"_B{self.id_instance}S"
    
    def get_end_name(self): 
        return f"_B{self.id_instance}E"
    
    def get_bolt_name(self):
        return f"_B{self.id_instance}"

    def get_short_name(self):
        return f"_B{self.id_instance}"
    
    def get_detail_name(self):
        return f"_B{self.id_instance}_{round(self.radius,1)}_{round(self.start_radius,1)}_{round(self.end_radius,1)}_{round(self.start_height,1)}_{round(self.end_height,1)}_{round(self.preload,1)}"
    
    def get_length(self):
        return np.linalg.norm(self.end.get_coordinate() - self.start.get_coordinate())
    

class BoltsManager():
    def __init__(self):
        self.bolts = []

    def __del__(self):
        for b in self.bolts:
            del b

    def add_bolt(self, bolt_prop:dict, id:int=None):
        self.bolts.append(VirtualBolt(id=id, **bolt_prop))
        return self.bolts[-1].id_instance

    def get_bolt(self, id:int):
        for bolt in self.bolts:
            if bolt.id_instance == id:
                return bolt
        return None
    
    def remove_bolt(self, id:int):
        for idx,bolt in enumerate(self.bolts):
            if bolt.id_instance == id:
                sid = bolt.sid
                del self.bolts[idx]
                return sid
        return None
    
    def update_bolt(self, id:int, bolt_prop:dict):
        for bolt in self.bolts:
            if bolt.id_instance == id:
                for key, value in bolt_prop.items():
                    setattr(bolt, key, value)
                return bolt.get_detail_name() 
        return None
        
        