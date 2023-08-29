# -*- coding: utf-8 -*-
# utilities for contact scripts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import salome
builder = salome.myStudy.NewBuilder()

# get object => IDL:SALOMEDS/SObject:1.0
# id as "0:1:1..."
def get_SALOMEDS_SObject(id):
    return salome.IDToSObject(id)

# get object => IDL:GEOM/GEOM_Object:1.0
# id as "0:1:1..."
def get_GEOM_Object(id):
    return salome.IDToObject(id)

# convert object => IDL:GEOM/GEOM_Object:1.0
def convertObjToSobj(obj):
    return salome.ObjectToSOBJ(obj)

#rename object in study and geom from itself
def rename_from_obj(obj, name):
    obj.SetName(name)
    sobj=salome.ObjectToSObject(obj)
    builder.FindOrCreateAttribute(sobj, "AttributeName").SetValue(name)

#rename object in study and geom from id
def rename_from_id(id, name):
    obj = salome.IDToObject(id)
    obj.SetName(name)
    sobj=salome.ObjectToSObject(obj)
    builder.FindOrCreateAttribute(sobj, "AttributeName").SetValue(name)
