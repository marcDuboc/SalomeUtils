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
DEBUG=False
try:
    import Utilitai
except:
    DEBUG=True

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

# load the json file with respect of the platform (windows or linux). Input path as argument
def loadJson(path):
    if sys.platform == "win32":
        path = path.replace("/", "\\")
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def getSlaveMasterIndex(surfaces, pattern=re.compile(".*S$")):
    # return the postion of the slave
    index = next((i for i, string in enumerate(surfaces) if pattern.match(string)), None)
    return index

def get_pair_and_dict_id(data): 
    """
    return a dict with key as contact id and value as tuple of part_id and surface_id
    pairs = {id_contact:(shape_id of the master, subshape_id of the slave)}
    dict_id = {id:name}
    """
    pairs = dict()
    dict_id = dict()

    for item in data:
        if item["type"] in ("BONDED", "SLIDING"):
            mid=0
            sid = getSlaveMasterIndex(item["subshapes"], re.compile(".*S$"))
            if sid == 0:
                mid = 1
            pairs[item['id']] = (item["shapes_id"][mid], item["subshapes_id"][sid])
            dict_id[item['subshapes_id'][sid]] = item['subshapes'][sid]
            dict_id[item['shapes_id'][mid]] = item['shapes'][mid]

    return pairs,dict_id

def getPairSet(pairs):
    # return a list of all the value contained in the pairs
    result_set = {item for t in pairs for item in t}
    return list(result_set)

def find(node, parent):
    if parent[node] != node:
        parent[node] = find(parent[node], parent)  # Compression de chemin
    return parent[node]

def union(node1, node2, parent):
    root1 = find(node1, parent)
    root2 = find(node2, parent)
    if root1 != root2:
        parent[root1] = root2

def combine_tuples(pairs):
    # Initialisation des parents pour l'union-find
    parent = {x: x for pair in pairs for x in pair}

    # Construction du graphe par union-find
    for a, b in pairs:
        union(a, b, parent)

    # Récupération des composants connexes
    groups = defaultdict(set)
    for node in parent:
        root = find(node, parent)
        groups[root].add(node)

    return [tuple(sorted(group)) for group in groups.values()]

def parsePairs(pairs,dict_id):
    """
    pairs is a dict with key as contact id and value as tuple of part_id and surface_id
    """
    group_per_slave= dict() #k:slave, v: list of master
    common = []

    # check if pairs are identical
    for _,v in pairs.items():
        if v[1] not in group_per_slave.keys():
            group_per_slave[v[1]] = []
        group_per_slave[v[1]].append(v[0])

    for k,v in group_per_slave.items():
        d=dict(slave= dict_id[k], master=[dict_id[i] for i in v])
        common.append(d)

    return common

def extractContact(data,pairs):
    bonded = []
    sliding = []
    frictionless = []
    friction = []
    idIndex= {item["id"]:i for i,item in enumerate(data)}

    for item in data:
        if item["type"] in ("BONDED", "SLIDING"):
            # check master and slave index. master surface name end with M, slave surface name end with S
            # built tuple pair: (master by the part name, slave as surface name)
            if not item["id"] in getPairSet(pairs):
                mid = getSlaveMasterIndex(item["subshapes"], re.compile(".*M$"))
                sid = getSlaveMasterIndex(item["subshapes"], re.compile(".*S$"))
                master = item["shapes"][mid]
                slave = item["subshapes"][sid]

                if item["type"] == "BONDED":
                    if DEBUG:
                        sliding.append((master, slave))
                    else:
                        bonded.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=(master, )))

                elif item["type"] == "SLIDING":
                    sliding.append((master, slave,'dnor','dnor'))
            

        elif item["type"] == "FRICTION":
            friction.append(None)

        elif item["type"] == "FRICTIONLESS":
            frictionless.append(None)

    for item in pairs:
        slave = ""
        master = []

        # get the slave of surface of the first pair
        p0 = data[idIndex[item[0]]]
        contact_type = p0["type"]
        slave = p0["subshapes"][getSlaveMasterIndex(p0["subshapes"])]

        # append the master of all the pairs
        master.append(p0["shapes"][getSlaveMasterIndex(p0["subshapes"], re.compile(".*M$"))])

        for i in item[1:]:
            p = data[idIndex[i]]
            master.append(p["shapes"][getSlaveMasterIndex(p["subshapes"], re.compile(".*M$"))])
        
        if contact_type == "BONDED":
            if DEBUG:
                bonded.append((master, slave))
            else:
                bonded.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=tuple(master)))

        elif contact_type == "SLIDING":
            if DEBUG:
                sliding.append((master, slave,'DNOR','DNOR'))
            else:
                sliding.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=tuple(master),DDL_MAIT = 'DNOR', DDL_ESCL = 'DNOR')) 


    return dict(bonded=bonded, sliding=sliding, friction=friction, frictionless=frictionless)

# ________________________________________________________________
# Main
# ________________________________________________________________

# replace the file with your json file absolute path
file = "E:\GitRepo\SalomeUtils\debug\contact.json"
data = loadJson(file)
pair,dict_id = get_pair_and_dict_id(data)
print(dict_id)
common = parsePairs(pair,dict_id)
for k in common:
    print(k)
"""contact=extractContact(data,common)
print('pairs',pairs)
print('common',common)

print("Contact Extracted")
print("==================")
for k,v in contact.items():
    print(k," : nb contacts" ,len(v))
print("\n")

bonded = contact["bonded"]
sliding = contact["sliding"]
friction = contact["friction"]
frictionless = contact["frictionless"]

for item in sliding:
    print("_F(GROUP_MA_ESCL=('{}'),GROUP_MA_MAIT=('{}')),".format(item[1],item[0]))"""