# -*- coding: utf-8 -*-
# extract contact from json
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import sys
import json
import re
import itertools
from collections import defaultdict

# check if the script is run from Code Aster or from python
ASTER=False
try:
    import Utilitai
except:
    ASTER=True

"""
input json file as list of dict:
[
    {
        "id": 1,
        "type": "BONDED",
        "shapes": [
            "P1",
            "P2"
        ],
        "shapes_id": [
            "0:1:1:5:2",
            "0:1:1:5:3"
        ],
        "subshapes": [
            "_CA1M",
            "_CA1S"
        ],
        "subshapes_id": [
            "0:1:1:5:2:6",
            "0:1:1:5:3:6"
        ],
        "gap": null
    },...]

"""


# ________________________________________________________________
# Function
# ________________________________________________________________

class ContactItem:
    """Class to store contact information"""
    def __init__(self,data) -> None:
        #print(data)
        self.type = data["type"]
        self.id = data["id"]
        self.shapes = data["shapes"]
        self.shapes_id = data["shapes_id"]
        self.subshapes = data["subshapes"]
        self.subshapes_id = data["subshapes_id"]
        self.master_id = data["master_id"]
        #self.gap = data["gap"]

    def getSlaveName(self):
        if self.type in ["BONDED","SLIDING"]:
            return self.subshapes[1 if self.master_id == 0 else 0]
    
    def getMasterName(self):
        if self.type in ["BONDED","SLIDING"]:
            return self.shapes[self.master_id]
        
        elif self.type in ["FRICTION","FRICTIONLESS"]:
            return self.subshapes[self.master_id]

class Contacts:
    """Class to store and access all contact"""
    def __init__(self,data) -> None:
        self.ids = [item["id"] for item in data]
        for item in data:
            setattr(self,item["id"],ContactItem(item))
  
    def getAllContact(self):
        return [getattr(self,id) for id in self.ids]

    def getContact(self,id):
        return getattr(self,id)
    
    def getContactByType(self,type):
        return [item for item in self.getAllContact() if item.type == type]
    
    def getContactByShape(self,shape):
        return [item for item in self.getAllContact() if shape in item.shapes]
    
    def getContactBySubShape(self,subshape):
        return [item for item in self.getAllContact() if subshape in item.subshapes]
    
    def getContactByShapeId(self,shape_id):
        return [item for item in self.getAllContact() if shape_id in item.shapes_id]
    
    def getContactBySubShapeId(self,subshape_id):
        return [item for item in self.getAllContact() if subshape_id in item.subshapes_id]
    
    def getMasterSlave(self,id):
        contact = getattr(self,id)

        if contact.type in ["BONDED","SLIDING"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.shapes[master_index],"slave":contact.subshapes[slave_index]}
        
        elif contact.type in ["FRICTION","FRICTIONLESS"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.subshapes[master_index],"slave":contact.subshapes[slave_index]}
        
    def getMasterSlaveID(self,id):
        contact = getattr(self,id)
        if contact.type in ["BONDED","SLIDING"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.shapes_id[master_index],"slave":contact.subshapes_id[slave_index]}
        
        elif contact.type in ["FRICTION","FRICTIONLESS"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.subshapes_id[master_index],"slave":contact.subshapes_id[slave_index]}

    def getMasterSlaveName(self,id):
        contact = getattr(self,id)
        if contact.type in ["BONDED","SLIDING"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.shapes[master_index],"slave":contact.subshapes[slave_index]}
        
        elif contact.type in ["FRICTION","FRICTIONLESS"]:
            master_index= contact.master_id
            slave_index = 1 if master_index == 0 else 0
            return {"id":id,"master":contact.subshapes[master_index],"slave":contact.subshapes[slave_index]}

    def shapeNameFromShapeID(self):
        """return a dict of shape name from shape id"""
        d= defaultdict(list)
        for item in self.getAllContact():
                for i in (0,1):
                    d[item.shapes_id[i]].append(item.shapes[i])
        #remove duplicate
        for k,v in d.items():
            d[k] = list(set(v))[0]
        return d
    
    def subshapeNameFromSubshapeID(self):
        """return a dict of subshape name from subshape id"""
        d= defaultdict(list)
        for item in self.getAllContact():
                for i in (0,1):
                    d[item.subshapes_id[i]].append(item.subshapes[i])
        #remove duplicate
        for k,v in d.items():
            d[k] = list(set(v))[0]
        return d

