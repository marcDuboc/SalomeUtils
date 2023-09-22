from bolt.shape import VirtualBolt
from bolt.properties import Point, Vector
from contact import logging

class MakeComm:

    @staticmethod
    def _listNameToStrTuple(names) -> str:
        logging.debug("names: {}".format(names))
        logging.debug("type(names): {}".format(type(names)))

        str_names =chr(40)
        if type(names) is str:
            str_names += "'{}',".format(names)

        elif type(names) is list:
            for n in names:
                if type(n) is str:
                    str_names += "'{}',".format(n)

        str_names += chr(41)
        return str_names
    
    @staticmethod
    def str_defi_group_tunnel(ma_bolt:str, no_master:str, contact_height:float, contact_radius:float, name_grp_no:str) -> str:
        dft = f"\t_F(GROUP_MA_AXE={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        GROUP_NO_ORIG={MakeComm._listNameToStrTuple(no_master)},\n\
        LONGUEUR={contact_height},\n\
        NOM='{name_grp_no}',\n\
        OPTION='TUNNEL',\n\
        RAYON={contact_radius},\n\
        TOUT='OUI'),\n"
        return dft
    
    @staticmethod
    def str_affe_model(ma_bolt):
        afm = f"\t_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        MODELISATION='POU_D_T',\n\
        PHENOMENE='MECANIQUE'),\n"
        return afm
    
    @staticmethod
    def str_affe_cara(ma_bolt:str, bolt_radius:float):
        afc = f"\t_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        SECTION='CERCLE',\n\
        VARI_SECT='CONSTANT',\n\
        CARA=('R', ),\n\
        VALE={bolt_radius}),\n"
        return afc

    @staticmethod
    def str_rbe3(no_slave, no_master):
        rbe = f"\t_F(GROUP_NO_ESCL={MakeComm._listNameToStrTuple(no_slave)},\n\
        GROUP_NO_MAIT={MakeComm._listNameToStrTuple(no_master)},\n\
        DDL_ESCL=('DX-DY-DZ',),\n\
        DDL_MAIT=('DX','DY','DZ','DRX','DRY','DRZ'),\n\
        COEF_ESCL=(1.0,)),\n"

        return rbe
    
    def process(self, bolts:list) -> str:
        comm = dict(CREA_GROUP_NO="", 
                    AFFE_MODELE="",
                    AFFE_CARA_ELEM="" , 
                    LIAISON_RBE3="")
        grp_bolt_name=[]
        for bolt in bolts:
            if type(bolt) is VirtualBolt:

                # group name
                ma_bolt = bolt.get_bolt_name()
                start_name = bolt.get_start_name()
                end_name = bolt.get_end_name()
                grp_bolt_name.append(ma_bolt)

                # variable
                radius = bolt.radius
                start_radius = bolt.start_radius
                start_height = bolt.start_height
                end_radius = bolt.end_radius
                end_height = bolt.end_height
                
                grp_no_start = bolt.get_start_name()+"S"
                grp_no_end = bolt.get_end_name()+"S"

                
                comm["CREA_GROUP_NO"] += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             start_name, 
                                                             start_height, 
                                                             start_radius, 
                                                             grp_no_start)

                comm["CREA_GROUP_NO"] += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             end_name, 
                                                             end_height, 
                                                             end_radius, 
                                                             grp_no_end)

                comm["AFFE_CARA_ELEM"]+= MakeComm.str_affe_cara(ma_bolt, radius)

                comm["LIAISON_RBE3"] += MakeComm.str_rbe3(grp_no_start, start_name)

                comm["LIAISON_RBE3"] += MakeComm.str_rbe3(grp_no_end, 
                                          end_name)
                
        comm["AFFE_MODELE"] += MakeComm.str_affe_model(grp_bolt_name)

        return comm
    


