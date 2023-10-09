import numpy as np
import time
import itertools
from collections import defaultdict
import copy
import GEOM
import salome
from salome.geom import geomBuilder
from common.properties import get_properties
from common import logging

try:
    from .utils import CombinePairs
except:
    from utils import CombinePairs

# Detect current study
geompy = geomBuilder.New()
salome.salome_init()


class ShapeCoincidence():

    def __init__(self):
        self.tolerance = 0.01
        self.gap = 0

    def are_coincident(self, shape1, shape2):
        prop1 = get_properties(shape1)
        prop2 = get_properties(shape2)
        logging.info(f"prop1: {prop1}")
        logging.info(f"prop2: {prop2}")

        if prop1['type'] in ('CYLINDER','CYLINDER2D') and prop2['type'] in ('CYLINDER','CYLINDER2D'):
            if self._are_cylinders_coincident(shape1, prop1 ,shape2, prop2):
                return True
            else:
                return False

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

    def _are_cylinders_coincident(self, shape1, prop1 ,shape2, prop2):
        """
        Vérifie si deux cylindres coïncident dans l'espace R^3.
        """
        cylinder1 = prop1
        cylinder2 = prop2
        tolerance = self.tolerance
        gap = self.gap
    
        # Normaliser les vecteurs de direction
        dir1_normalized = np.array(
            cylinder1['axis'].get_vector()) / np.linalg.norm(cylinder1['axis'].get_vector())
        dir2_normalized = np.array(
            cylinder2['axis'].get_vector()) / np.linalg.norm(cylinder2['axis'].get_vector())

        # Vérifier la colinéarité des axes
        dir_diff = np.arccos(
            np.clip(np.dot(dir1_normalized, dir2_normalized), -1.0, 1.0))
        if not (np.isclose(dir_diff, 0, atol=tolerance) or np.isclose(dir_diff, np.pi, atol=tolerance)):
            logging.info(f"dir_diff: {dir_diff}")
            return False

        # Vérifier la coïncidence des axes
        distance_centers_to_line1 = self.point_to_line_distance(
            cylinder2['origin'].get_coordinate(), cylinder1['origin'].get_coordinate(), dir1_normalized)
        distance_centers_to_line2 = self.point_to_line_distance(
            cylinder1['origin'].get_coordinate(), cylinder2['origin'].get_coordinate(), dir2_normalized)

        if distance_centers_to_line1 > (cylinder1['radius'] + tolerance) or \
                distance_centers_to_line2 > (cylinder2['radius'] + tolerance):
            logging.info(f"distance_centers_to_line1: {distance_centers_to_line1}")
            return False

        # Check if overlap between cylinders along the axis
        distance_centers = self.point_to_point_distance(
            cylinder1['origin'].get_coordinate(), cylinder2['origin'].get_coordinate())
        # 1% of the smallest length
        gap_mini = min(cylinder1['length'], cylinder2['length'])*0.01
        if (distance_centers + gap_mini) > (cylinder1['length'] / 2 + cylinder2['length'] / 2):
            logging.info(f"distance_centers: {distance_centers}")
            return False

        # check if diameter are equal and area contact is not null
        if cylinder1['radius'] == cylinder2['radius']:
            common = geompy.MakeCommon(shape1, shape2)
            props = geompy.BasicProperties(common)
            area_com = props[1]
            if area_com == 0.0:
                logging.info(f"area_com: {area_com}")
                return False

        # Compare radius
        if (abs(cylinder1['radius'] - cylinder2['radius']) > gap):
            logging.info(f"radius: {abs(cylinder1['radius'] - cylinder2['radius'])}")
            return False

        return True

