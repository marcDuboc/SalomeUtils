import numpy as np
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
    def __init__(self, length=0.0, area=0.0, volume=0.0):
        self.length = length
        self.area = area
        self.volume = volume

    def set_basic_properties(self, obj):
        basic = Geompy.BasicProperties(obj)
        self.length = basic[0]
        self.area = basic[1]
        self.volume = basic[2]

class Shape(BasicProperties):
    def __init__(self, *args, **kwargs):
        super().__init__(args)
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def set_basic_properties(self, obj):
        basic = Geompy.BasicProperties(obj)
        self.length = basic[0]
        self.area = basic[1]
        self.volume = basic[2]

class Plane(Shape):
    def __init__(self, origin, axis, *args):
        super().__init__(*args, origin=origin, axis=axis)

class Cylinder(Shape):
    def __init__(self, origin, axis, radius1, height, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, height=height)

class Sphere(Shape):
    def __init__(self, origin, radius1, *args):
        super().__init__(*args, origin=origin, radius1=radius1)

class Cone(Shape):
    def __init__(self, origin, axis, radius1, radius2, height, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, radius2=radius2, height=height)

class Torus(Shape):
    def __init__(self, origin, axis, radius1, radius2, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, radius2=radius2)

class Segment(Shape):
    def __init__(self, p1, p2, *args):
        super().__init__(*args, p1=p1, p2=p2)

class Circle(Shape):
    def __init__(self, origin, axis, radius1, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1)

class DiskCircle(Shape):
    def __init__(self, origin, axis, radius1, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1)

class Ellipse(Shape):
    def __init__(self, origin, axis, radius1, radius2, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, radius2=radius2)

class Vertex(Shape):
    def __init__(self, origin, *args):
        super().__init__(*args, origin=origin)

class ArcEllipse(Shape):
    def __init__(self, origin, axis, radius1, radius2, p1, p2, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, radius2=radius2, p1=p1, p2=p2)

class ArcCircle(Shape):
    def __init__(self, origin, axis, radius1, p1, p2, *args):
        super().__init__(*args, origin=origin, axis=axis, radius1=radius1, p1=p1, p2=p2)

class LCS(Shape):
    def __init__(self, origin, x, y, z, *args):
        super().__init__(*args, origin=origin, x=x, y=y, z=z)

Sphere2D = Sphere
Cylinder2D = Cylinder
Cone2D = Cone
Torus2D = Torus
Polygon = Plane
Planar = Plane
Line = Segment
DiskEllipse = Plane

type_to_class = {
    "PLANE": Plane,
    "CYLINDER": Cylinder,
    "SPHERE": Sphere,
    "CONE": Cone,
    "TORUS": Torus,
    "SEGMENT": Segment,
    "CIRCLE": Circle,
    "ELLIPSE": Ellipse,
    "VERTEX": Vertex,
    "ARC_ELIPSE": ArcEllipse,
    "ARC_CIRCLE": ArcCircle,
    "LCS": LCS,
    "SPHERE2D": Sphere2D,
    "CYLINDER2D": Cylinder2D,
    "CONE2D": Cone2D,
    "DISK_CIRCLE": DiskCircle,
    "DISK_ELLIPSE": DiskEllipse,
    "TORUS2D": Torus2D,
    "POLYGON": Polygon,
    "PLANAR": Planar,
    "LINE": Line,
}

def extract_properties(kos_list):
    kind = str(kos_list.pop(0))
    
    if kind in ("PLANE","PLANAR"):
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "kind": kind
        }
    elif kind in ("CYLINDER", "CYLINDER2D"):
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "height": kos_list[7],
            "kind": kind
        }
    elif kind in ("SPHERE", "SPHERE2D"):
        return {
            "origin": Point(*kos_list[0:3]),
            "radius1": kos_list[3],
            "kind": kind
        }
    elif kind  in ("CONE", "CONE2D"):
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "radius2": kos_list[7],
            "height": kos_list[8],
            "kind": kind
        }
    elif kind in ("TORUS", "TORUS2D"):
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "radius2": kos_list[7],
            "kind": kind
        }
    elif kind in ("SEGMENT", "LINE"):
        return {
            "p1": Point(*kos_list[0:3]),
            "p2": Point(*kos_list[3:6]),
            "kind": kind
        }
    elif kind == "CIRCLE":
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "kind": kind
        }
    elif kind == "ELLIPSE":
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "radius2": kos_list[7],
            "kind": kind
        }
    elif kind == "VERTEX":
        return {
            "origin": Point(*kos_list[0:3]),
            "kind": kind
        }
    elif kind == "ARC_ELIPSE":
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "radius2": kos_list[7],
            "p1": Point(*kos_list[8:11]),
            "p2": Point(*kos_list[11:14]),
            "kind": kind
        }
    elif kind == "ARC_CIRCLE":
        return {
            "origin": Point(*kos_list[0:3]),
            "axis": Vector(*kos_list[3:6]),
            "radius1": kos_list[6],
            "p1": Point(*kos_list[7:10]),
            "p2": Point(*kos_list[10:13]),
            "kind": kind
        }
    elif kind == "LCS":
        return {
            "origin": Point(*kos_list[0:3]),
            "x": Vector(*kos_list[3:6]),
            "y": Vector(*kos_list[6:9]),
            "z": Vector(*kos_list[9:12]),
            "kind": kind
        }
    # Ajoutez d'autres formes si nécessaire
    else:
        return None
    
def get_properties(obj):
    kos_lst = Geompy.KindOfShape(obj)
    print()
    props = extract_properties(kos_lst)
    print(props)
    if not props:
        return None

    kind = props.pop("kind")
    shape_class = type_to_class.get(kind)

    if shape_class:
        shape = shape_class(**props)
        shape.set_basic_properties(obj)
        return shape
    else:
        return None