# -*- coding: utf-8 -*-
# module to navigate in the salome tree strucutre  
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import salome
import GEOM


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

class TreeItem():
    def __init__(self,id:tuple,name:str,geom_obj:object):
        self.id = id
        self.name = name
        self.obj = geom_obj

    def parent_id(self):
        return self.id[:-1]
    
    def __repr__(self):
        return f'name={self.name}, id={tuple_to_id(self.id)}'

class Tree:
    def __init__(self) -> None:
        self.root = '0:1:1'
        self.objects = None
        self.contact_pattern = re.compile(r"^_C[A-D]\d{1,4}[MS]$")
    
    def get_objects(self, compound_id='0:1:1' , component=None):
        """
        retrun a list of tree items within the compound_id
        """

        if component is not None:
            self.root=component

        compound_id = id_to_tuple(compound_id)
        length_compound_id = len(compound_id)

        self.objects = list()
        component= salome.myStudy.FindComponentID(self.root)
        iter = salome.myStudy.NewChildIterator(component)
        iter.InitEx(True) # init recursive mode

        while iter.More():
            sobj = iter.Value()
            id = id_to_tuple(sobj.GetID()) 

            # check if the object is whithin the main object
            test_id = id[:length_compound_id]

            if test_id == compound_id:
                obj = sobj.GetObject()
                name = sobj.GetName()
                if name:
                    item=TreeItem(id,name,obj)
                    self.objects.append(item)

            iter.Next()

        return self.objects
    
    def parse_for_contact(self):
        """
        return a dict of contact objects such as {name:{master:obj, slave:obj}}}
        master and slave are defined by the suffix M|S
        """
        pattern = self.contact_pattern
        
        # select contact objects
        contacts = list()
        for obj in self.objects:
            if re.match(pattern,obj.name):
                contacts.append(obj)

        # regroup contacts by name (without the suffix M|S)
        contacts_by_name = dict()
        for contact in contacts:
            name = contact.name[:-1]
            if name not in contacts_by_name:
                contacts_by_name[name] = dict(master=None,slave=None)
            if contact.name[-1] == 'M':
                contacts_by_name[name]['master'] = contact.obj
            elif contact.name[-1] == 'S':
                contacts_by_name[name]['slave'] = contact.obj

        # sort the dict by id = int(name[3:])
        contacts_by_name = dict(sorted(contacts_by_name.items(), key=lambda item: int(item[0][3:])))
        
        return contacts_by_name
        