class MakeComm:
    types = ["BONDED","SLIDING","FRICTION","FRICTIONLESS"]

    def __init__(self,data:list) -> None:
        self.Contacts = Contacts(data)
        self.bonded_start =[]
        self.sliding_start =[]
        self.friction_start =[]
        self.frictionless_start =[]
        self.end_F = "),\n"
        
    @staticmethod
    def _listNameToStrTuple(names:list) -> str:
        str_names =chr(40)
        if type(names) is str:
            str_names += "'{}',".format(names)

        elif type(names) is list:
            for n in names:
                str_names += "'{}',".format(n)
        str_names += chr(41)
        return str_names

    def strFBonded(self,master,slave):
        # master as [m1,m2,...] to m as ('m1','m1',...)
        m = MakeComm._listNameToStrTuple(master)
        s = MakeComm._listNameToStrTuple(slave)
        return "_F(GROUP_MA_ESCL={},GROUP_MA_MAIT={}),".format(s,m)

    def strFSliding(self,master,slave):
        # master as [m1,m2,...] to m as ('m1','m1',...)
        m = MakeComm._listNameToStrTuple(master)
        s = MakeComm._listNameToStrTuple(slave)
        return "_F(GROUP_MA_ESCL=('{}'),GROUP_MA_MAIT=('{}'),DDL_MAIT = 'DNOR', DDL_ESCL = 'DNOR'),".format(slave,master)          

    def strFFrictionless(self,master,slave):
        # master as [m1,m2,...] to m as ('m1','m1',...)
        m = MakeComm._listNameToStrTuple(master)
        s = MakeComm._listNameToStrTuple(slave)
        return "_F(GROUP_MA_ESCL=('{}'),GROUP_MA_MAIT=('{}')),".format(slave,master)  
    
    def strFFriction(self,master,slave):
        # master as [m1,m2,...] to m as ('m1','m1',...)
        m = MakeComm._listNameToStrTuple(master)
        s = MakeComm._listNameToStrTuple(slave)
        coulomb = 0.5
        e_t= 10000
        return "_F(GROUP_MA_ESCL=('{}'),GROUP_MA_MAIT=('{}'),COULOMB={}, E_T ={}),".format(slave,master,coulomb,e_t)  
    
    def regroupMasterbySlave(self, contacts:list):
        masterSalveId = defaultdict(list)
        #masterSalveId = dict()
        for item in contacts:
            #if item["slave"] not in masterSalveId.keys():
                #masterSalveId[item["slave"]] = [item["master"]]
            #else:
                masterSalveId[item["slave"]].append(item["master"])
        return masterSalveId
    
    def makeBonded(self,reGroup=True):
        str_bonded = 'bonded = (\n'
        bonded = self.Contacts.getContactByType("BONDED")
        bonded_id = [item.id for item in bonded]
        masterSalveIdList = [self.Contacts.getMasterSlaveID(i) for i in bonded_id]

        shapeName = self.Contacts.shapeNameFromShapeID()
        subshapeName = self.Contacts.subshapeNameFromSubshapeID()

        if reGroup:
            regrouped = self.regroupMasterbySlave(masterSalveIdList)
            for k, v in regrouped.items():
                slave_name = subshapeName[k]
                master_name = [shapeName[m] for m in v]
                str_bonded += '\t  ' + self.strFBonded(master_name,slave_name)+"\n"
        else:
            for item in bonded:
                c = self.Contacts.getMasterSlave(item.id)
                slave_name = c['slave']
                master_name = c['master']
                str_bonded += '\t  ' + self.strFBonded(master_name,slave_name)+"\n"

        return str_bonded + '\t  ' + ')\n'
    
    def makeSliding(self):
        str_slide = 'sliding = (\n'
        sliding = self.Contacts.getContactByType("SLIDING")

        for item in sliding:
            c = self.Contacts.getMasterSlave(item.id)
            str_slide += '\t  ' +(self.strFSliding(c['master'],c['slave']))

        return str_slide + '\t  ' + ')\n'

    def makeFriction(self):
        str_friction = 'friction = (\n'
        friction = self.Contacts.getContactByType("FRICTION")

        for item in friction:
            c = self.Contacts.getMasterSlave(item.id)
            str_friction += '\t  ' +(self.strFFriction(c['master'],c['slave']))

        return str_friction + '\t  ' + ')\n'
    
    def makeFrictionless(self):
        str_frictionless = 'frictionless = (\n'
        frictionless = self.Contacts.getContactByType("FRICTIONLESS")

        for item in frictionless:
            c = self.Contacts.getMasterSlave(item.id)
            str_frictionless += '\t  ' +(self.strFFrictionless(c['master'],c['slave']))

        return str_frictionless + '\t  ' + ')\n'
    
    def process(self,bonded_regroup_master=True):
        bonded = self.makeBonded(bonded_regroup_master)
        sliding = self.makeSliding()
        friction = self.makeFriction()
        frictionless = self.makeFrictionless()
        return bonded + sliding + friction + frictionless

if __name__ == '__main__' :
    # load the json file with respect of the platform (windows or linux). Input path as argument
    def loadJson(path):
        if sys.platform == "win32":
            path = path.replace("/", "\\")
        with open(path, 'r') as f:
            data = json.load(f)
        return data

    # ________________________________________________________________
    # Main
    # ________________________________________________________________

    # replace the file with your json file absolute path
    file = "E:\GIT_REPO\SalomeUtils\debug\contact.json"
    data = loadJson(file)
    comm = MakeComm(data)
    bb = comm.makeBonded()
    print(bb)



