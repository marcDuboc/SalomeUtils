# -*- coding: utf-8 -*-
# module to navigate in the salome tree strucutre  
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import salome
import GEOM
from contact import logging

def id_to_tuple(id):
    """
    convert a string id to a tuple of integers
    """
    return tuple([int(i) for i in id.split(':')])

def tuple_to_id(tuple):
    """
    convert a tuple of integers to a string id
    """
    return ':'.join([str(i) for i in tuple])

class ObjectType():
    """reference 
    https://docs.salome-platform.org/7/gui/GEOM/geometrical_obj_prop_page.html"""

    SOLID = 26
    FACE = 24
    SHELL = 25
    COMPOUND = 27
    SUBSHAPE= 28
    GROUP = 37

class TreeItem():
    def __init__(self,id:tuple,name:str,type=int):
        self.id = id
        self.name = name
        self.type = type

    def parent_id(self):
        return self.id[:-1]
    
    def get_sid(self):
        return tuple_to_id(self.id)
    
    def __repr__(self):
        return f"TreeItem(id={self.id},name={self.name},type={self.type})"

class Tree:

    def __init__(self) -> None:
        self.root = '0:1:1'
        self.objects = None
        self.contact_pattern = re.compile(r"^_C[A-D]\d{1,4}[MS]$")

    def _check_type(self, obj_sid:str):
        """
        return True if the object is allowed
        """
        obj=salome.IDToObject(obj_sid)
        try:
            obj_type = obj.GetType()
            return True,obj_type

        except:
            return False,None
    
    def parse_tree_objects(self, compound_id:str() , component=None):
        """
        retrun a list of tree items within the compound_id
        """

        if component is not None:
            self.root=component

        compound_id = id_to_tuple(compound_id)
        length_compound_id = len(compound_id)

        objects = list()
        component= salome.myStudy.FindComponentID(self.root)
        iter = salome.myStudy.NewChildIterator(component)
        iter.InitEx(True) # init recursive mode

        while iter.More():
            sobj = iter.Value()
            id = id_to_tuple(sobj.GetID()) 

            # check if the object is whithin the main object
            test_id = id[:length_compound_id]

            if test_id == compound_id:
                ok, obj_type = self._check_type(sobj.GetID())
                if ok:
                    item=TreeItem(id,sobj.GetName(),obj_type)
                    objects.append(item)
            iter.Next()
            
        self.objects = objects
        return objects
    
    def get_parts(self,type=[ObjectType.SOLID,ObjectType.SUBSHAPE]):
        """
        return a list of parts
        """
        parts = list()
        for obj in self.objects:
            if obj.type in type:
                parts.append(obj)
        return parts
    
    def get_bolts(self):
        """
        return a dict of contact objects such as {name:{master:obj, slave:obj}}}
        master and slave are defined by the suffix M|S
        """
        pattern = self.contact_pattern
        
        # select contact objects
        contacts = list()
        for obj in self.objects:
            if re.match(pattern,obj.name) and obj.type == ObjectType.GROUP:
                contacts.append(obj)

        # regroup contacts by name (without the suffix M|S)
        contacts_by_name = dict()
        for contact in contacts:
            name = contact.name[:-1]
            if name not in contacts_by_name:
                contacts_by_name[name] = dict(master=None,slave=None)
            if contact.name[-1] == 'M':
                contacts_by_name[name]['master'] = tuple_to_id(contact.id)
            elif contact.name[-1] == 'S':
                contacts_by_name[name]['slave'] = tuple_to_id(contact.id)

        # sort the dict by id = int(name[3:])
        #add the pair_id to the dict
        for name in contacts_by_name:
            contacts_by_name[name]['pair_id'] = int(name[3:])

        contacts_by_name = dict(sorted(contacts_by_name.items(), key=lambda item: int(item[0][3:])))
        
        return contacts_by_name
        
    def get_by_type(self,type:int):
        """
        return a list of objects of type
        """
        objects = list()
        for obj in self.objects:
            if obj.type == type:
                objects.append(obj)
        return objects


