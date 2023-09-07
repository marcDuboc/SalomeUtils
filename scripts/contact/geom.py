import numpy as np
import time
import itertools
from collections import defaultdict
import copy
import GEOM
import salome
from salome.geom import geomBuilder
from contact import logging

try:
    from .utils import CombinePairs
except:
    from utils import CombinePairs

# Detect current study
geompy = geomBuilder.New()
salome.salome_init()

class Point():
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def get_coordinate(self):
        return np.array([self.x, self.y, self.z])
    
    def to_dict(self):
        return dict(x=self.x, y=self.y, z=self.z)
    
    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y}, {self.z})"

class Vector():
    def __init__(self, vx=0.0, vy=0.0, vz=1.0):
        self.vx = vx
        self.vy = vy
        self.vz = vz

    def get_vector(self):
        return np.array([self.vx, self.vy, self.vz])
    
    def to_dict(self):
        return dict(vx=self.vx, vy=self.vy, vz=self.vz)
    
    def __repr__(self) -> str:
        return f"Vector({self.vx}, {self.vy}, {self.vz})"

class BasicProperties():
    def __init__(self, args):
        self.length= args[0]
        self.area = args[1]
        self.volume = args[2]

class ShapeProperties():
    # TODO check if face are canonical and get properties
    # use geompy tesselate + alogrithm to get is planar or not
    
    Geompy = geomBuilder.New()

    FACE = dict()
    EDGE = dict()
    PLANE= dict(origin=Point(), normal=Vector())
    CYLINDER = dict(origin=Point(), axis=Vector(), radius=1, height=1)
    SPHERE = dict(origin=Point(), radius=0.0, area=0.0)
    CONE = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0.0, height=1)
    TORUS = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0.0)
    SEGMENT = dict(p1=Point(), p2=Vector())
    CIRCLE = dict(origin=Point(), normal=Vector(), radius=1)
    ELLIPSE = dict(origin=Point(), normal=Vector(), radius1=1, radius2=0)
    VERTEX = dict(origin=Point())
    ARC_ELIPSE = dict(origin=Point(), normal=Vector(), radius1=1, radius2=0, p1=Point(), p2=Point())
    ARC_CIRCLE = dict(origin=Point(), normal=Vector(), radius=1, p1=Point(), p2=Point())
    LCS = dict(origin=Point(), x=Vector(), y=Vector(), z=Vector())
    SPHERE2D = SPHERE
    CYLINDER2D = CYLINDER
    CONE2D = CONE
    TORUS2D = TORUS
    DISK_CIRCLE= PLANE
    DISK_ELLIPSE = PLANE
    POLYGON = PLANE
    PLANAR = PLANE
    LINE = SEGMENT

    Template = dict(
        PLANE=PLANE,
        CYLINDER=CYLINDER,
        SPHERE=SPHERE,
        CONE=CONE,
        TORUS=TORUS,
        SEGMENT=SEGMENT,
        CIRCLE=CIRCLE,
        ELLIPSE=ELLIPSE,
        VERTEX=VERTEX,
        ARC_ELIPSE=ARC_ELIPSE,
        ARC_CIRCLE=ARC_CIRCLE,
        LCS=LCS,
        SPHERE2D=SPHERE2D,
        CYLINDER2D = CYLINDER,
        CONE2D = CONE,
        DISK_CIRCLE= PLANE,
        DISK_ELLIPSE = PLANE,
        TORUS2D = TORUS,
        POLYGON = PLANE,
        PLANAR = PLANE,
        LINE = SEGMENT,
    )

    @staticmethod
    def get(obj):
        # KindOfShape() return a list of , first properties been the kind of shape
        kos_lst= ShapeProperties.Geompy.KindOfShape(obj)
        kind = str(kos_lst[0])

        # get the basic properties from geompy
        basic = BasicProperties(ShapeProperties.Geompy.BasicProperties(obj))

        basic_prop = dict(type=kind)
        if basic.length > 0:
            basic_prop['length'] = basic.length
        if basic.area > 0:
            basic_prop['area'] = basic.area
        if basic.volume > 0:
            basic_prop['volume'] = basic.volume

        # get the template of properties
        template= dict()

        if kind in ShapeProperties.Template.keys():
            template = ShapeProperties.Template[kind]
            kos_lst.pop(0)
            for k,v in template.items():
                if type(v) == Point:
                    for i in range(3):
                        val = kos_lst.pop(0)
                        if i ==0:
                            template[k].x = val
                        elif i ==1:
                            template[k].y = val
                        elif i ==2:
                            template[k].z = val
                elif type(v) == Vector:
                    for i in range(3):
                        val = kos_lst.pop(0)
                        if i ==0:
                            template[k].vx = val
                        elif i ==1:
                            template[k].vy = val
                        elif i ==2:
                            template[k].vz = val
                else:
                    template[k] = kos_lst.pop(0)


        # result properties
        properties = dict(**basic_prop, **template)
        
        return properties
           
