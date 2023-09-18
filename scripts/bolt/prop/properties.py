import numpy as np
from copy import deepcopy
import salome
from salome.geom import geomBuilder
Geompy = geomBuilder.New()

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

    FACE = dict()
    EDGE = dict()
    PLANE= dict(origin=Point(),axis=Vector())
    DISK_CIRCLE = dict(origin=Point(),axis=Vector(), radius=1)
    CYLINDER = dict(origin=Point(), axis=Vector(), radius=1, height=1)
    SPHERE = dict(origin=Point(), radius=0.0, area=0.0)
    CONE = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0.0, height=1)
    TORUS = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0.0)
    SEGMENT = dict(p1=Point(), p2=Vector())
    CIRCLE = dict(origin=Point(), axis=Vector(), radius=1)
    ELLIPSE = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0)
    VERTEX = dict(origin=Point())
    ARC_ELIPSE = dict(origin=Point(), axis=Vector(), radius1=1, radius2=0, p1=Point(), p2=Point())
    ARC_CIRCLE = dict(origin=Point(), axis=Vector(), radius=1, p1=Point(), p2=Point())
    LCS = dict(origin=Point(), x=Vector(), y=Vector(), z=Vector())
    SPHERE2D = SPHERE
    CYLINDER2D = CYLINDER
    CONE2D = CONE
    TORUS2D = TORUS
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
        DISK_CIRCLE= DISK_CIRCLE,
        DISK_ELLIPSE = PLANE,
        TORUS2D = TORUS,
        POLYGON = PLANE,
        PLANAR = PLANE,
        LINE = SEGMENT,
    )

    @staticmethod
    def get(obj):
        # KindOfShape() return a list of , first properties been the kind of shape
        kos_lst= Geompy.KindOfShape(obj)
        kind = str(kos_lst[0])

        # get the basic properties from geompy
        basic = BasicProperties(Geompy.BasicProperties(obj))

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
                    p= Point()
                    for i in range(3):
                        val = kos_lst.pop(0)
                        if i ==0:
                            p.x = val
                        elif i ==1:
                            p.y = val
                        elif i ==2:
                            p.z = val

                    template[k] = p
                elif type(v) == Vector:
                    v= Vector()
                    for i in range(3):
                        val = kos_lst.pop(0)
                        if i ==0:
                            v.vx = val
                        elif i ==1:
                            v.vy = val
                        elif i ==2:
                            v.vz = val
                    template[k] = v
                else:
                    template[k] = kos_lst.pop(0)


        # result properties
        properties = dict(**basic_prop, **template)
        
        return properties