# -*- coding: utf-8 -*-
# explore data structure
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import re
import salome
from salome.geom import geomBuilder,geomtools
salome.salome_init()

re_name= re.compile(r'_C\d+(.+?)')

# Detect current study
std_name = salome.myStudy._get_Name()
print("Current study: ", std_name)

studies = salome.myStudyManager.GetOpenStudies()
#file = salome.myStudy.path()  
#print(file)

# get object => IDL:GEOM/GEOM_Object:1.0
def get_GEOM_Object(id):
      return salome.myStudy.FindObjectID(id).GetObject()

#get name componenent
def get_name(id):
      return get_SALOMEDS_SObject(id).GetName()

# get object => IDL:SALOMEDS/SObject:1.0
def get_SALOMEDS_SObject(id):
      return geomtools.IDToSObject(id)

def get_Parent(id):
      return geomtools.IDToSObject(id).GetFather()

# iterate through objects of the data tree with child iterator return child and parent id and name
root = salome.myStudy.FindComponentID("0:1:1") # get the root component
iter = salome.myStudy.NewChildIterator(root) # initialize from the component
iter.InitEx(True) # init recursive mode
while iter.More():
      c = iter.Value()
      p = get_Parent(c.GetID())
      if re_name.match(c.GetName()):
                # check if id exist in contact list
                print(c.GetName(),p.GetName())

      #print(c.GetID(),c.GetName(),p.GetID(),p.GetName())
      iter.Next()
      pass