class ShapeCoincidence():

    def __init__(self):
        self.tolerance = 0.01
        self.gap = 0

    def are_coincident(self, shape1, shape2):
        prop1 = ShapeProperties.get(shape1)
        prop2 = ShapeProperties.get(shape2)

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
            return False

        # Vérifier la coïncidence des axes
        distance_centers_to_line1 = self.point_to_line_distance(
            cylinder2['origin'].get_coordinate(), cylinder1['origin'].get_coordinate(), dir1_normalized)
        distance_centers_to_line2 = self.point_to_line_distance(
            cylinder1['origin'].get_coordinate(), cylinder2['origin'].get_coordinate(), dir2_normalized)

        if distance_centers_to_line1 > (cylinder1['radius'] + tolerance) or \
                distance_centers_to_line2 > (cylinder2['radius'] + tolerance):
            return False

        # Check if overlap between cylinders along the axis
        distance_centers = self.point_to_point_distance(
            cylinder1['origin'].get_coordinate(), cylinder2['origin'].get_coordinate())
        # 1% of the smallest length
        gap_mini = min(cylinder1['length'], cylinder2['length'])*0.01
        if (distance_centers + gap_mini) > (cylinder1['length'] / 2 + cylinder2['length'] / 2):
            return False

        # check if diameter are equal and area contact is not null
        if cylinder1['radius'] == cylinder2['radius']:
            common = geompy.MakeCommon(shape1, shape2)
            props = geompy.BasicProperties(common)
            area_com = props[1]
            if area_com == 0.0:
                return False

        # Compare radius
        if (abs(cylinder1['radius'] - cylinder2['radius']) > gap):
            return False

        return True

class ParseShapesIntersection():
    """
    Class to parse the intersection between two shapes
    """

    Shape_allowed = ['PLANE','PLANAR','POLYGON','DISK_CIRCLE','DISK_ELLIPSE' ,'CYLINDER', 'CYLINDER2D', 'SPHERE','SHERE2D', 'CONE','CONE2D', 'TORUS']

    def __init__(self):
        self.Coincidence = ShapeCoincidence()
        
    def _parse_for_allow_subshapes(self, subshape_list):
        subshapes=list()
        for i in range(len(subshape_list)):
            kos = str(geompy.KindOfShape(subshape_list[i])[0])
            
            if kos in ParseShapesIntersection.Shape_allowed:
                subshapes.append(subshape_list[i])

            else:
                raise ValueError(f"Shape {kos} is not allowed")

        return subshapes

    """def _get_shapeSid_and_subshapesIndices(self, subshapes:GEOM._objref_GEOM_Object):
        parent_sid = subshapes.GetMainShape().GetStudyEntry()
        subshape_index = subshapes.GetSubShapeIndices()

        if type(subshape_index)!=list:
            subshape_index = list(subshape_index)

        return (parent_sid, subshape_index)"""
        
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
            for c in comb_c:
                try:
                    connected, _, _ = geompy.FastIntersect(c[0], c[1], 0.0)
                except:
                    connected = False

                if connected:
                    id_a = c[0].GetSubShapeIndices()[0]
                    id_b = c[1].GetSubShapeIndices()[0]
                    part_con.append((id_a,id_b))

                    if id_a in c_id:
                        c_id.remove(id_a)

                    if id_b in c_id:
                        c_id.remove(id_b)
            
            if len(part_con)>1:
                part_con = CombPairs.combine(part_con)

            if len(c_id) > 0:
                part_con.append(tuple(c_id) )

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

        #print(pairs_AB)
        #print(A_connection)
        #print(B_connection)
        #print(regroup_AB)

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
        candidates = list()
        group = list()
        has_contact = False

        try:
            isconnect, res1, res2 = geompy.FastIntersect(obj1, obj2, gap)

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
                    
                    except:
                        connected = False

                    if connected:
                        # check for shape coincidence
                        if self.Coincidence.are_coincident(c[0], c[1]):
                            has_contact = True
                            candidates.append(([c[0]],[c[1]]))
                        else:
                        # check by contact area
                            area = self._get_contact_area(c[0], c[1])

                            if area > 0:
                                has_contact = True
                                candidates.append(([c[0]],[c[1]]))

                if has_contact:
                    # option to merge subshapes by part
                    #print('nb_contact',len(candidates))
                    if merge_by_part:
                        candidates = self._merge_subshapes_by_part(candidates)
                        #print('nb_merge',len(candidates))
                    
                    elif merge_by_proximity:
                        candidates = self._merge_subshapes_by_proximity(candidates)
                        #print('nb_merge',len(candidates))

                    # defined the master and slave
                    ms = self._master_and_slave_from_area(candidates)
                    #print('nb ms',len(ms))

                    # extract the sid and subshape indices
                    group = self._extract_sid_and_indices(ms)
                    #print('nb group',len(group))
                    
                return has_contact,tuple(group)

            else:
                return has_contact, None
        except:
            return has_contact, None

    




        
   