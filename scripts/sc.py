import sys
from importlib import reload
sys.path.append('E:\GIT_REPO\SalomeUtils\scripts')

try:
    reload(sys.modules['bolt.properties'])
    reload(sys.modules['bolt.shape'])
    reload(sys.modules['bolt.aster'])
except:
    pass

import salome
from salome.kernel.studyedit import getStudyEditor
from salome.geom import geomtools, geomBuilder
StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)
Geompy = geomBuilder.New()

from bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
from bolt.properties import get_properties
from bolt.aster import MakeComm

P = Parse()

nuts = []
screws = []
threads = []

for id in [f"0:1:1:5:{i}" for i in range(2,51)]:
    o = P.parse_obj(id)

    if type(o) == Nut:
        nuts.append(o)
    elif type(o) == Screw:

        screws.append(o)
    elif type(o) == list:
        for e in o:
            if type(e) == Thread:
                threads.append(e)
                
connections = pair_screw_nut_threads(screws,nuts,threads,tol_angle=0.01, tol_dist=0.1)

# create virtual bolts
v_bolts = []
parts_to_delete = []

for bolt in connections['bolts']:
    v_bolt = create_virtual_bolt(bolt)

    if not v_bolt is None:
        v_bolts.append(v_bolt)    
        for p in bolt:
            parts_to_delete.append(p.part_id)

for threads in connections['threads']:
    v_bolt = create_virtual_bolt_from_thread(threads)

    if not v_bolt is None:
        v_bolts.append(v_bolt)
        for p in threads:
            if type(p) == Screw:
                    parts_to_delete.append(p.part_id)

# build geom in salome
lines_ids = []
for v_bolt in v_bolts:
    lines_ids.append(create_salome_line(v_bolt))

vbf= Geompy.NewFolder('Virtual Bolts')
Geompy.PutListToFolder(lines_ids, vbf)

# refresh viewer
salome.sg.updateObjBrowser()

# delete parts
delete=True
if delete:
    for grp in parts_to_delete:
        Gst.removeFromStudy(grp)
        Gst.eraseShapeByEntry(grp)


# write comm file
Comm = MakeComm()
data=Comm.process(v_bolts)

with open("E:\GIT_REPO\SalomeUtils\debug\Bolt.txt","w") as f:
    for k,v in data.items():
        f.write("#========="+str(k)+"========\n")
        f.write(v)
        f.write("\n\n")
