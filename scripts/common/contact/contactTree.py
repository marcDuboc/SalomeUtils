# -*- coding: utf-8 -*-
# module to navigate in the salome tree strucutre  
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import re
import salome
import GEOM
from common.tree import Tree,tuple_to_id
from common import logging


class ContactTree(Tree):
    contact_pattern = re.compile(r"^_C[A-D]\d{1,4}[MS]$")

    def get_contacts(self):
        """
        return a dict of contact objects such as {name:{master:obj, slave:obj}}}
        master and slave are defined by the suffix M|S
        """
        pattern = self.contact_pattern
        
        # select contact objects
        contacts = list()
        for obj in self.objects:
            if re.match(pattern,obj.name) and obj.is_group==True:
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

        #add the pair_id to the dict
        for name in contacts_by_name:
            contacts_by_name[name]['pair_id'] = int(name[3:])

        contacts_by_name = dict(sorted(contacts_by_name.items(), key=lambda item: int(item[0][3:])))
        
        return contacts_by_name
        


