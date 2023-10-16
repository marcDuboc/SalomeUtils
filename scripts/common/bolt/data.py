import numpy as np
from collections import defaultdict

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

    def __del__(self):
        VirtualBolt.ids_used.remove(self.id_instance)
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

        def add_bolt(self, bolt_prop:dict, id:int=None):
            self.bolts.append(VirtualBolt(id=id, **bolt_prop))

        def get_bolt(self, id:int):
            for bolt in self.bolts:
                if bolt.id_instance == id:
                    return bolt
            return None
        
        def delete_bolt(self, id:int):
            for bolt in self.bolts:
                if bolt.id_instance == id:
                    del bolt
                    return
            return None
        
        def rename_bolt(self, id:int, new_name:str):
            for bolt in self.bolts:
                if bolt.id_instance == id:
                    bolt.name = new_name
                    return
            return None