# -*- coding: utf-8 -*-
# utilities for contact
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

from collections import defaultdict
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


class CombinePairs():
    """
    Combine pairs of tuples or lists
    input such as [('a', 'b'), ('b', 'c'), ('a', 'c'), ('d', 'f')]
    output such as [('a', 'b', 'c'), ('d', 'f')]
    """
    def __find(self,node, parent):
        if parent[node] != node:
            parent[node] = self.__find(parent[node], parent) # Compression de chemin
        return parent[node]

    def __union(self,node1, node2, parent):
        root1 = self.__find(node1, parent)
        root2 = self.__find(node2, parent)
        if root1 != root2:
            parent[root1] = root2

    def combine(self,pairs):
        # Initialisation des parents pour l'union-find
        parent = {x: x for pair in pairs for x in pair}

        # Construction du graphe par union-find
        for a, b in pairs:
            self.__union(a, b, parent)

        # Récupération des composants connexes
        groups = defaultdict(set)
        for node in parent:
            root = self.__find(node, parent)
            groups[root].add(node)

        return [tuple(sorted(group)) for group in groups.values()]    
