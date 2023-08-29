# to set the name in the gui
import salome

# id of the object in the tree
ID=("0:1:1:5")


#______________________________________________________________________________
#  Set in the study
#______________________________________________________________________________

# get the study builder
builder = salome.myStudy.NewBuilder()

# get the object Study object
obj = salome.IDTSObject("0:1:1:5")

# get the attribute and set the value
sobjattr = builder.FindOrCreateAttribute(obj, "AttributeName")
sobjattr.SetValue("NewName")

# update the object browser
salome.sg.updateObjBrowser()


#______________________________________________________________________________
#  Set in GEOM
#______________________________________________________________________________

# Get the GEOM object
obj = salome.IDToObject(ID)

# Set the name
obj.SetName("NewName")


#______________________________________________________________________________
#  Altenrative Both study and GEOM
#______________________________________________________________________________

# get the GEOM object
obj = salome.IDToObject(ID)

# convert goem object to study object
sobj = salome.ObjectToSObject(obj)

# Set the name in goem
obj.SetName("NewName")

# Set the name in the study
sobjattr = builder.FindOrCreateAttribute(sobj, "AttributeName")
sobjattr.SetValue("NewName")

# update the object browser
salome.sg.updateObjBrowser()

