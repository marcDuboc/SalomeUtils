import numpy as np
import time
import itertools
import copy
import GEOM
import salome
from salome.geom import geomBuilder


# Detect current study
geompy = geomBuilder.New()
salome.salome_init()

DEBUG_FILE = 'E:\GitRepo\SalomeUtils\debug\d.txt'

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

    def _get_shapeSid_and_subshapesIndices(self, subshapes:GEOM._objref_GEOM_Object):
        parent_sid = subshapes.GetMainShape().GetStudyEntry()
        subshape_index = subshapes.GetSubShapeIndices()

        if type(subshape_index)!=list:
            subshape_index = list(subshape_index)

        return (parent_sid, subshape_index)
        
    def _get_contact_area(self, subobj1, subobj2):
        common_area = geompy.MakeCommon(subobj1, subobj2)
        area = geompy.BasicProperties(common_area)
        return area[1]
    
    def _get_shape_area(self,shape):
        area = geompy.BasicProperties(shape)
        return area[1]
    
    def _merge_subshapes_per_part(self, candidates:list):
        """
        Merge subshapes into one group per part
        """
        part_list= {x[i][0] for i in (0,1) for x in candidates}

        part_1 = list()
        part_2 = list()

        for c in candidates:
            if c[0][0] not in part_1:
                part_1.append(c[0][0])

            if c[1][0] not in part_2:
                part_2.append(c[1][0])
        
        return part_1, part_2
    
    def intersection(self, obj1_sid:str, obj2_sid:str, gap=0.0, tol=0.01):
        """
        Get the intersection between two shapes
        """
        obj1 = salome.IDToObject(obj1_sid)
        obj2 = salome.IDToObject(obj2_sid)

        self.Coincidence.gap = gap
        candidates = list()
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
                            m= self._get_shapeSid_and_subshapesIndices(c[0])
                            s= self._get_shapeSid_and_subshapesIndices(c[1])
                            candidates.append((m,s))

                        else:
                        # check by contact area
                            area = self._get_contact_area(c[0], c[1])

                            if area > 0:

                                has_contact = True
                                if self._get_shape_area(c[0]) >= self._get_shape_area(c[1]):
                                    m= self._get_shapeSid_and_subshapesIndices(c[0])
                                    s= self._get_shapeSid_and_subshapesIndices(c[1])

                                else:
                                    m= self._get_shapeSid_and_subshapesIndices(c[1])
                                    s= self._get_shapeSid_and_subshapesIndices(c[0])

                                candidates.append((m,s))
                    
                return has_contact, tuple(candidates)

            else:
                return has_contact, None
            
        except:
            return has_contact, None

    def intersection_dev(self, obj1_sid:str, obj2_sid:str, gap=0.0, tol=0.01):
        """
        Get the intersection between two shapes
        """

        obj1 = salome.IDToObject(obj1_sid)
        obj2 = salome.IDToObject(obj2_sid)

        self.Coincidence.gap = gap
        candidates = list()
        sub_0 = list()
        sub_1 = list()
        has_contact = False
        test= list()

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
                            m= self._get_shapeSid_and_subshapesIndices(c[0])
                            s= self._get_shapeSid_and_subshapesIndices(c[1])

                            #TODO set master and slave
                            candidates.append((m,s))
                            sub_0.append(c[0])
                            sub_1.append(c[1])

                        else:
                        # check by contact area
                            area = self._get_contact_area(c[0], c[1])

                            if area > 0:
                                has_contact = True
                                #if self._get_shape_area(c[0]) >= self._get_shape_area(c[1]):
                                m= self._get_shapeSid_and_subshapesIndices(c[0])
                                s= self._get_shapeSid_and_subshapesIndices(c[1])

                                #else:
                                    #m= self._get_shapeSid_and_subshapesIndices(c[1])
                                    #s= self._get_shapeSid_and_subshapesIndices(c[0])

                                candidates.append((m,s))
                                sub_0.append(c[0])
                                sub_1.append(c[1])

                area_sub1 = sum((self._get_shape_area(x) for x in sub_0))
                area_sub2 = sum((self._get_shape_area(x) for x in sub_1))

                grp_1_part = self._get_shapeSid_and_subshapesIndices(sub_0[0])[0]
                grp_2_part = self._get_shapeSid_and_subshapesIndices(sub_1[0])[0]

                grp1_t=(self._get_shapeSid_and_subshapesIndices(x)[1] for x in sub_0)
                grp2_t=(self._get_shapeSid_and_subshapesIndices(x)[1] for x in sub_1)
                grp1=list()
                grp2=list()
                for i in grp1_t:
                        grp1.extend(i)
                for i in grp2_t:
                        grp2.extend(i)

                print(area_sub1, area_sub2, grp_1_part, grp_2_part)
                print(grp1)
                print(grp2)
                
                return has_contact, tuple(candidates)

            else:
                return has_contact, None
            
        except:
            return has_contact, None       




        
   