class ParseShapesIntersection():
    """
    Class to parse the intersection between two shapes
    """

    Shape_allowed = ['FACE','TORUS2D','PLANE','PLANAR','POLYGON','DISK_CIRCLE','DISK_ELLIPSE' ,'CYLINDER', 'CYLINDER2D', 'SPHERE','SHERE2D', 'CONE','CONE2D', 'TORUS']

    def __init__(self):
        self.Coincidence = ShapeCoincidence()
        
    def _parse_for_allow_subshapes(self, subshape_list):
        subshapes=list()
        for i in range(len(subshape_list)):
            kos = str(geompy.KindOfShape(subshape_list[i])[0])
            if kos in ParseShapesIntersection.Shape_allowed:
                subshapes.append(subshape_list[i])

            else:
                print(f"Shape {kos} is not allowed")
                logging.info(f"Shape {kos} is not allowed")
    

        return subshapes
 
    def _get_contact_area(self, subobj1, subobj2):
        common_area = geompy.MakeCommon(subobj1, subobj2)
        area = geompy.BasicProperties(common_area)
        return area[1]
    
    def _get_shape_area(self,shape):
        area = geompy.BasicProperties(shape)
        return area[1]
    
    def _master_and_slave_from_area(self, candidates:list):
        ms=list()
        for c in candidates:
            area_0 = 0.0
            area_1 = 0.0

            # get the area of each subshapes
            for s in c[0]:
                area_0 += self._get_shape_area(s)
            for s in c[1]:
                area_1 += self._get_shape_area(s)

            if area_0 >= area_1:
                m= c[0]
                s= c[1]
            else:
                m= c[1]
                s= c[0]
            ms.append((m,s))

        return tuple(ms)
    
    def _extract_sid_and_indices(self,candidate:list):
        res = list()
        for c in candidate:
            # sid
            part0= c[0][0].GetMainShape().GetStudyEntry()
            part1= c[1][0].GetMainShape().GetStudyEntry()

            # subshape indices
            subshape_index0 = [c.GetSubShapeIndices()[0] for c in c[0]]
            subshape_index1 = [c.GetSubShapeIndices()[0] for c in c[1]]

            res.append(((part0,subshape_index0),(part1,subshape_index1)))
        return res

    def _merge_subshapes_by_part(self, candidates:list):
        """
        Merge subshapes into one group per part
        """
        c0=list()
        c1=list()

        for c in candidates:
            c0.extend(c[0])
            c1.extend(c[1])

        return ((list(set(c0)),list(set(c1))),)

    def _merge_subshapes_by_proximity(self, candidates:list):
        """
        Merge subshapes into one group per proximity
        """
        def check_proximity(c:list):
            c_id = [x.GetSubShapeIndices()[0] for x in c]
            part_con=list()
            comb_c = list(itertools.combinations(c, 2))
            CombPairs = CombinePairs()
            has_connected_parts = False

            for c in comb_c:
                try:
                    connected, _, _ = geompy.FastIntersect(c[0], c[1], 0.0)
                except:
                    connected = False
                    
                if connected:
                    has_connected_parts = True
                    id_a = c[0].GetSubShapeIndices()[0]
                    id_b = c[1].GetSubShapeIndices()[0]
                    part_con.append((id_a,id_b))

                    if id_a in c_id:
                        c_id.remove(id_a)

                    if id_b in c_id:
                        c_id.remove(id_b)
            
            if has_connected_parts:
                part_con = CombPairs.combine(part_con)
            
            if len(c_id) > 0:
                for c in c_id:
                    part_con.append((c,))
                
            return part_con
        
        pairs_AB = list()

        # get all subshape 
        c0=list()
        c1=list()

        #dict of subshape indices
        subshape_dict0 = dict()
        subshape_dict1 = dict()

        for c in candidates:
            #print(c)
            id0 = c[0][0].GetSubShapeIndices()[0]
            subshape_dict0[id0] = c[0][0]
            id1 = c[1][0].GetSubShapeIndices()[0]
            subshape_dict1[id1] = c[1][0]
            pairs_AB.append((id0,id1))
            c0.extend(c[0])
            c1.extend(c[1])

        #print(subshape_dict1)
        c0= list(set(c0))
        c1= list(set(c1))   

        # check by proximity
        A_connection = check_proximity(c0)
        B_connection = check_proximity(c1)

        # regroup by proximity and connectivity
        regroup_AB = list()

        def find(list:list,value:int):
            for l in list:
                if value in l:
                    return l
            return None
        
        for a, b in pairs_AB:
            find_a = find(A_connection,a)
            find_b = find(B_connection,b)
            regroup_AB.append((find_a,find_b))

        # set back the is to salome object
        regroup_AB = list(set(regroup_AB))

        logging.info(f"pairs_AB: {pairs_AB}")
        logging.info(f"A_connection: {A_connection}")
        logging.info(f"B_connection: {B_connection}")
        logging.info(f"regroup_AB: {regroup_AB}")

        res=list()
        for con in regroup_AB:
            sub0=[]
            sub1=[]
            for a in con[0]:
                sub0.append(subshape_dict0[a])
            for b in con[1]:
                sub1.append(subshape_dict1[b])
            res.append((sub0,sub1))

        return res      

    def intersection(self, obj1_sid:str, obj2_sid:str, gap=0.0, tol=0.01, merge_by_part=False, merge_by_proximity=True):
        """
        Get the intersection between two shapes

        """
        obj1 = salome.IDToObject(obj1_sid)
        obj2 = salome.IDToObject(obj2_sid)

        self.Coincidence.gap = gap
        self.Coincidence.tolerance = tol
        candidates = list()
        group = list()
        has_contact = False

        logging.info(f"Intersection between {obj1_sid} and {obj2_sid}")

        try:
            isconnect, res1, res2 = geompy.FastIntersect(obj1, obj2, gap)
            logging.info(f"isconnect: {isconnect}")
            if isconnect:
                uncheck_1 = geompy.SubShapes(obj1, res1)
                uncheck_2 = geompy.SubShapes(obj2, res2)
                contact_1 = self._parse_for_allow_subshapes(uncheck_1)
                contact_2 = self._parse_for_allow_subshapes(uncheck_2)
                combinaison = list(itertools.product(contact_1, contact_2))

                # check if subshapes intersect
                for c in combinaison:
                    try:
                        connected, _, _ = geompy.FastIntersect(c[0], c[1], gap)
                        logging.info(f"subshapes {c[0]} and {c[1]} are connected")
                    
                    except:
                        connected = False

                    if connected:
                        # check for shape coincidence
                        if self.Coincidence.are_coincident(c[0],c[1]):
                            has_contact = True
                            candidates.append(([c[0]],[c[1]]))

                        else:
                        # check by contact area
                            area = self._get_contact_area(c[0], c[1])

                            if area > 0:
                                has_contact = True
                                candidates.append(([c[0]],[c[1]]))

                if has_contact:
                    if merge_by_part:
                        candidates = self._merge_subshapes_by_part(candidates)
                    
                    elif merge_by_proximity:
                        candidates = self._merge_subshapes_by_proximity(candidates)

                    # defined the master and slave
                    ms = self._master_and_slave_from_area(candidates)

                    # extract the sid and subshape indices
                    group = self._extract_sid_and_indices(ms)
                    
                return has_contact,tuple(group)

            else:
                return has_contact, None
        except:
            return has_contact, None

    




        
   