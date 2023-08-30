# -*- coding: utf-8 -*-
# data class for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import json
import salome
import GEOM
from salome.geom import geomBuilder, geomtools
from salome.kernel.studyedit import getStudyEditor


class ContactItem():

    # get the geom builder
    Geompy = geomBuilder.New()
    
    # allowable topology
    shape_allowable_type = (Geompy.ShapeType["FACE"], Geompy.ShapeType["EDGE"], Geompy.ShapeType["VERTEX"])

    def __init__(self, shape):
        self.shapes = [] # GEOM object
        self.type = None    # string
        self.parent = None    # GEOM object

        # check if shape and subshape are allowed
        if self._are_allowed(shape) :
            self.shapes.append(shape)

        # check working at coumpound level
        if not shape.IsMainShape() :
            self.parent = shape.GetMainShape()
        else:
            raise ValueError("Contact must be defined at compound level")

    def add_shape(self, shape):
        if self._are_same_parent(shape) and self._are_same_type(shape):
            self.shapes.append(shape)
        else:
            raise ValueError("Shape and subshape are not valid")

    def _are_same_parent(self, shape):
        # check if the shape and subshape are from the same parent
        return self.parent.IsSame(shape.GetMainShape())
    
    def _are_same_type(self, shape):
        # check if the shape and subshape are from the same type
        return self.type == shape.GetShapeType()._v

    def _are_allowed(self, shape):
        #Check if the shape and subshape topology are valid
        type = shape.GetShapeType()._v

        if type not in ContactItem.shape_allowable_type:
            raise ValueError("Shape type {} is not valid. Allowable type are: {}".format(type,ContactItem.shape_allowable_type))
        
        self.type = type

        return True
    
    def get_area(self):
        area = 0
        for shape in self.shapes:
            area += ContactItem.Geompy.BasicProperties(shape)[1]
        return area
    
    def get_indices(self):
        return [shape.GetSubShapeIndices()[0] for shape in self.shapes]
    
    def get_parent_index(self):
        return self.parent.GetSubShapeIndices()[0]
    
    
