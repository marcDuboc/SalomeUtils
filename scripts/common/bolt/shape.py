
import numpy as np
from itertools import combinations,product
from enum import Enum

import GEOM
import salome
from salome.geom import geomBuilder
Gg = salome.ImportComponentGUI("GEOM")

# Detect current study
Geompy = geomBuilder.New()
salome.salome_init()

from common.properties import get_properties, Point, Vector, Cylinder, Plane, DiskCircle, DiskAnnular
from common import logging

class Method(Enum):
    """
    Enum class to store the method used to create the bolt
    SCREW: if screw and nut availbel in the CAD. First search for screw then pair with nut or hole
    HOLE: if no screw in the CAD. first search for hole then pair other hole

    """
    SCREW = 1
    HOLE = 2

class Screw():
    """
    Screw class to store the screw properties

    attributes:
        part_id: str
        origin: Point
        direction: Vector
        length: float
        radius: float
        contact_radius: float
    """
    def __init__(self,  *args, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"Screw({self.origin}, {self.axis}, {self.height}, {self.radius}, {self.contact_radius})"

class Nut():
    """
    Nut class to store the screw properties

    attributes:
        part_id: str
        origin: Point
        direction: Vector
        length: float
        radius: float
        contact_radius: float
    """
    def __init__(self,  *args, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"Nut({self.origin}, {self.axis}, {self.height}, {self.radius}, {self.contact_radius})"

class Thread():
    """
     class to store the tread properties

    attributes:
        part_id: str
        origin: Point
        direction: Vector
        height: float
        radius: float
    """
    def __init__(self,  *args, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

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

class ShapeCoincidence():
    """
    Class to check if two shapes are coincident
    mainly used to check if the axis of a cylinder is coincident with the axis of a screw or nut
    """

    def point_to_line_distance(self, point, line_point, line_dir):
        """
        Calcule la distance d'un point à une ligne définie par un point et une direction.
        """
        point_vec = point - line_point
        return np.linalg.norm(point_vec - np.dot(point_vec, line_dir) * line_dir)

    def point_to_point_distance(self, point1, point2):
        """
        Calcule la distance entre deux points.
        """
        return np.linalg.norm(point1 - point2)

    def are_axis_colinear(self, prop1 ,prop2, tol_angle=0.01, tol_dist=0.01):
        """
        Vérifie si la norme d'un plan ou l'axer d'un cylindre sont colinear dans l'espace R^3.
        """
        shape1 = prop1
        shape2 = prop2

        # Normaliser les vecteurs de direction
        dir1_normalized = np.array(shape1.axis.get_vector()) / np.linalg.norm(shape1.axis.get_vector())
        dir2_normalized = np.array(shape2.axis.get_vector()) / np.linalg.norm(shape2.axis.get_vector())

        # Vérifier la parralélisme des deux vecteur dans le deux direction vect et -vect
        dir_diff = np.arccos(np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
        if not (np.isclose(dir_diff, 0, atol=tol_angle) or np.isclose(dir_diff, np.pi, atol=tol_angle)):
            #logging.info(f"dir_diff: {dir_diff}")
            return False
        
        #verifier la distance entre les deux axes
        dist1 = self.point_to_line_distance(shape1.origin.get_coordinate(), shape2.origin.get_coordinate(), dir1_normalized)
        dist2 = self.point_to_line_distance(shape2.origin.get_coordinate(), shape1.origin.get_coordinate(), dir2_normalized)
        if dist1 > tol_dist or dist2 > tol_dist:
            #logging.info(f"dist1: {dist1} \t dist2: {dist2}")
            return False

        return True
    
    def closests_surfaces_from_cylinder_extremity(self, cylinder, surfaces):
        """
        Retourne les surfaces les plus proche des extrémités d'un cylindre
        """

        # get both extrmity of the cylinder
        e1 = cylinder.origin.get_coordinate()
        e2 = cylinder.origin.get_coordinate() + cylinder.axis.get_vector() * cylinder.height

        # get the closest surface from both extrmity
        s1n = [self.point_to_point_distance(e1, s.origin.get_coordinate()) for s in surfaces]
        s2n = [self.point_to_point_distance(e2, s.origin.get_coordinate()) for s in surfaces]
        

        #check if the closest surface are not the same
        if len(s1n) > 0 and len(s2n) > 0:

            # closest surface
            s1 = surfaces[np.argmin(s1n)]
            s2 = surfaces[np.argmin(s2n)]

            if type(s1) in [DiskCircle, DiskAnnular] and type(s2) in [DiskCircle, DiskAnnular]:
                # check if attribut radius2 is present and get the larger radius from  the two

                s1_r = s1.radius1
                if hasattr(s1, 'radius2'):
                    s1_r2 = s1.radius2
                    s1_r = max(s1_r, s1_r2)

                s2_r = s2.radius1
                if hasattr(s2, 'radius2'):
                    s2_r2 = s2.radius2
                    s2_r = max(s2_r, s2_r2)

                # check if the radius of the surface is smaller than the radius of the cylinder
                top=s1_r
                bot=s2_r

                #case for screw
                if s1_r <= cylinder.radius1:
                    bot = s1
                    top = s2

                # case for nut with washer integrated
                elif s2_r > s1_r:
                    top = s2
                    bot = s1

                elif s1_r > s2_r:
                    top = s1
                    bot = s2

                # case for standart nut
                elif s2_r == s1_r:
                    bot = s2
                    top = s1

                return top, bot
            
            else:
                return None, None
        else :
            return None, None

class Parse():
    """
    a class to parse the shape and extract the screw, nut and tread

    attributes:
        NUT_RATIO_MINIMUM: float
        NUT_RATIO_MAXIMUM: float
        SCREW_RATIO_MINIMUM: float
        allow_type: list
    
    methods:
        _check_part_kind: helper function to determine if nut or screw
        is_nut_or_bolt: function to check if the shape is a nut or a screw
        is_tread: function to check if the shape is a tread
        parse_obj: function to extract kind of object
    """

    NUT_RATIO_MINIMUM = 0.4
    NUT_RATIO_MAXIMUM = 2.0
    SCREW_RATIO_MINIMUM = 2.0
    THREAD_RATIO_MINIMUM = 0.5

    allow_type = [Cylinder,DiskCircle,Plane,DiskAnnular]

    def _check_part_kind(self,cylinder_prop,top_prop,bot_prop):
        """function to determine if nut or screw
            -check againt radius
            -check ratio between cylinder radius and distaance between top and bottom surface
            -check if distance between top and bottom surface is larger or egal than cylinder height

        Args:
            cylinder_prop (Cylinder): [description]
            top_prop (DiskCircle): [description]
            bot_prop (DiskCircle): [description]

        Returns:
            type: nut or screw
            length: distance between top and bottom surface
            contact_radius: max radius of the surface
        """

        top_r = top_prop.radius1
        if hasattr(top_prop, 'radius2'):
            top_r2 = top_prop.radius2
            top_r = max(top_r, top_r2)

        bot_r = bot_prop.radius1
        if hasattr(bot_prop, 'radius2'):
            bot_r2 = bot_prop.radius2
            bot_r = max(bot_r, bot_r2)

        dist = ShapeCoincidence().point_to_point_distance(top_prop.origin.get_coordinate(),bot_prop.origin.get_coordinate())
        ratio = dist/(cylinder_prop.radius1*2)

        if top_r >= cylinder_prop.radius1 and bot_r >= cylinder_prop.radius1:
            if ratio > self.NUT_RATIO_MINIMUM and ratio < self.NUT_RATIO_MAXIMUM and dist >= cylinder_prop.height:
                axis = cylinder_prop.axis.get_vector()
                axis_norm = axis/np.linalg.norm(axis)
                return dict(kind="NUT", 
                            height=dist, 
                            radius=cylinder_prop.radius1, 
                            axis=Vector(*axis_norm),
                            origin=top_prop.origin ,
                            contact_radius = max(top_r,bot_r))
            return None
        
        elif bot_r <= cylinder_prop.radius1 or top_r <= cylinder_prop.radius1:
            if ratio > self.SCREW_RATIO_MINIMUM and dist >= cylinder_prop.height:
                axis = (top_prop.origin.get_coordinate() - bot_prop.origin.get_coordinate())
                axis_norm = axis/np.linalg.norm(axis)
                return dict(kind="SCREW", 
                            height=dist,
                            origin=top_prop.origin,
                            radius=cylinder_prop.radius1,
                            axis=Vector(*axis_norm), 
                            contact_radius = max(top_r,bot_r))
            return None
           
    def is_nut_or_bolt(self,subshape: list):

        # 1. Extract all the cylinders from the subshapes
        cylinders = [s for s in subshape if type(s['prop']) is Cylinder]
        if not cylinders:
            return None
        
        # 2. Get the longest cylinder which will be considered as the main body of the screw
        cylinder = sorted(cylinders, key=lambda k: k['prop'].height, reverse=True)[0]
        
        # 3. Check all other shapes that might be connected to the cylinder (possible top/bottom surfaces or screw head)
        candidate_surfaces= []
        S = ShapeCoincidence()
        for s in subshape:
            if type(s['prop']) in [Plane, DiskAnnular, DiskCircle]:
                if S.are_axis_colinear(cylinder['prop'], s['prop']):
                    candidate_surfaces.append(s)
        
        if candidate_surfaces is not None:

            # 4. Filter surfaces that are at the top and bottom of the cylinder
            top_surface, bottom_surface = S.closests_surfaces_from_cylinder_extremity(cylinder['prop'],[s['prop'] for s in candidate_surfaces])

            if top_surface is not None or bottom_surface is not None:

                obj = self._check_part_kind(cylinder['prop'],top_surface,bottom_surface)

                if obj is not None:
                    if obj['kind'] == "NUT":
                        nut_properties = {
                            'part_id': "",
                            'origin': obj['origin'],
                            'axis': obj['axis'],
                            'height': obj['height'],
                            'radius': obj['radius'],
                            'contact_radius': obj['contact_radius'],
                        }
                        return Nut(**nut_properties)
                     
                    elif obj['kind'] == "SCREW":
                        screw_properties = {
                            'part_id': "",
                            'origin': obj['origin'],
                            'axis': obj['axis'],
                            'height': obj['height'],
                            'radius': obj['radius'],
                            'contact_radius': obj['contact_radius'],
                        }
                        return Screw(**screw_properties)
                else:
                    return None
            else:
                return None
        else:
            return None

    def _filter_candidate_treads(self,cylinders:list):
        """function to filter the candidate treads
        only the full cylinder will be retained
        """
        #1. group cylinder by comparing their origin, if similar they are grouped
        candidate_treads = []
        origins = []
        for t in cylinders:
            if origins == []:
                candidate_treads.append([t])
                origins.append(t.origin.get_coordinate())
            else:
                for i,origin in enumerate(origins):
                    if np.isclose(origin, t.origin.get_coordinate(), atol=0.1).all():
                        candidate_treads[i].append(t)
                        break
                    else:
                        candidate_treads.append([t])
                        origins.append(t.origin.get_coordinate())
                        break

        #2. filter the candidate for each group, check the if the sum of the area is egal to np.pi*radius^2*height
        threads = []
        for i,group in enumerate(candidate_treads):
            area = 0
            for t in group:
                area += t.area

            area_calculated = 2*group[0].radius1*np.pi * group[0].height

            if np.isclose(area,area_calculated, atol=0.01):
                threads.append(group[0])

        return threads

    def is_tread(self,subshape:list):
        """function to check if the shape is a candidate tread
         return a list of tread

        """
        threads=[]
        candidate=[]
        for s in subshape:
            if type(s['prop']) is Cylinder:
                if (s['prop'].height/(s['prop'].radius1*2)) > self.THREAD_RATIO_MINIMUM:
                    candidate.append(s['prop'])

        filtered = self._filter_candidate_treads(candidate)

        # create thread object
        for c in filtered:
            ext = c.origin.get_coordinate() + c.axis.get_vector() * c.height
            end = Point(*ext)
            tread_properties ={
                                'part_id': "",
                                'origin': c.origin,
                                'end': end,
                                'axis': c.axis,
                                'height': c.height,
                                'radius': c.radius1,
                            }
            threads.append(Thread(**tread_properties))

        return threads

    def parse_obj(self,obj_id:str, min_diameter:float=3, max_diameter:float=20, ):
        """function to extract kind of object"""
        obj = salome.IDToObject(obj_id)

        if obj is None:
            return None

        if obj.GetShapeType() not in (GEOM.SOLID,GEOM.SHELL):
            return None
        
        else:
            # get the subshapes of the object
            subshapes= Geompy.SubShapeAll(obj,GEOM.FACE)

            # get the basic properties from geompy
            props = list()

            is_candidate = False
            for s in subshapes:
                    p = get_properties(s)
                    if type(p) is Cylinder:
                        if (p.radius1*2)>=min_diameter and (p.radius1*2)<=max_diameter:
                            is_candidate = True
                            props.append(dict(obj=s, prop=p))
                    elif type(p) in self.allow_type and type(p) is not Cylinder:
                        props.append(dict(obj=s, prop=p))

            if not is_candidate:
                return None
            
            else:
                # first check with the number of cylinder
                cyls = [s['prop'] for s in props if type(s['prop']) is Cylinder]
                cyls = list(set(cyls))
                
                if len(cyls) < 3:
                    screw_nut = self.is_nut_or_bolt(props)
                    if screw_nut is not None:
                        id = obj.GetStudyEntry()
                        screw_nut.part_id = id
                        return screw_nut
                    
                else:
                    is_tread = self.is_tread(props)
                    if is_tread is not None:
                        id = obj.GetStudyEntry()
                        for t in is_tread:
                            t.part_id = id

                        return is_tread
                    
                    else:
                        return None

def pair_screw_nut_threads(screw_list, nut_list, treads_list,tol_angle=0.01, tol_dist=0.01) -> dict:
    """
    Pair the screw and nut together

    attributes:
        screw_list: list of screw
        nut_list: list of nut
        treads_list: list of treads
        tol_angle: tolerance angle to check if the axis are colinear
        tol_dist: tolerance distance to check if the axis are colinear

    return:
        dict(bolts=screw_nut_pairs, treads=screw_thread_pairs)
    """

    # 1. Pair the screw and nut together using itertools product
    screw_nut_pairs = list(product(screw_list, nut_list))

    # 2.check if the screw and nut are coincident
    S = ShapeCoincidence()
    screw_nut_pairs = [p for p in screw_nut_pairs if S.are_axis_colinear(p[0], p[1],tol_angle, tol_dist)]

    # 3. check the distance between the screw and nut, if longer than the screw height, remove the pair
    screw_nut_pairs = [p for p in screw_nut_pairs if np.linalg.norm(p[0].origin.get_coordinate() - p[1].origin.get_coordinate()) <= p[0].height]

    # 4.get the screw.part_id used for the nuts
    screw_part_id_used = [s[0].part_id for s in screw_nut_pairs]
    screw_remaining = [s for s in screw_list if s.part_id not in screw_part_id_used]

    # 5.get the nut.part_id used for the screws
    screw_thread_pairs = list(product(screw_remaining, treads_list))
    screw_thread_pairs = [p for p in screw_thread_pairs if S.are_axis_colinear(p[0], p[1],tol_angle, tol_dist)]

    # TODO 6.remove the pair with the same screw on the screw_tread_pairs

    return dict(bolts=screw_nut_pairs, threads=screw_thread_pairs)

def pair_holes(holes_list,tol_angle=0.01, tol_dist=0.01) -> dict:
    pass

def create_virtual_bolt(pair:list):

    if type(pair[0])==Nut and type(pair[1])==Screw:
        nut = pair[0]
        screw = pair[1]

    elif type(pair[0])==Screw and type(pair[1])==Nut:
        screw = pair[0]
        nut = pair[1]

    else:
        return None
    
    #1.get the origin of the screw
    origin = screw.origin.get_coordinate()

    #2.get the nut extremity points
    nut_ext = [nut.origin.get_coordinate(),nut.origin.get_coordinate() + nut.axis.get_vector() * nut.height]

    #3.get the closest point from the screw origin
    nut_ext_dist = [np.linalg.norm(origin - n) for n in nut_ext]
    nut_ext = nut_ext[np.argmin(nut_ext_dist)]
    
    # create the virtual bolt
    bolt_properties = {
        'start': Point(*origin),
        'end': Point(*nut_ext),
        'radius': screw.radius,
        'start_radius': screw.contact_radius,
        'start_height': 1.0,
        'end_radius': nut.contact_radius,
        'end_height': -1.0,
    }

    return VirtualBolt(**bolt_properties)

def create_virtual_bolt_from_thread(pair:list):
    
    if type(pair[0])==Thread and type(pair[1])==Screw:
        thread = pair[0]
        screw = pair[1]

    elif type(pair[0])==Screw and type(pair[1])==Thread:
        screw = pair[0]
        thread = pair[1]

    else:
        return None
    
    #1.get the origin of the screw
    origin = screw.origin.get_coordinate()

    #2.get the thread extremity points
    thread_ext = [thread.origin.get_coordinate(),thread.end.get_coordinate()]

    #3.get the closest point from the screw origin
    thread_ext_dist = [np.linalg.norm(origin - n) for n in thread_ext]
    thread_ext = thread_ext[np.argmin(thread_ext_dist)]

    if np.isclose(origin, thread_ext, atol=0.1).all():
        return None

    o_dist = np.linalg.norm(origin - thread_ext)
    screw_remaining = screw.height - o_dist
    
    end_height = 0

    if screw_remaining <= 0:
        return None
    
    elif screw_remaining > thread.height:
        end_height = thread.height
        
    else:
        end_height = screw_remaining

    # create the virtual bolt
    bolt_properties = {
        'start': Point(*origin),
        'end': Point(*thread_ext),
        'radius': screw.radius,
        'start_radius': screw.contact_radius,
        'start_height': 1.0,
        'end_radius': thread.radius,
        'end_height': end_height,
    }

    return VirtualBolt(**bolt_properties)

def create_salome_line(bolt:VirtualBolt) -> str:
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









