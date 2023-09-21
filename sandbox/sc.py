import sys
import salome
from salome.kernel.studyedit import getStudyEditor
from importlib import reload
sys.path.append('E:\GitRepo\SalomeUtils\scripts')

try:
    reload(sys.modules['bolt.properties'])
    reload(sys.modules['bolt.shape'])
except:
    pass

StudyEditor = getStudyEditor()
Gst = geomtools.GeomStudyTools(StudyEditor)

from bolt.shape import Parse, Nut, Screw, Thread, pair_screw_nut_threads, create_virtual_bolt,create_virtual_bolt_from_thread ,create_salome_line
from bolt.properties import get_properties
from bolt.aster import MakeComm

P = Parse()

nuts = []
screws = []
threads = []

for id in [f"0:1:1:5:{i}" for i in range(2,38)]:
    o = P.parse_obj(id)

    if type(o) == Nut:
        nuts.append(o)
    elif type(o) == Screw:

        screws.append(o)
    elif type(o) == list:
        for e in o:
            if type(e) == Thread:
                threads.append(e)
                
connections = pair_screw_nut_threads(screws,nuts,threads,tol_angle=0.01, tol_dist=0.01)

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
for v_bolt in v_bolts:
    create_salome_line("0:1:1:5",v_bolt)

#delete unwanted parts
for p in parts_to_delete:
    Gst.removeFromStudy(p)
    Gst.eraseShapeByEntry(p)

salome.sg.updateObjBrowser()

# write comm file
Comm = MakeComm()
data=Comm.process(v_bolts)

print(data)

#with open("E:\GitRepo\SalomeUtils\debug\Bolt.txt","w") as f:
    #for k,v in data:
    #    f.write("========="+str(k)+"========\n")
    #    f.write(v)
