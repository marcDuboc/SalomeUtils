# -*- coding: utf-8 -*-
# data class for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import time
import json
import itertools
from collections import OrderedDict
import salome
import GEOM
from salome.geom import geomBuilder, geomtools
from salome.kernel.studyedit import getStudyEditor
from contact.geom import ShapeProperties
from contact import logging


Geompy = geomBuilder.New()
StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Gg = salome.ImportComponentGUI("GEOM")
Builder = salome.myStudy.NewBuilder()


class GroupItem():
    shape_allowable_type = (Geompy.ShapeType["FACE"], Geompy.ShapeType["EDGE"], Geompy.ShapeType["VERTEX"])

    def __init__(self):
        self.type = None
        self.shape_sid = None
        self.subshapes_indices = []

    def __repr__(self) -> str:
        return "GroupItem(shape_sid={}, subshapes_indices={}, type={})".format(self.shape_sid, self.subshapes_indices,self.type)

    def __eq__(self, __value: object) -> bool:
        shape=salome.IDToObject(self.shape_sid)
        __shape=salome.IDToObject(__value.shape_sid)
        if not shape.IsSame(__shape):
            return False
        else:
            for indices in self.subshapes_indices:
                if indices not in __value.subshapes_indices:
                    return False
            return True

    def create(self, shape_sid:str, subshape_indices:list):
        self.shape_sid = shape_sid
        self.subshapes_indices = subshape_indices
        subobj = Geompy.GetSubShape(salome.IDToObject(shape_sid), [subshape_indices[0]])
        self.type = subobj.GetShapeType()._v

    def create_from_group(self, group_sid:str):
        obj = salome.IDToObject(group_sid)
        parent = obj.GetMainShape()
        subshapes_indices = obj.GetSubShapeIndices()
        sub = Geompy.GetSubShape(parent, subshapes_indices)

        if type(sub) == list:
            sub = sub[0]
        self.type = sub.GetShapeType()._v

        self.shape_sid = parent.GetStudyEntry()
        self.subshapes_indices = subshapes_indices

    def get_parent(self):
        return salome.IDToObject(self.shape_sid)

        
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

    # pattern for subshape name
    subshape_name_pattern = re.compile(r"^_C[A-D]\d{1,4}[MS]$")

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
        self.groups_sid = [] # group study entry
        self.type = "BONDED"  # bonded, sliding, separation
        self.master = 0  # master number as surface index
        self.gap = None  # gap value as float
        self.completed = False  # contact completed: both part and surface are defined
        type_str = ContactPair.type_dict[self.type]
        self.name='_C'+type_str+str(self.id_instance)
        self.visible = True

    def __del__(self):
        ContactPair.ids_used.clear()
        ContactPair.ids_available=[x for x in range(1,1000)]

        self.groups_sid.clear()
        for item in self.items:
            del item

    def delete(self):
        for grp in self.groups_sid:
            Gst.removeFromStudy(grp)
            Gst.eraseShapeByEntry(grp)

        if self.id_instance in ContactPair.ids_used:
            ContactPair.ids_used.remove(self.id_instance)
            ContactPair.ids_available.append(self.id_instance)
            ContactPair.ids_available.sort()

    def to_dict(self):
        return {
            "id": self.id_instance,
            "group_names": self.get_group_names(),
            "type": self.type,
            "master": self.master,
            "gap": self.gap,
            "completed": self.completed
        }
    
    def to_dict_for_export(self):
        if self.completed:
            cont = dict()
            cont['id'] = str(self.id_instance)
            cont['type'] = self.type
            cont['master_id'] = self.master
            cont['shapes'] = self.get_parents_name()
            cont['subshapes'] = self.get_group_names()

            shapes_indices = [salome.IDToObject(x).GetSubShapeIndices()[0] for x in self.get_parents_sid()]
            subshapes_indices = [salome.IDToObject(x).GetSubShapeIndices()[0] for x in self.get_groups_sid()]

            cont['shapes_id'] = shapes_indices
            cont['subshapes_id'] = subshapes_indices
            
            return cont

    def to_table_model(self):
        return OrderedDict(id=self.id_instance, name=self.name, type=self.type, visible=self.visible)

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self.to_dict())
    
    def _create_physical_group(self,group_item: GroupItem):
        c_type = self.type_dict[self.type]
        common_name = '_C' + c_type + str(self.id_instance)
        
        if len(self.items)==1:
            suffix = 'M'
            color = self.master_color

        elif len(self.items)==2:
            suffix = 'S'
            color = self.slave_color

        name = common_name + suffix

        group = Geompy.CreateGroup(group_item.get_parent(), group_item.type)
        indices = group_item.subshapes_indices.copy()

        Geompy.AddObject(group, indices.pop(0))
        if len(indices) > 0:
            Geompy.UnionIDs(group,indices)

        group_sid = Geompy.addToStudyInFather(group_item.get_parent(), group, name)
        self.groups_sid.append(group_sid)

        # set the color
        salome.IDToObject(group_sid).SetColor(color)
        
        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    def _reset_name_master_slave(self):
        self.master = 0
        c_type = self.type_dict[self.type]
        common_name = '_C' + c_type + str(self.id_instance)
        
        suffix = ['M','S']
        colors = (self.master_color, self.slave_color)
        
        for i in range(len(self.groups_sid)):
            name = common_name + suffix[i]
            group = salome.IDToObject(self.groups_sid[i])
            group.SetName(name)
            group.SetColor(colors[i])
            self._set_study_name(self.groups_sid[i], name)
            Gg.setDisplayMode(self.groups_sid[i],2)
        
        if salome.sg.hasDesktop():
            salome.sg.updateObjBrowser()

    def _set_study_name(self, obj_sid:str, name:str):
        try:
            sobj = salome.IDToSObject(obj_sid)
            logging.info("Set study name {} for object {}".format(name,sobj))
            sobjattr = Builder.FindOrCreateAttribute(sobj, "AttributeName")
            sobjattr.SetValue(name)
        except:
            logging.warning("Cannot set study name {} for object {}".format(name, obj_sid))

    def get_parents(self):
        return (salome.IDToObject(x.shape_sid) for x in self.items)
    
    def get_parents_name(self):
        names = [salome.IDToObject(x.shape_sid).GetName() for x in self.items]
        return tuple(names)
    
    def get_parents_sid(self):
        sid = [x.shape_sid for x in self.items]
        return tuple(sid)
    
    def get_groups(self):
        return (salome.IDToObejct(group) for group in self.groups_sid)
    
    def get_groups_sid(self):
        return self.groups_sid
    
    def get_group_names(self):
        grp_name= [salome.IDToObject(group).GetName() for group in self.groups_sid]
        return grp_name

    def set_type(self, type:str):
        if type in self.type_dict.keys():
            self.type = type

            type_str=ContactPair.type_dict[self.type]
            self.name = '_C'+type_str+str(self.id_instance)

            for i in range(len(self.groups_sid)):
                p_name = salome.IDToObject(self.groups_sid[i]).GetName()
                n_name = self.name+p_name[-1]
                group = salome.IDToObject(self.groups_sid[i])
                group.SetName(n_name)
                self._set_study_name(self.groups_sid[i], n_name)
        else:
            raise ValueError("Type not available. Available types are: {}".format(list(self.type_dict.keys())))
    
    def set_gap(self, gap:float):
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

            for i in range(len(self.groups_sid)):
                group=salome.IDToObject(self.groups_sid[i])
                p_name = group.GetName()
                n_name = p_name[:-1]+suffix[i] 
                group.SetColor(colors[i])
                group.SetName(n_name)
                self._set_study_name(self.groups_sid[i], n_name)
                Gg.setDisplayMode(self.groups_sid[i],2)

            if salome.sg.hasDesktop():
                salome.sg.updateObjBrowser()


        else:
            raise ValueError("Cannot swap master and slave. Master or slave are not defined")
        
    def add_items(self, group_item: GroupItem):
        if self.completed == False:
            self.items.append(group_item)
            self._create_physical_group(group_item)
            if len(self.items) > 1:
                self.completed = True
        else:
            raise ValueError("Cannot add item. Contact group is completed")
                   
