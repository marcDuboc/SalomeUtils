
class ContactItem():
    def __init__(self, id, part, part_id, surface, surface_id):
        self.id = id
        self.type = "bonded"  # bonded, sliding, separation
        self.parts = [None, None]  # part name as string
        self.parts_id = [None, None]  # part id as int
        self.surfaces = [None, None]  # surface name as string
        self.surfaces_id = [None, None]  # surface id as int
        self.master = None  # master number as surface index
        self.gap = None  # gap value as float
        self.completed = False  # contact completed: both part and surface are defined

        self.parts[0] = part
        self.surfaces[0] = surface
        self.parts_id[0] = part_id
        self.surfaces_id[0] = surface_id

    def __str__(self):
        return "{id: " + str(self.id) + " type: " + self.type + ""

    def __repr__(self) -> str:
        return "{id: " + str(self.id) + ", completed:"+str(self.completed) + ", type: " + self.type + ", parts:[" + str(self.parts[0])+','+str(self.parts[1]) + "], parts_id:[" + str(self.parts_id[0])+','+str(self.parts_id[1]) + "], surfaces:[" + str(self.surfaces[0])+','+str(self.surfaces[1]) + "], surfaces_id:[" + str(self.surfaces_id[0])+','+str(self.surfaces_id[1]) + "]}"

    def isValid(self):
        if self.id != None:
            return True
        else:
            return False

    def to_dict(self):
        return {"id": self.id, "type": self.type, "parts": self.parts, "parts_id": self.parts_id, "surfaces": self.surfaces, "surfaces_id": self.surfaces_id, "master": self.master, "gap": self.gap, "completed": self.completed}

    def swap_master_slave(self):
        if self.master == 0:
            self.master = 1
        else:
            self.master = 0

    def add(self, part, part_id, surface, surface_id):
        if self.surfaces[0] != surface and self.completed == False:
            self.parts[1] = part
            self.parts_id[1] = part_id
            self.surfaces[1] = surface
            self.surfaces_id[1] = surface_id
            self.completed = True
