
import numpy as np
from itertools import combinations

import GEOM
import salome
from salome.geom import geomBuilder
from contact import logging

# Detect current study
Geompy = geomBuilder.New()
salome.salome_init()

from bolt.properties import get_properties, Point, Vector, Cylinder, Plane, DiskCircle, DiskAnnular

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

        # Vérifier la parralélisme des deux vecteurs
        dir_diff = np.arccos(np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
        if not (np.isclose(dir_diff, 0, atol=tol_angle) or np.isclose(dir_diff, np.pi, atol=tol_angle)):
            logging.info(f"dir_diff: {dir_diff}")
            return False
        
        #verifier la distance entre les deux axes
        if self.point_to_line_distance(shape1.origin.get_coordinate(), shape2.origin.get_coordinate(), dir1_normalized) > tol_dist:
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
    NUT_RATIO_MAXIMUM = 1.6
    SCREW_RATIO_MINIMUM = 2.0

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
                return dict(kind="NUT", height=dist, radius=cylinder_prop.radius1, axis=cylinder_prop.axis,origin=top_prop.origin ,contact_radius = max(top_r,bot_r))
            return None
        
        elif bot_r <= cylinder_prop.radius1 or top_r <= cylinder_prop.radius1:
            if ratio > self.SCREW_RATIO_MINIMUM and dist >= cylinder_prop.height:
                #set axis as origin from top and bottom surface
                axis = (top_prop.origin.get_coordinate() - bot_prop.origin.get_coordinate())
                axis_norm = np.linalg.norm(axis)
                return dict(kind="SCREW", height=dist,origin=top_prop.origin,radius=cylinder_prop.radius1,axis=axis_norm, contact_radius = max(top_r,bot_r))
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
                            'part_id': cylinder['obj'].GetStudyEntry(),
                            'origin': obj['origin'],
                            'axis': obj['axis'],
                            'height': obj['height'],
                            'radius': obj['radius'],
                            'contact_radius': obj['contact_radius'],
                        }
                        return Nut(**nut_properties)
                     
                    elif obj['kind'] == "SCREW":
                        screw_properties = {
                            'part_id': cylinder['obj'].GetStudyEntry(),
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

    def is_tread(self,subshape:list):
        """function to check if the shape is a tread

        fisrt check => define the candidate:
        _ a tread is defined by a cylinder, at least one top surface,
        _ normal of the surface should be coincident to the axis of the cylinder
        _ the bottom surface area should be smaller than the top surface and his area soule be egal or smaller of the cylinder section
        
        post check => valid the candidate agaitn each screw:
        _ the cylinder should overlap
        _ the axis of the cylinder should be coincident with the axis of the screw
        _ the diametter should be close to the screw diametter

        alogrithm:
        _ if not screr or nut=> store to tread object with salome_id and return

        """
        pass

    def parse_obj(self,obj_id:str, min_diameter:float=3, max_diameter:float=10):
        """function to extract kind of object"""
        obj = salome.IDToObject(obj_id)

        # check if solid or shell
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
                        is_candidate = True
                    if type(p) in self.allow_type:
                        props.append(dict(obj=s, prop=p))

            if not is_candidate:
                return None
            
            else:
                screw_nut = self.is_nut_or_bolt(props)
                if screw_nut is not None:
                    return screw_nut
                    
                else:
                    is_tread = self.is_tread(props)
                    if is_tread is not None:
                        return is_tread
                    else:
                        return None

def pair_screw_nut_treads():
    pass

            










