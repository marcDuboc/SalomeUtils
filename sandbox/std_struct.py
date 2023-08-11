# -*- coding: utf-8 -*-
# explore data structure
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import salome

salome.salome_init()

# Detect current study
std_name = salome.myStudy._get_Name()
print("Current study: ", std_name)

# iterate through objects of the data tree with child iterator
root = salome.myStudy.FindComponentID("0:1:1") # get the root component
iter = salome.myStudy.NewChildIterator(root) # initialize from the component
iter.InitEx(True) # init recursive mode
while iter.More():
      c = iter.Value()
      print(c.GetID())
      iter.Next()
      pass

#TODO: get the name of the component store in dict with ID and type 
# target find all contact and part 