class ContactPair():
    """
    Class for contact pair

    Description: class to create pair of contact bewteen contact items.
    Responsability
    - create the ids for the contact group
    - create the group name 
    - create the group type
    - create the physical group
    - create the group gap
    - create the group items

    TODO: 
    - customize the to_dict method depending of the type of contact.
    - if not yet created, create a physical group on the master for bonded and sliding contact.  
    """

    Geompy = geomBuilder.New()
    StudyEditor = getStudyEditor()
    Gst = geomtools.GeomStudyTools(StudyEditor)
    Gg = salome.ImportComponentGUI("GEOM")

    # get the study builder
    Builder = salome.myStudy.NewBuilder()

    # pattern for subshape name
    subshape_name_pattern = re.compile(r"^_C\d{1,4}[A-D][MS]$")

    # ids management
    ids_counter = 0
    ids_used=set()
    ids_available=[x for x in range(1,1000)]

    # dictionary for type of contact
    type_dict = {"BONDED": "A", "SLIDING": "B", "FRICTIONLESS": "C", "FRICTION": "D"}

    # color for master and slave
    master_color=salome.SALOMEDS.Color(1,0,0)
    slave_color=salome.SALOMEDS.Color(0,0,1)

    def __init__(self, id=None):
        if id in ContactPair.ids_available:
            self.id_instance=id
            ContactPair.ids_available.remove(self.id_instance)
        
        else:
            self.id_instance = ContactPair.ids_available.pop(0)

        ContactPair.ids_used.add(self.id_instance)
        ContactPair.ids_counter += 1

        self.items = [] # ContactItem objects
        self.groups = [] # GEOM objects
        self.type = "BONDED"  # bonded, sliding, separation
        self.master = 0  # master number as surface index
        self.gap = None  # gap value as float
        self.completed = False  # contact completed: both part and surface are defined

    def __del__(self):
        # update ids at instance destruction
        if self.id_instance in ContactPair.ids_used:
            ContactPair.ids_used.remove(self.id_instance)
            ContactPair.ids_available.append(self.id_instance)
            ContactPair.ids_available.sort()

    def delete(self):
        for grp in self.groups:
            ContactPair.Gst.removeFromStudy(grp.GetStudyEntry())
            ContactPair.Gst.eraseShapeByEntry(grp.GetStudyEntry())

    def to_dict(self):
        return {
            "id": self.id_instance,
            "group_names": self.get_group_names(),
            "type": self.type,
            "master": self.master,
            "gap": self.gap,
            "completed": self.completed
        }
    
    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self.to_dict())
    
    def _create_physical_group(self,contact_item: ContactItem):
        common_name = '_C' + str(self.id_instance)
        c_type = self.type_dict[self.type]

        if len(self.items)==1:
            suffix = 'M'
            color = self.master_color

        elif len(self.items)==2:
            suffix = 'S'
            color = self.slave_color

        name = common_name + c_type + suffix

        group = ContactPair.Geompy.CreateGroup(contact_item.parent, contact_item.type)
        indices = contact_item.get_indices()
        ContactPair.Geompy.AddObject(group, indices.pop(0))
        if len(indices) > 0:
            ContactPair.Geompy.UnionIDs(group,indices)
        ojb_group = salome.IDToObject(ContactPair.Geompy.addToStudyInFather(contact_item.parent, group, name))
        self.groups.append(ojb_group)
        self.groups[-1].SetColor(color)

        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    def _reset_name_master_slave(self):
        self.master = 0
        common_name = '_C' + str(self.id_instance)
        c_type = self.type_dict[self.type]
        suffix = ['M','S']
        colors = (self.master_color, self.slave_color)
        
        for i in range(len(self.groups)):
            name = common_name + c_type + suffix[i]
            self.groups[i].SetName(name)
            self._set_study_name(self.groups[i], name)
            self.groups[i].SetColor(colors[i])
            ContactPair.Gg.setDisplayMode(self.groups[i].GetStudyEntry(),2)
        
        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    def _set_study_name(self, obj, name):
        sobj=salome.ObjectToSObject(obj)
        sobjattr = ContactPair.Builder.FindOrCreateAttribute(sobj, "AttributeName")
        sobjattr.SetValue(name)

    def get_parents(self):
        return [x.parent for x in self.items]
    
    def get_groups(self):
        return self.groups
    
    def get_group_names(self):
        return (group.GetName() for group in self.groups)

    def set_type(self, type):
        if type in self.type_dict.keys():
            self.type = type
            for i in range(len(self.groups)):
                p_name = self.groups[i].GetName()
                n_name = p_name[:-2]+self.type_dict[type]+p_name[-1]
                self.groups[i].SetName(n_name)
                self._set_study_name(self.groups[i], n_name)
        else:
            raise ValueError("Type not available. Available types are: {}".format(self.get_type_available()))
    
    def set_gap(self, gap):
        if gap >= 0:
            self.gap = gap
        else:
            raise ValueError("Gap must be positive")
        
    def swap_master_slave(self):
        if self.completed:
            suffix=tuple()   

            if self.master == 0:
                suffix=('S','M')
                colors = (self.slave_color, self.master_color)
                self.master = 1

            elif self.master == 1:
                suffix=('M','S')
                colors = (self.master_color, self.slave_color)
                self.master = 0

            for i in range(len(self.groups)):
                p_name = self.groups[i].GetName()
                n_name = p_name[:-1]+suffix[i]
                self.groups[i].SetColor(colors[i])
                self.groups[i].SetName(n_name)
                self._set_study_name(self.groups[i], n_name)
                ContactPair.Gg.setDisplayMode(self.groups[i].GetStudyEntry(),2)

            if salome.sg.hasDesktop():
                salome.sg.updateObjBrowser()


        else:
            raise ValueError("Cannot swap master and slave. Master or slave are not defined")
        
    def add_items(self, contact_item: ContactItem):
        if self.completed == False:
            self.items.append(contact_item)
            self._create_physical_group(contact_item)
            if len(self.items) > 1:
                self.completed = True
        else:
            raise ValueError("Cannot add item. Contact group is completed")
                   
