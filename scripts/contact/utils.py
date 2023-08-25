# -*- coding: utf-8 -*-
# utilities for contact scripts
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import salome
from salome.geom import geomtools

# get object => IDL:SALOMEDS/SObject:1.0
# id as "0:1:1..."
def get_SALOMEDS_SObject(id):
    return geomtools.IDToSObject(id)

# get object => IDL:GEOM/GEOM_Object:1.0
# id as "0:1:1..."
def get_GEOM_Object(id):
    return salome.myStudy.FindObjectID(id).GetObject()