class ObjectType():
    """reference 
    https://docs.salome-platform.org/7/gui/GEOM/geometrical_obj_prop_page.html
    
    object type are accessible from GEOM_Object.GetType()
    """

    COPY= 0
    IMPORT= 1
    POINT= 2
    VECTOR= 3
    PLANE= 4
    LINE= 5
    TORUS= 6
    BOX= 7
    CYLINDER= 8
    CONE= 9
    SPHERE= 10
    PRISM= 11
    REVOLUTION= 12
    BOOLEAN= 13
    PARTITION= 14
    POLYLINE= 15
    CIRCLE= 16
    SPLINE= 17
    ELLIPSE= 18
    CIRC_ARC= 19
    FILLET= 20
    CHAMFER= 21
    EDGE= 22
    WIRE= 23
    FACE= 24
    SHELL= 25
    SOLID= 26
    COMPOUND= 27
    SUBSHAPE= 28
    PIPE= 29
    ARCHIMEDE= 30
    FILLING= 31
    EXPLODE= 32
    GLUED= 33
    SKETCHER= 34
    CDG= 35
    FREE_BOUNDS= 36
    GROUP= 37
    BLOCK= 38
    MARKER= 39
    THRUSECTIONS= 40
    COMPOUNDFILTER= 41
    SHAPES_ON_SHAPE= 42
    ELLIPSE_ARC= 43
    FILLET_2D= 45
    FILLET_1D= 46
    PIPETSHAPE= 201


class ShapeType:
    """reference 
    https://docs.salome-platform.org/7/gui/GEOM/geometrical_obj_prop_page.html
    
    object shape type are accessible from GEOM_Object.GetShapeType()
    """
    COMPOUND=0
    COMPSOLID=0
    SOLID=0
    SHELL=0
    FACE=0
    WIRE=0
    EDGE=0
    VERTEX=0
    SHAPE=0