class ContactManagement():
    """
    class for contact management at study level

    responsability:
    - create contact groups from tree
    - create contact groups from geometry selection
    - create contact groups from manually selection
    - deletion of contact groups from study inputs id
    - manage visibility from study inputs id
    - hide/show master and slave from study inputs id
    - export contact groups to list

    - @creation TODO:
                - swap master and slave if necessary
    """

    def __init__(self):
        self._contacts = []

    def __del__(self):
        for contact in self._contacts:
            del contact

    def get_contacts(self):
        return self._contacts

    def _get_subshape_from_group(self, group_sid:str):
        group_obj = salome.IDToObject(group_sid)
        indices = group_obj.GetSubShapeIndices()
        main_shape = group_obj.GetMainShape()
        return Geompy.SubShapes(main_shape, indices)
    
    # check if the contact already exists
    def _does_contact_pairs_exist(self, group_1:GroupItem, group_2:GroupItem):
        for pairs in self._contacts:
            if pairs.items[0] == group_1 and pairs.items[1] == group_2:
                print(pairs.items[0],group_1,pairs.items[1],group_2)
                return True
            elif pairs.items[0] == group_2 and pairs.items[1] == group_1:
                print(pairs.items[0],group_2,pairs.items[1],group_1)
                return True
            else:
                return False
    
    # method to be used with autotools
    def create_from_groupItem(self, group_1:GroupItem, group_2:GroupItem):
        # check if the contact already exists
        if self._does_contact_pairs_exist(group_1, group_2):
            return False
        
        else:
            group_pairs = ContactPair()
            group_pairs.add_items(group_1)
            group_pairs.add_items(group_2)
            self._contacts.append(group_pairs)
            # show the group
            self.show(group_pairs.id_instance)
            return True

    # create the contact group from the tree. Run once at script launch 
    # the naming convention is _C<type><id><MS>   
    # contact_from_tree is a dict with the following structure: {id: {master:GEOM_Obj, slave:GEOM_Obj}}
    # id is extracted from the name of the dict keys name
    def create_from_tree(self, contact_from_tree:dict()):
        for k,v in contact_from_tree.items():
            # create group item
            ci1 = GroupItem()
            ci2 = GroupItem()
            ci1.create_from_group(v['master'])
            ci2.create_from_group(v['slave'])

            if not self._does_contact_pairs_exist(ci1,ci2):
                # create contact pair
                id=v['pair_id']
                cp = ContactPair(id)
                cp.name = k
                # extract the type from the name
                type = k[2]
                reversed_dict = {v: k for k, v in ContactPair.type_dict.items()}
                cp.type = reversed_dict[type]
                cp.groups_sid=[v['master'],v['slave']]
                cp.items=[ci1,ci2]
                cp.completed = True
                cp.master = 0
                cp._reset_name_master_slave()
                self._contacts.append(cp)

                # show the group
                self.show(cp.id_instance)
                
    # create contact manually by selecting 2 groups. the original groups are deleted. New group are created using contactPair class. 
    def create_from_groupsID(self, group_1_sid:str, group_2_sid:str):

       # create group item
        grp1 = GroupItem()
        grp2= GroupItem()
        grp1.create_from_group(group_1_sid)
        grp2.create_from_group(group_2_sid)

        # check if the contact already exists
        if self._does_contact_pairs_exist(grp1, grp2):
            return False
        else:
            # create contact pair
            self.create_from_groupItem(grp1, grp2)

            # delete the original groups
            for id in (group_1_sid, group_2_sid):
                Gst.removeFromStudy(id)
                Gst.eraseShapeByEntry(id)
            return True

    def get_all_pairs(self):
        return self._contacts

    def to_table_model(self):
        model=[]
        for pair in self._contacts:
            d= list(pair.to_table_model().values())
            model.append(d)
        return model
    
    # get contact pairs
    def get_pair(self,id:int):
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
    def delete_by_id(self, id:int):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                self._contacts.remove(pairs)
                pairs.delete()
                break
   
    # show pairs 
    def show(self, id:int):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                pairs.visible = True
                for sid in pairs.get_groups_sid():
                    salome.sg.Display(sid)
                    Gg.setDisplayMode(sid,2)
                break

    # hide pairs                
    def hide(self, id:int):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                pairs.visible = False
                for sid in pairs.get_groups_sid():
                    Gg.eraseGO(sid)
                break

    # export contact pairs to list
    def export(self,file:str):
        pairs_list = [pairs.to_dict_for_export() for pairs in self._contacts]

        with open(file, 'w') as file:
            json.dump(pairs_list, file, indent=4)
        
    # swap master and slave
    def swap_master_slave_by_id(self,id:int):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                pairs.swap_master_slave()
                break

    # hide/show pairs
    def hideshow_by_id(self,id:int,value:bool):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                if value:
                    self.show(id)
                else:
                    self.hide(id)
                break

    # change type of contact
    def change_type_by_id(self,id:int,value:str):
        for pairs in self._contacts:
            if pairs.id_instance == id:
                pairs.set_type(value)
            
    # TODO check the fucntion some bug occur for some part !!!        
    def check_adjacent_slave_group(self):
        """
        check if each part has more than one adjacent slave group targeting to a different master part
        """
        parts_slave=dict()
        name_to_sid=dict()
        sid_to_name=dict()
        sid_to_pairs_id=dict()
        slave_target = dict() 
        
        # find all the parts and slave groups
        for contact in self._contacts:
            names = contact.get_group_names()
            groups_sid = contact.groups_sid

            name_to_sid[names[0]]=groups_sid[0]
            name_to_sid[names[1]]=groups_sid[1]

            sid_to_pairs_id[groups_sid[0]]=contact.id_instance
            sid_to_pairs_id[groups_sid[1]]=contact.id_instance
            parents = contact.get_parents_sid()


            for item in contact.items:
                if item.shape_sid not in parts_slave.keys():
                    parts_slave[item.shape_sid]=[]

            for i,name in enumerate(names):
                if name[-1]=='S':
                    parts_slave[item.shape_sid].append(name)
                if name[-1]=='M':
                    sn = name[:-1]+'S'
                    p_sid  = parents[i]
                    slave_target[sn]=p_sid

        sid_to_name={v:k for k,v in name_to_sid.items()}

        # reversed dict salve_part
        slave_part=dict()
        for k,v in parts_slave.items():
            for slave in v:
                if slave not in slave_part.keys():
                    slave_part[slave]=[]
                
                slave_part[slave].append(k)
        
        # check if the slave group are connected and not targeting the same parts
        to_reversed_id = list()

        for k,v in parts_slave.items():
            if len(v)>1:
                slave_sid = [name_to_sid[name] for name in v]
                comb = list(itertools.combinations(slave_sid, 2))
                for c in comb:
                    try:
                        obj1=salome.IDToObject(c[0])
                        obj2=salome.IDToObject(c[1])
                        isconnect, _, _ = Geompy.FastIntersect(obj1, obj2)

                        if isconnect:
                            s0 = sid_to_name[slave_sid[0]]
                            s1 = sid_to_name[slave_sid[1]]
                            s0_part = slave_target[s0]
                            s1_part = slave_target[s1]

                            if s0_part != s1_part:

                                # reversed the part with the lower ratio (slave_area/master_area)
                                s0_area = Geompy.BasicProperties(obj1)[1]
                                s1_area = Geompy.BasicProperties(obj2)[1]
                                m0_name = sid_to_name[c[0]][:-1]+'M'
                                m1_name = sid_to_name[c[1]][:-1]+'M'
                                m0_area = Geompy.BasicProperties(salome.IDToObject(name_to_sid[m0_name]))[1]
                                m1_area = Geompy.BasicProperties(salome.IDToObject(name_to_sid[m1_name]))[1]

                                if s0_area/m0_area >= s1_area/m1_area:
                                    to_reversed_id.append(sid_to_pairs_id[slave_sid[0]])
                                else:
                                    to_reversed_id.append(sid_to_pairs_id[slave_sid[1]])

                    except:
                        msg = "Cannot check if slave groups {} are connected. Check manually".format(c)
                        print(msg)
                        logging.warning(msg)
                                 
        # reversed
        ids = list(set(to_reversed_id))
        nb = len(ids)
        for id in ids:
            logging.info("Swap master and slave for contact pair {}".format(id))
            self.swap_master_slave_by_id(id)
        
        return nb
        






