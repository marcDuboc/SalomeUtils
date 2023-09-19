from typing import Any
import numpy as np
from copy import deepcopy
import GEOM
import salome
from salome.geom import geomBuilder
from contact import logging

# Detect current study
Geompy = geomBuilder.New()
salome.salome_init()

from bolt.prop.properties import ShapeProperties, Point, Vector


class Screw():
    def __init__(self) -> None:
        self.origin = Point
        self.direction = Vector()
        self.length = None 
        self.radius = None
        self.contact_radius = None

    def __repr__(self) -> str:
        return f"Screw({self.origin}, {self.direction}, {self.length}, {self.radius}, {self.contact_radius})"

class Nut():
    def __init__(self) -> None:
        self.origin = Point
        self.direction = Vector()
        self.height = None 
        self.radius = None
        self.contact_radius = None

    def __repr__(self) -> str:
        return f"Nut({self.origin}, {self.direction}, {self.height}, {self.radius}, {self.contact_radius})"

class ShapeCoincidence():

    def __init__(self):
        self.tolerance = 0.01
        self.gap = 0

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

    def are_axis_colinear(self, prop1 ,prop2):
        """
        Vérifie si la norme d'un plan ou l'axer d'un cylindre sotn colinear dans l'espace R^3.
        """
        shape1 = prop1
        shape2 = prop2
        tolerance = self.tolerance
    
        # Normaliser les vecteurs de direction
        dir1_normalized = np.array(shape1['axis'].get_vector()) / np.linalg.norm(shape1['axis'].get_vector())
        dir2_normalized = np.array(shape2['axis'].get_vector()) / np.linalg.norm(shape2['axis'].get_vector())

        # Vérifier la colinéarité des axes
        dir_diff = np.arccos(
            np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
        if not (np.isclose(dir_diff, 0, atol=tolerance) or np.isclose(dir_diff, np.pi, atol=tolerance)):
            logging.info(f"dir_diff: {dir_diff}")
            return False

        return True

class ParseObject():

    allow_type = ['CYLINDER2D','PLANE','DISK_CIRCLE','POLYGON','PLANAR']

    def is_face_disk_annular(self,obj, origin_cylinder=None, axis_cylinder=None):
        """function to check if the face is a disk annular

        _ a disk annular is defined by a disk with a hole in the center
        _ the normal of the disk and the hole should be coincident
        _ the origin of the disk and the hole should be coincident
        _ the radius of the hole should be smaller than the disk radius

        algorithm:
        _ check  disctance between the circle origin  tol=r/100 => True if 2 surfaces are coincidents
        _ if True => return radius of the disk and the hole, origin, normal
        _ else return None
        """
        edges = Geompy.SubShapeAll(obj,GEOM.EDGE)
        
        edges = [deepcopy(ShapeProperties.get(e)) for e in edges]

        # get all the type of edge
        edges_type = [e['type'] for e in edges]

        if any(item in ('CIRCLE','ARC_CIRCLE') for item in edges_type) == False:
            return None
        
        if any(item in ('LINE','SEGMENT') for item in edges_type) == True:
            return None
        
        else:
            origin_circles = []
            radius_circles = []

            for e in edges:
                if e['type'] in ('CIRCLE','ARC_CIRCLE'):
                    origin_circles.append(e['origin'].get_coordinate())
                    radius_circles.append(e['radius1'])
            
            #get the means of the origin
            origin = np.mean(origin_circles,axis=0)

            #get the max deviation of the origin
            d = np.max([np.linalg.norm(o-origin) for o in origin_circles])
            
            # get the radius of the disk
            radius= [min(radius_circles),max(radius_circles)]

            if d < min(radius)/100:
                #index of the max radius
                prop = deepcopy(ShapeProperties.DISK_CIRCLE)
                prop['origin'] = Point(*origin)
                prop['area'] = np.pi*radius[1]**2
                prop['axis'] = Vector(*axis_cylinder)
                prop['type'] = 'DISK_ANNULAR'
                prop['radius1'] = radius[0]
                if radius[0] != radius[1]:
                    prop['radius2'] = radius[1]

                return prop
            
            else:
                return None
  
    def is_nut(self,subshape:list):
        """function to check if the shape is a nut

        _ a nut is defined by a cylinder, one top and one bottom surface,
        _ normal of the surface should be coincident to the axis of the cylinder 
        _ the ratio between the diameter and distance beween the top and bottom should be beween 0.4 to 1.5
        _ the origin of the cylinder should be at the center of the top and bottom surface

        algorithm:
        _ check coincident normal between the cylinder and surfaces => True if 2 surfaces and 1 cylinder are coincidents
        _ if 2 surfaces => check if the ratio is beween 0.4 to 1.5 => True if ratio is ok
        _ if surface are not disk2D => decompose the surfaces in edges
        _ check if both (top bottom) max diameter is larger than the cylnder diameter => True
        _ if True => store to nut object with salome_id and return
        """
        surface = []
        cylinder = []
        candidate_surface = []
        top_bottom = []

        S = ShapeCoincidence()

        # get the cylinder and surface
        for s in subshape:
            if s['prop']['type'] == 'CYLINDER2D':
                cylinder.append(s)

            elif s['prop']['type'] != 'CYLINDER2D':
                surface.append(s)

        # get the longest cylinder
        if len(cylinder) > 1:
            cylinder = sorted(cylinder, key=lambda k: k['prop']['height'], reverse=True)
            cylinder = cylinder[0]
        
        # check if the cylinder is coliniear with the surface normal
        for s in surface:
            if S.are_axis_colinear(cylinder['prop'],s['prop']):
                candidate_surface.append(s)

        # check type of surface 
        for s in candidate_surface:
            if s['prop']['type'] == 'DISK_CIRCLE':
                top_bottom.append(s)

            # check if the surface is a disk annular
            else:
                test= self.is_face_disk_annular(s['obj'],cylinder['prop']['origin'].get_coordinate(),cylinder['prop']['axis'].get_vector())
                if test is not None:
                    s['prop'] = test
                    top_bottom.append(s)

        if len(top_bottom) < 1:
            return None 

        # get the closer surface to the cylinder extremity
        # get cylinder extremities
        ext=[None,None]
        cylinder = cylinder['prop']
        ext[0] = cylinder['origin'].get_coordinate()
        cylinder_axis = cylinder['axis'].get_vector()
        cylinder_height = cylinder['height']
        ext[1] = ext[0] + cylinder_axis*cylinder_height
    
        # get the closed surface from cylinder extremity using the distance between the extremity and the origin of the surface
        d0 = [S.point_to_point_distance(ext[1],s['prop']['origin'].get_coordinate()) for s in top_bottom]
        d1 = [S.point_to_point_distance(ext[0],s['prop']['origin'].get_coordinate()) for s in top_bottom]

        # get the index minimum distance
        if len(d0) == 0 or len(d1) == 0:
            return None
        
        i0 = np.argmin(d0)
        i1 = np.argmin(d1)

        # get the top and bottom surface
        top_bottom = [top_bottom[i0],top_bottom[i1]]
        
        # Origin of the nut is the origin of the surface with the largest radius and closest to one cylinder extremity
        # the other surface surface radius should be larger than of the cylinder radius
        rl = []
        for i,s in enumerate(top_bottom):
            if s['prop']['type'] == 'DISK_CIRCLE':
                r = s['prop']['radius1']
                rl.append((r,i))

            elif s['prop']['type'] == 'DISK_ANNULAR':
                r1 = s['prop']['radius1']
                r2=-1
                if 'radius2' in s['prop']:
                    r2 = s['prop']['radius2']
                if r2 > r1:
                    rl.append((r2,i))
                else:
                    rl.append((r1,i))

        rl = sorted(rl, key=lambda k: k[0], reverse=True)

        top_bottom = [top_bottom[rl[0][1]],top_bottom[rl[1][1]]]

        if rl[0][0] < cylinder['radius1'] or rl[1][0] < cylinder['radius1']:
            return None
        
        # check if the ratio is beween 0.4 to 1.5
        distance_between_surface = S.point_to_point_distance(top_bottom[0]['prop']['origin'].get_coordinate(),top_bottom[1]['prop']['origin'].get_coordinate())
        ratio = distance_between_surface/(cylinder['radius1']*2)

        if ratio < 0.4 or ratio > 1.6:
            return None
        
        # get the origin of the nut
        origin = top_bottom[0]['prop']['origin'].get_coordinate()
        
        # get the direction of the nut
        direction = cylinder['axis'].get_vector()

        # get the height of the nut
        height = cylinder['height']

        # get the radius of the nut
        radius = cylinder['radius1']

        # get the diameter for the contact surface as diameter of the top surface
        contact_radius = rl[0][0]

        # create the nut object
        nut = Nut()
        nut.origin = Point(*origin)
        nut.direction = Vector(*direction)
        nut.height = height
        nut.radius = radius
        nut.contact_radius = contact_radius

        return nut

    def is_screw(self,subshape:list):
        """function to check if the shape is a screw

        _ a screw is defined at least one cylinder (2 if chc/torx screw), at least one top and one bottom surface,
        _ normal of the surface should be coincident to the axis of the cylinder
        _ the bottom surface area should be smaller than the top surface and his area soule be egal or smaller of the cylinder section
        _ the origin of the cylinder should be at the center of the top and bottom surface

        input:
        _ subshape: list of dict with obj and prop [{obj:o, prop:p},...]

        algorithm:
        _ if more than 2 cylinder => retain the lengthest cylinder
        _ check coincident normal between the cylinder and surfaces => True if 2 or 3 surfaces and 1 cylinder are coincidents
        _ check if one surface is smaller than the cylinder secton area => True if one surface is smaller than the cylinder section area, this is the bottom surface
        _ define the vector of the bolt from the origin of the cylinder to the center of the bottom surface
        _ check the other surface and retain the closest one to the cylinder origin => True if one surface is closer to the cylinder section, this is the top surface
        _ if True => store to screw object with salome_id and return

        """
        surface = []
        cylinder = []
        candidate_surface = []
        top_bottom = []

        S = ShapeCoincidence()

        # get the cylinder and surface
        for s in subshape:
            if s['prop']['type'] == 'CYLINDER2D':
                cylinder.append(s)

            elif s['prop']['type'] != 'CYLINDER2D':
                surface.append(s)

        # get the longest cylinder
        if len(cylinder) > 1:
            cylinder = sorted(cylinder, key=lambda k: k['prop']['height'], reverse=True)
            cylinder = cylinder[0]
        
        # check if the cylinder is coliniear with the surface normal
        for s in surface:
            if S.are_axis_colinear(cylinder['prop'],s['prop']):
                candidate_surface.append(s)

        # check type of surface 
        for s in candidate_surface:
            if s['prop']['type'] == 'DISK_CIRCLE':
                top_bottom.append(s)

            # check if the surface is a disk annular
            else:
                test= self.is_face_disk_annular(s['obj'],cylinder['prop']['origin'].get_coordinate(),cylinder['prop']['axis'].get_vector())
                if test is not None:
                    s['prop'] = test
                    top_bottom.append(s)

        if len(top_bottom) < 1:
            return None 

        # get cylinder extremities
        ext=[None,None]
        cylinder = cylinder['prop']
        ext[0] = cylinder['origin'].get_coordinate()
        cylinder_axis = cylinder['axis'].get_vector()
        cylinder_height = cylinder['height']
        ext[1] = ext[0] + cylinder_axis*cylinder_height

        # get the closed surface from cylinder extremity using the distance between the extremity and the origin of the surface 
        d0 = [S.point_to_point_distance(ext[1],s['prop']['origin'].get_coordinate()) for s in top_bottom]
        d1 = [S.point_to_point_distance(ext[0],s['prop']['origin'].get_coordinate()) for s in top_bottom]

        i0 = np.argmin(d0)
        i1 = np.argmin(d1)

        # get the top and bottom surface
        top_bottom = [top_bottom[i0],top_bottom[i1]]

        # Origin of the screw is the origin of the surface with the largest radius and closest to one cylinder extremity
        # the other surface surface area should be egal or smaller of the cylinder section
        rl = []
        for i,s in enumerate(top_bottom):
            if s['prop']['type'] == 'DISK_CIRCLE':
                r = s['prop']['radius1']
                rl.append((r,i))

            elif s['prop']['type'] == 'DISK_ANNULAR':
                r1 = s['prop']['radius1']
                r2 = -1
                if 'radius2' in s['prop']:
                    r2 = s['prop']['radius2']
                if r2 > r1:
                    rl.append((r2,i))
                else:
                    rl.append((r1,i))

        rl = sorted(rl, key=lambda k: k[0], reverse=True)

        top_bottom = [top_bottom[rl[0][1]],top_bottom[rl[1][1]]]

        # check if the other area is smaller than the cylinder section
        if top_bottom[1]['prop']['area'] > cylinder['area']:
            return None
        
        # check if both radius are larger then the cylinder radius
        if rl[0][0] > cylinder['radius1'] and rl[1][0] > cylinder['radius1']:
            return None

        origin = top_bottom[0]['prop']['origin'].get_coordinate()

        # direction of the screw is the vector from the origin of the cylinder to the origin of the second surface
        direction = top_bottom[1]['prop']['origin'].get_coordinate() - top_bottom[0]['prop']['origin'].get_coordinate()
        direction = direction/np.linalg.norm(direction)

        # get the radius of the screw
        radius = cylinder['radius1']

        # get the length of the screw as distance between the origin of the cylinder and the origin of the second surface
        length = S.point_to_point_distance(origin,top_bottom[1]['prop']['origin'].get_coordinate())

        # get the diameter for the contact surface as diameter of the top surface
        contact_radius = rl[0][0]
       
        # create the screw object
        screw = Screw()
        screw.origin = Point(*origin)
        screw.direction = Vector(*direction)
        screw.length = length
        screw.radius = radius
        screw.contact_radius = contact_radius

        # check if the bottom surface is smaller than the cylinder section
        return screw
             
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
        """function to extract the seed point of the bolt and basic parameters of the bolt"""
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
                    p = deepcopy(ShapeProperties.get(s))
                    otype = p['type']

                    if otype == 'CYLINDER2D':
                         is_candidate = True
                    if otype in self.allow_type:
                        props.append(dict(obj=s, prop=p))

            if not is_candidate:
                return None
            
            else:
                is_screw = self.is_screw(props)
                if is_screw is not None:
                    return is_screw
                
                else:
                    is_nut = self.is_nut(props)
                    if is_nut is not None:
                        return is_nut
                    
                    else:
                        is_tread = self.is_tread(props)
                        if is_tread is not None:
                            return is_tread
                        else:
                            return None



            










