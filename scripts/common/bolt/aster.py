import numpy as np
from collections import defaultdict 
from .shape import VirtualBolt
from common.properties import Point, Vector
from common import logging

class MakeComm:

    @staticmethod
    def _listNameToStrTuple(names) -> str:
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
        dft = f"_F(GROUP_MA_AXE={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        GROUP_NO_ORIG={MakeComm._listNameToStrTuple(no_master)},\n\
        LONGUEUR={contact_height},\n\
        NOM='{name_grp_no}',\n\
        OPTION='TUNNEL',\n\
        RAYON={contact_radius},\n\
        TOUT='OUI'),\n"
        return dft
    
    @staticmethod
    def str_affe_model(ma_bolt):
        afm = f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        MODELISATION='POU_D_T',\n\
        PHENOMENE='MECANIQUE'),\n"
        return afm
    
    @staticmethod
    def str_affe_cara(ma_bolt:str, bolt_radius:float):
        afc = f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        SECTION='CERCLE',\n\
        VARI_SECT='CONSTANT',\n\
        CARA=('R', ),\n\
        VALE={bolt_radius}),\n"
        return afc
    
    @staticmethod
    def str_pre_espi(ma_bolt:str, bolt_radius:float,  modulus:2.1e5):
        epsi = -(np.pi*bolt_radius**2)/modulus
        pre = f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
        EPX = {epsi},)\n"
        return pre

    @staticmethod
    def str_rbe3(no_slave, no_master):
        rbe = f"_F(GROUP_NO_ESCL={MakeComm._listNameToStrTuple(no_slave)},\n\
        GROUP_NO_MAIT={MakeComm._listNameToStrTuple(no_master)},\n\
        DDL_ESCL=('DX-DY-DZ',),\n\
        DDL_MAIT=('DX','DY','DZ','DRX','DRY','DRZ'),\n\
        COEF_ESCL=(1.0,)),\n"
        return rbe
    
    @staticmethod
    def str_post_releve_t(ma_bolt:str):
        post = f"_F(GROUP_NO=('{ma_bolt}', ),\n\
        INTITULE='{ma_bolt}',\n\
        NOM_CHAM='SIEF_ELNO',\n\
        OPERATION=('EXTRACTION', ),\n\
        RESULTAT=BOLTS,\n\
        TOUT_CMP='OUI',\n\
        TOUT_ORDRE='OUI'),\n"
        return post
    
    def process(self, bolts:list) -> str:
        comm = dict(CREA_GROUP_NO="", 
                    AFFE_MODELE="",
                    AFFE_CARA_ELEM="" , 
                    LIAISON_RBE3="",
                    CALC_CHAMP="",
                    POST_RELEVE_T="",)
        grp_bolt_name=[]
        grp_bolt_size=defaultdict() # {radius_str: [bolt_name_1,bolt_name_2,...]}

        for bolt in bolts:
            if isinstance(bolt,VirtualBolt):

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

                # group size
                if str(radius) not in grp_bolt_size:
                    grp_bolt_size[str(radius)] = [ma_bolt]
                else:
                    grp_bolt_size[str(radius)].append(ma_bolt)

                
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
                
                comm["LIAISON_RBE3"] += MakeComm.str_rbe3(grp_no_start, start_name)

                comm["LIAISON_RBE3"] += MakeComm.str_rbe3(grp_no_end, end_name)

                comm["POST_RELEVE_T"] += MakeComm.str_post_releve_t(ma_bolt)
                
        comm["AFFE_MODELE"] += MakeComm.str_affe_model(grp_bolt_name)

        for k,v in grp_bolt_size.items():
            comm["AFFE_CARA_ELEM"]+= MakeComm.str_affe_cara(v, float(k))
            comm["CALC_CHAMP"] += MakeComm.str_pre_espi(v, float(k), 2.1e5)

        return comm
    
    def to_str(self, comm:dict) -> str:
        str_comm = ""
        for key, value in comm.items():
            str_comm += f"# {key}==========================\n"
            str_comm += f"{key} = {value}\n\n"
            
        return str_comm
    