class ContactManagement():
    """
    class for contact management at study level

    responsability:
    - create contact groups from tree
    - create contact groups from autotools
    - create contact groups manually
    - deletion of contact groups from study inputs id
    - manage visibility from study inputs id
    - hide/show master and slave from study inputs id

    TODO: check if the contact group is already created
    """

    # get the geom builder
    Geompy = geomBuilder.New()
    StudyEditor = getStudyEditor()
    Gst = geomtools.GeomStudyTools(StudyEditor)
    Gg = salome.ImportComponentGUI("GEOM")

    def __init__(self):
        self._contacts = []

    def _get_subshape_from_group(self, group_obj):
        indices = group_obj.GetSubShapeIndices()
        main_shape = group_obj.GetMainShape()
        return ContactManagement.Geompy.SubShapes(main_shape, indices)
    
    # method to be used with autotools
    def create_from_shapes(self, obj_1:list(), obj_2:list()):
        c1 = ContactItem(obj_1.pop(0))
        for shape in obj_1:
            c1.add_shape(shape)
        c2 = ContactItem(obj_2.pop(0))
        for shape in obj_2:
            c2.add_shape(shape)

        group = ContactPair()
        group.add_items(c1)
        group.add_items(c2)
        self._contacts.append(group)

        # show the group
        self.show(group.id_instance)

    # create the contact group from the tree. Run once at script launch 
    # the naming convention is _C<type><id><MS>   
    def create_from_tree(self, master_grp, slave_grp, id):
        cp = ContactPair(id)
        
        # get the shapes from the group
        shapes_1 = self._get_subshape_from_group(master_grp)
        shapes_2 = self._get_subshape_from_group(slave_grp)

        ci1 = ContactItem(shapes_1.pop(0))
        for shape in shapes_1:
            ci1.add_shape(shape)

        ci2 = ContactItem(shapes_2.pop(0))
        for shape in shapes_2:
            ci2.add_shape(shape)

        cp.groups=[master_grp,slave_grp]

        cp.items=[ci1,ci2]

        cp.completed = True
        cp.master = 0

        # extract the type from the name
        name = master_grp.GetName()
        type = name[2]
        reversed_dict = {v: k for k, v in ContactPair.type_dict.items()}
        cp.type = reversed_dict[type]

        cp._reset_name_master_slave()
        self._contacts.append(cp)

        # show the group
        self.show(cp.id_instance)

    # create contact manually by selecting 2 groups. the original groups are deleted. New group are created using contactPair class. 
    def create_from_groups(self, group_1_id:str, group_2_id:str):

        # get the shapes from the group
        shapes_1 = self._get_subshape_from_group(salome.IDToObject(group_1_id))
        shapes_2 = self._get_subshape_from_group(salome.IDToObject(group_2_id))

        # create contact pair
        self.create_from_shapes(shapes_1, shapes_2)

        # delete the original groups
        for id in (group_1_id, group_2_id):
            ContactPair.Gst.removeFromStudy(id)
            ContactPair.Gst.eraseShapeByEntry(id)

    # get contact pairs
    def get_pairs(self,id):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                return pairs
            
    # get existing contact pairs
    def get_existing_pairs_indices(self):
        indices_list = []
        for pairs in self._contacts:
            if pairs.is_completed():
                indices=dict(shapes=[],subshapes=[])
                for items in pairs:
                    indices.shapes.append(items.get_parent_index())
                    items.subshapes.append(items.get_indices())
                indices_list.append(indices)
        return indices_list

    # delete contact pairs from study inputs id
    def delete(self, id):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                self._contacts.remove(pairs)
                pairs.delete()
                break
        salome.sg.updateObjBrowser()
   
    # show pairs 
    def show(self, id, transparency=0.8):
        for pairs in self._contacts:
            if pairs.id_instance == id:

                groups = pairs.get_groups()
                groups_id = [g.GetStudyEntry() for g in groups]
                for id in groups_id:
                    salome.sg.Display(id)

                parents = pairs.get_parents()
                parents_id = [p.GetStudyEntry() for p in parents]
                for id in parents_id:
                    salome.sg.Display(id)
                    ContactPair.Gg.setTransparency(id,transparency)
                break

    # hide pairs                
    def hide(self, id):
        for pairs in self._contacts:
            if pairs.id_instance == id:

                groups = pairs.get_groups()
                groups_id = [g.GetStudyEntry() for g in groups]
                for id in groups_id:
                    salome.sg.Erase(id)

                parents = pairs.get_parents()
                parents_id = [p.GetStudyEntry() for p in parents]
                for id in parents_id:
                    ContactPair.Gg.setTransparency(id,0)
                    salome.sg.Erase(id)
                break

    # export contact pairs to list
    def export(self,file):
        pairs_list = [pairs.to_dict() for pairs in self._contacts]
        json.dump(pairs_list, file, indent=4)
        
    

