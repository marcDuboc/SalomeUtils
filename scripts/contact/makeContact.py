# -*- coding: utf-8 -*-
# extract contact from json
# License: LGPL v 2.1
# Autor: Marc DUBOC
# Version: 11/08/2023

import json
import sys
import os

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

# extract the contact from the json file
def extractContact(data):
    bonded = []
    sliding = []
    frictionless = []
    friction = []

    for item in data:
        if item["type"] in ("bonded","sliding"):
            # check master and slave index. master surface name end with M, slave surface name end with S
            # built tuple pair: (master by the part name, slave as surface name)

            for i in range(len(item["parts"])):
                if item["surfaces"][i][-1] == "M":
                    master = item["parts"][i]
                else:
                    slave = item["surfaces"][i]

            if item["type"] == "bonded":
                #bonded.append(_F(GROUP_MA_ESCL=(slave, ),GROUP_MA_MAIT=(master, )))
                bonded.append((master, slave)) 

            elif item["type"] == "sliding":
                sliding.append((master, slave))   

        elif item["type"] == "friction":
            friction.append(None)

        elif item["type"] == "frictionless":
            frictionless.append(None)

    return dict(bonded=bonded, sliding=sliding, friction=friction, frictionless=frictionless)

# ________________________________________________________________
# Main
# ________________________________________________________________


# replace the file with your json file absolute path
file = "E:\GIT_REPO\SalomeUtils\scripts\contact\contact.json"
data = loadJson(file)
contact = extractContact(data)

print("Contact Extracted")
print("==================")
for k,v in contact.items():
    print(k," : nb contacts" ,len(v))
print("\n")

bonded = contact["bonded"]
sliding = contact["sliding"]
friction = contact["friction"]
frictionless = contact["frictionless"]

print("Bonded 38", bonded[38])

