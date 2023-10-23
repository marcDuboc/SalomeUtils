# -*- coding: utf-8 -*-
# module to extract the screw, nut and tread from a CAD model
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import numpy as np
from itertools import product,combinations
from enum import Enum

import GEOM
import salome
from salome.geom import geomBuilder


# Detect current study
Geompy = geomBuilder.New()
salome.salome_init()
   
from common.properties import get_properties, Point, Vector, Cylinder, Plane, DiskCircle, DiskAnnular
from common.bolt.data import VirtualBolt
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
        end: Point
        direction: Vector
        height: float
        radius: float
    """
    def __init__(self,  *args, **kwargs) -> None:
        self.part_id = ""
        self.origin = Point(0,0,0)
        self.end = Point(0,0,0)
        self.axis = Vector(0,0,0)
        self.height = 0
        self.radius = 0

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        return f"Thread({self.origin}, {self.end}, {self.axis}, {self.height}, {self.radius})"

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
    
    def closests_surfaces_from_cylinder_extremity(self, cylinder, candidates):
        """
        Retourne les surfaces les plus proche des extrémités d'un cylindre
        """

        # filter by class
        surfaces = [s for s in candidates if isinstance(s,(DiskCircle, DiskAnnular))]

        # get both extrmity of the cylinder
        e1 = cylinder.origin.get_coordinate()
        e2 = cylinder.origin.get_coordinate() + cylinder.axis.get_vector() * cylinder.height

        logging.info(f"e1: {e1} \t e2: {e2}")
        
        # get the closest surface from both extrmity
        ori = [s.origin.get_coordinate() for s in surfaces]
        for o in ori:
            logging.info(f"ori_n: {o}")

        s1n = [self.point_to_point_distance(e1, s.origin.get_coordinate()) for s in surfaces]
        s2n = [self.point_to_point_distance(e2, s.origin.get_coordinate()) for s in surfaces]
        
        logging.info(f"s1n: {s1n} \t s2n: {s2n}")

        #check if the closest surface are not the same
        if len(s1n) > 0 and len(s2n) > 0:

            # closest surface
            s1 = surfaces[np.argmin(s1n)]
            s2 = surfaces[np.argmin(s2n)]

            logging.info(f"s1: {s1} \t s2: {s2}")
            logging.info(f"s1 origin: {s1.origin.get_coordinate()} \t s2 origin: {s2.origin.get_coordinate()}")

            if isinstance(s1,(DiskCircle, DiskAnnular)) and isinstance(s2,(DiskCircle, DiskAnnular)):
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

        logging.info(f"top_r: {top_r} \t bot_r: {bot_r} \t dist: {dist} \t ratio: {ratio}")

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
        cylinders = [s for s in subshape if isinstance(s,Cylinder)]
        if not cylinders:
            return None

        # 2. Get the longest cylinder which will be considered as the main body of the screw
        cylinder = sorted(cylinders, key=lambda k: k.height, reverse=True)[0]
        logging.info(f"cylinder: {cylinder.height} \t {cylinder.radius1}")

        # 3. Check all other shapes that might be connected to the cylinder (possible top/bottom surfaces or screw head)
        candidate_surfaces= []
        S = ShapeCoincidence()
        for s in subshape:
            if isinstance(s,(Plane, DiskAnnular, DiskCircle)):
                if S.are_axis_colinear(cylinder, s,tol_angle=0.01, tol_dist=0.01):
                    logging.info(f"candidate: {s}")
                    candidate_surfaces.append(s)
        
        if candidate_surfaces is not None:

            # 4. Filter surfaces that are at the top and bottom of the cylinder
            top_surface, bottom_surface = S.closests_surfaces_from_cylinder_extremity(cylinder,[s for s in candidate_surfaces])
            logging.info(f"top_surface: {top_surface} \t bottom_surface: {bottom_surface}")
            if top_surface is not None or bottom_surface is not None:

                obj = self._check_part_kind(cylinder,top_surface,bottom_surface)

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

    def _filter_cylinders(self,cylinders:list):
        """function to filter the cylinder:

           return a list of full cylinders
        """
        #1. group cylinder by comparing their origin, if similar they are grouped
        candidate_cylinder = []
        origins = []
        for t in cylinders:
            if origins == []:
                candidate_cylinder.append([t])
                origins.append(t.origin.get_coordinate())
            else:
                for i,origin in enumerate(origins):
                    if np.isclose(origin, t.origin.get_coordinate(), atol=0.1).all():
                        candidate_cylinder[i].append(t)
                        break
                    else:
                        candidate_cylinder.append([t])
                        origins.append(t.origin.get_coordinate())
                        break

        #2. filter the candidate for each group, check the if the sum of the area is egal to np.pi*radius^2*height
        full_cylinders = []
        for i,group in enumerate(candidate_cylinder):
            area = 0
            for t in group:
                area += t.area

            area_calculated = 2*group[0].radius1*np.pi * group[0].height

            if np.isclose(area,area_calculated, atol=0.01):
                fc = group[0]
                fc.area = area_calculated
                full_cylinders.append(fc)

        return full_cylinders


    def is_tread(self,subshape:list):
        """function to check if the shape is a candidate tread
         return a list of tread

        """
        threads=[]
        candidate=[]
        for s in subshape:
            if isinstance(s,Cylinder):
                if (s.height/(s.radius1*2)) > self.THREAD_RATIO_MINIMUM:
                    candidate.append(s)

        #filtered = self._filter_candidate_treads(candidate)
        filtered = candidate

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

        #logging.info(f"obj_id: {obj_id}")

        obj = salome.IDToObject(obj_id)

        if obj is None:
            return None

        if obj.GetShapeType() not in (GEOM.SOLID,GEOM.SHELL):
            return None
        
        else:
            # get the subshapes of the object
            subshapes= Geompy.SubShapeAll(obj,GEOM.FACE)

            # get the basic properties from geompy
            unfiltred_cyl = list()
            other = list()

            is_candidate = False
            for s in subshapes:
                    p = get_properties(s)
                    
                    if isinstance(p, Cylinder):
                        if (p.radius1*2)>=min_diameter and (p.radius1*2)<=max_diameter:
                            is_candidate = True
                            unfiltred_cyl.append(p)

                    elif isinstance(p,tuple(self.allow_type)) and isinstance(p,Cylinder) == False:
                        other.append(p)

            if not is_candidate:
                return None
            
            else:
                # regroup cylinder by comparing their origin, if similar and represent a full cylinder they are grouped
                filtred_cyl =self._filter_cylinders(unfiltred_cyl)
                props = filtred_cyl + other
                
                screw_nut = self.is_nut_or_bolt(props)
                if screw_nut is not None:
                    screw_nut.part_id = obj_id
                    return screw_nut
                    
                else:
                    is_tread = self.is_tread(props)
                    if is_tread is not None:
                        for t in is_tread:
                            t.part_id = obj_id
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
    """
    Pair the holes together

    attributes:
        holes_list: list of holes
    Pair the hole together

    attributes:
        hole_list: list of screw
        tol_angle: tolerance angle to check if the axis are colinear
        tol_dist: tolerance distance to check if the axis are colinear

    return:
        dict(bolts=screw_nut_pairs, treads=screw_thread_pairs)
    """

    #1. pair the holes together using itertools

    hole_pairs = list(combinations(holes_list, 2))

    #2. check if the holes are coincident
    S = ShapeCoincidence()
    hole_pairs = [p for p in hole_pairs if S.are_axis_colinear(p[0], p[1],tol_angle, tol_dist)]

    logging.info(f"hole_pairs: {hole_pairs}")

    #3. check the min and max distance between the pair holes extremities
    valid_pairs=[]
    for p in hole_pairs:
        p0_s = p[0].origin.get_coordinate()
        p0_e = p[0].end.get_coordinate()
        p1_s = p[1].origin.get_coordinate()
        p1_e = p[1].end.get_coordinate()

        dist = [np.linalg.norm(p0_s - p1_s),np.linalg.norm(p0_s - p1_e),np.linalg.norm(p0_e - p1_s),np.linalg.norm(p0_e - p1_e)]
        min_dist = np.min(dist)
        max_dist = np.max(dist)
        logging.info(f"min_dist: {min_dist} \t max_dist: {max_dist}")

        # valid if the max distance is larger than the sum height of height the hole
        if max_dist >= p[0].height + p[1].height:
            valid_pairs.append(p)

    logging.info(f"valid_pairs: {valid_pairs}")
    return dict(holes=valid_pairs)
 
def create_virtual_bolt(pair:list):

    if isinstance(pair[0],Nut) and isinstance(pair[1],Screw):
        nut = pair[0]
        screw = pair[1]

    elif isinstance(pair[0],Screw) and isinstance(pair[1],Nut):
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

    return bolt_properties

def create_virtual_bolt_from_thread(pair:list):
    
    if isinstance(pair[0],Thread) and isinstance(pair[1],Screw):
        thread = pair[0]
        screw = pair[1]

    elif isinstance(pair[0],Screw) and isinstance(pair[1],Thread):
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

    return bolt_properties

def create_virtual_bolt_from_hole(pair:list):

    commom_bolt_diameter = [2,3,3.5,4,5,6,8,10,12,14,16,20,24,30,36,42,48,56,64,72,80,90,100]
    factor_diamter_to_head = 1.6

    # 1 from the list of points get the farthest points form each other
    p0_s = pair[0].origin.get_coordinate()
    p0_e = pair[0].end.get_coordinate()
    p1_s = pair[1].origin.get_coordinate()
    p1_e = pair[1].end.get_coordinate()
    dist = [np.linalg.norm(p0_s - p1_s),np.linalg.norm(p0_s - p1_e),np.linalg.norm(p0_e - p1_s),np.linalg.norm(p0_e - p1_e)]
    max_dist = np.max(dist)

    extremity = None
    if max_dist == np.linalg.norm(p0_s - p1_s):
        extremity= dict(start=Point(*p0_s),end=Point(*p1_s))
    elif max_dist == np.linalg.norm(p0_s - p1_e):
        extremity= dict(start=Point(*p0_s),end=Point(*p1_e))
    elif max_dist == np.linalg.norm(p0_e - p1_s):
        extremity= dict(start=Point(*p0_e),end=Point(*p1_s))
    elif max_dist == np.linalg.norm(p0_e - p1_e):
        extremity= dict(start=Point(*p0_e),end=Point(*p1_e))

    # 2 get the diameter of the hole
    radius1 = pair[0].radius
    radius2 = pair[1].radius

    if radius1 != radius2:
        screw_radius= 0.0
        extremity_start = 0

        # suppose junction screw and threads, the largest diameter been the screw
        if radius1 > radius2:
            screw_radius_ref = radius1
            thread_radius_ref = radius2
            thread_height = pair[1].height
            extremity_start = 0

        elif radius2 > radius1:
            screw_radius_ref = radius2
            thread_radius_ref = radius1
            thread_height = pair[0].height
            extremity_start = 1

        # get the diamter of the screw by searching the closed value in the list commom_bolt_diameter
        d_idx = np.argmin([np.abs(np.array(commom_bolt_diameter) - screw_radius_ref*2)])
        diameter = commom_bolt_diameter[d_idx]
        radius = diameter/2

        if radius*factor_diamter_to_head < screw_radius_ref:
            screw_radius = screw_radius_ref*factor_diamter_to_head

        else:
            screw_radius = radius*factor_diamter_to_head

        # create the virtual bolt
        bolt_properties = {
            'start': extremity['start'],
            'end': extremity['end'],
            'radius': screw_radius,
            'start_radius': 0.0,
            'start_height': 0.0,
            'end_radius': 0.0,
            'end_height': 0.0,
        }

        if extremity_start == 0:
            bolt_properties['start_radius'] = screw_radius
            bolt_properties['start_height'] = 1.0
            bolt_properties['end_radius'] = thread_radius_ref
            bolt_properties['end_height'] = -thread_height

        elif extremity_start == 1:
            bolt_properties['start_radius'] = thread_radius_ref
            bolt_properties['start_height'] = thread_height
            bolt_properties['end_radius'] = screw_radius
            bolt_properties['end_height'] = -1.0


    elif radius2 == radius1:
        contact_radius = 0.0
        # suppose junction screw and nut
        # get the diamter of the screw by searching the closed value in the list commom_bolt_diameter
        d_idx = np.argmin([np.abs(np.array(commom_bolt_diameter) - radius1*2)])
        diameter = commom_bolt_diameter[d_idx]
        radius = diameter/2

        if radius*factor_diamter_to_head < radius1:
            contact_radius = radius1*factor_diamter_to_head
        
        else:
            contact_radius = radius*factor_diamter_to_head

        # create the virtual bolt
        bolt_properties = {
            'start': extremity['start'],
            'end': extremity['end'],
            'radius': radius,
            'start_radius': contact_radius,
            'start_height': 1.0,
            'end_radius': contact_radius,
            'end_height': -1.0,
        }

    return bolt_properties







