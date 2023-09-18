import numpy as np
from copy import deepcopy
import GEOM
import salome
from salome.geom import geomBuilder
from contact import logging

# Detect current study
Geompy = geomBuilder.New()
salome.salome_init()

from bolt.prop.properties import ShapeProperties


class Screw():
    pass


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

    def is_face_disk_annular(self,obj):
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
        if len(edges) != 2:
            return None
        
        else:
            edges = [ShapeProperties.get(e) for e in edges]
            if edges[0]['type'] != 'CIRCLE' or edges[1]['type'] != 'CIRCLE':
                return None
            else:
                d = np.linalg.norm(edges[0]['origin'].get_coordinate() - edges[1]['origin'].get_coordinate())
                radius= [edges[0]['radius'],edges[1]['radius']]
                if d < min(radius)/100:
                   #index of the max radius
                    i = np.argmax(radius)
                    prop = edges[i]
                    prop['type'] = 'DISK_ANNULAR'
                    prop['area'] = radius[i]**2*np.pi
                    print("prop from function",prop)
                    return prop
                
                else:
                    return None
  

    def is_nut(self,subShapeProp:list):
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
        pass

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
                test= self.is_face_disk_annular(s['obj'])
                if test is not None:
                    s['prop'] = test
                    top_bottom.append(s)

        # get the closed surface to the cylinder origin
        print(top_bottom)

        """if len(top_bottom) > 1:
            origin = cylinder['origin'].get_coordinate()
            print([S.point_to_point_distance(k['origin'].get_coordinate(),origin) for k in top_bottom])
            top_bottom = sorted(top_bottom, key=lambda k: S.point_to_point_distance(k['origin'].get_coordinate(),origin))
            top_bottom = top_bottom[:2]"""

        # check if the bottom surface is smaller than the cylinder section
        return top_bottom
        
      

    def is_tread(self,subShapeProp:list):
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
                #return (props)
                return self.is_screw(props)



            










