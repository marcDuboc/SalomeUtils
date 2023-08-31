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
        "id": "1",
        "type": "bonded",
        "parts": [
            "P1",
            "P19"
        ],
        "surfaces": [
            "_C1S",
            "_C1M"
        ],
        "master": null,
        "gap": null,
        "completed": true
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

def getPair(data):
    pairs = dict()
    for item in data:
        if item["type"] in ("bonded", "sliding"):
            sid = getSlaveMasterIndex(item["surfaces"], re.compile(".*S$"))
            pairs[item['id']] = (item["parts_id"][sid], item["surfaces_id"][sid])
    return pairs

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

def parsePairs(pairs):
    """
    pairs is a dict with key as contact id and value as tuple of part_id and surface_id
    """
    common = list()

    # create combinaison of pairs two by two
    comb = itertools.combinations(pairs.keys(), 2)

    # check if pairs are identical
    for i in comb:
        if pairs[i[0]] == pairs[i[1]]:
            print("contact {} and {} are identical".format(i[0], i[1]))
            common.append(i)

    return combine_tuples(common)

def extractContact(data,pairs):
    bonded = []
    sliding = []
    frictionless = []
    friction = []
    idIndex= {item["id"]:i for i,item in enumerate(data)}

    for item in data:
        if item["type"] in ("bonded", "sliding"):
            # check master and slave index. master surface name end with M, slave surface name end with S
            # built tuple pair: (master by the part name, slave as surface name)
            if not item["id"] in getPairSet(pairs):
                mid = getSlaveMasterIndex(item["surfaces"], re.compile(".*M$"))
                sid = getSlaveMasterIndex(item["surfaces"], re.compile(".*S$"))
                master = item["parts"][mid]
                slave = item["surfaces"][sid]

                if item["type"] == "bonded":
                    if DEBUG:
                        bonded.append((master, slave))
                    else:
                        bonded.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=(master, )))

                elif item["type"] == "sliding":
                    sliding.append((master, slave,'dnor','dnor'))
            

        elif item["type"] == "friction":
            friction.append(None)

        elif item["type"] == "frictionless":
            frictionless.append(None)

    for item in pairs:
        slave = ""
        master = []

        # get the slave of surface of the first pair
        p0 = data[idIndex[item[0]]]
        contact_type = p0["type"]
        slave = p0["surfaces"][getSlaveMasterIndex(p0["surfaces"])]

        # append the master of all the pairs
        master.append(p0["parts"][getSlaveMasterIndex(p0["surfaces"], re.compile(".*M$"))])

        for i in item[1:]:
            p = data[idIndex[i]]
            master.append(p["parts"][getSlaveMasterIndex(p["surfaces"], re.compile(".*M$"))])
        
        if contact_type == "bonded":
            if DEBUG:
                bonded.append((master, slave))
            else:
                bonded.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=tuple(master)))

        elif contact_type == "sliding":
            if DEBUG:
                sliding.append((master, slave,'DNOR','DNOR'))
            else:
                sliding.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=tuple(master),DDL_MAIT = 'DNOR', DDL_ESCL = 'DNOR')) 


    return dict(bonded=bonded, sliding=sliding, friction=friction, frictionless=frictionless)

# ________________________________________________________________
# Main
# ________________________________________________________________

# replace the file with your json file absolute path
file = "E:\GIT_REPO\SalomeUtils\debug\contact.json"
data = loadJson(file)
pairs = getPair(data)
common = parsePairs(pairs)
contact=extractContact(data,common)

print("Contact Extracted")
print("==================")
for k,v in contact.items():
    print(k," : nb contacts" ,len(v))
print("\n")

bonded = contact["bonded"]
sliding = contact["sliding"]
friction = contact["friction"]
frictionless = contact["frictionless"]

for item in bonded:
    print("_F(GROUP_MA_ESCL=('{}'),GROUP_MA_MAIT=('{}')),".format(item[1],item[0]))