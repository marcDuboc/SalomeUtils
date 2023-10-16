import numpy as np
from collections import defaultdict 
from common.bolt.data import VirtualBolt
#from common import logging

class MakeComm:

    start_rbe="PROP = AFFE_CARA_ELEM(POUTRE=("
    end_rbe="),\nMODELE='your_model')"

    start_pre = "BOLTS_PRE = AFFE_CHAR_MECA(PRE_EPSI=("
    end_pre = "),\nMODELE='your_model')"

    start_prop="PROP = AFFE_CARA_ELEM(POUTRE=("
    end_prop="),\nMODELE='your_model')"

    start_no="'your_mesh' = DEFI_GROUP(CREA_GROUP_NO=("
    end_no="),\nreuse='your_mesh')"

    start_elno="BOLTS_ELNO = CALC_CHAMP(" 
    end_elno="),\nMODELE='your_model',\nRESULTAT='your_result',\nCARA_ELEM=PROP,\nCHAM_MATER='your_material_field')"

    start_releve="TAB_BOLTS = POST_RELEVE_T(ACTION=("
    end_releve="),\nRESULTAT=BOLTS_ELNO,\nMODELE='your_model')"

    start_model='"your_model" = AFFE_MODELE(AFFE=('
    end_model='),\nMAILLAGE="your_mesh",)'

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
        dft = (f"_F(GROUP_MA_AXE={MakeComm._listNameToStrTuple(ma_bolt)},\n"
               f"   GROUP_NO_ORIG={MakeComm._listNameToStrTuple(no_master)},\n"
               f"   LONGUEUR={contact_height},\n"
               f"   NOM='{name_grp_no}',\n"
                "   OPTION='TUNNEL',\n"
               f"   RAYON={contact_radius},\n"
                "   TOUT='OUI'),\n")
        return dft
    
    @staticmethod
    def str_affe_model(ma_bolt):
        afm = ("_F(MODELISATION='3D',\n"
               "   PHENOMENE='MECANIQUE',\n"
               "   TOUT='OUI'),\n"
              f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n"
               "   MODELISATION='POU_D_E,\n"
               "   PHENOMENE='MECANIQUE'),\n")
        return afm
    
    @staticmethod
    def str_affe_cara(ma_bolt:str, bolt_radius:float):
        afc = (f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n"
                "   SECTION='CERCLE',\n"
                "   VARI_SECT='CONSTANT',\n"
                "   CARA=('R', ),\n"
               f"   VALE={bolt_radius}),\n")
        return afc
    
    @staticmethod
    def str_pre_espi(ma_bolt:str, bolt_radius:float,preload:float, modulus:2.1e5):
        epsi = 0.0
        if preload > 0.0:
            sigma = (preload/(np.pi*bolt_radius**2))*1E3
            epsi = sigma/modulus
        pre = (f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n"
               f"   EPX = {epsi},)\n")
        return pre

    @staticmethod
    def str_rbe3(no_slave, no_master):
        rbe = (f"_F(GROUP_NO_ESCL={MakeComm._listNameToStrTuple(no_slave)},\n"
               f"   GROUP_NO_MAIT={MakeComm._listNameToStrTuple(no_master)},\n"
                "   DDL_ESCL=('DX-DY-DZ',),\n"
                "   DDL_MAIT=('DX','DY','DZ','DRX','DRY','DRZ'),\n"
                "   COEF_ESCL=(1.0,)),\n")
        return rbe
    
    @staticmethod
    def str_bolts_elno(ma_bolts:list):
        elno = (f"_F(GROUP_MA={MakeComm._listNameToStrTuple(ma_bolts)},\n"
                 "   CONTRAINTE='SIEF_ELNO',\n")
        return elno

    @staticmethod
    def str_post_releve_t(ma_bolt:str):
        post = (f"_F(GROUP_NO=('{ma_bolt}', ),\n"
                 "   INTITULE='{ma_bolt}',\n"
                 "   NOM_CHAM='SIEF_ELNO',\n"
                 "   OPERATION='EXTRACTION',\n"
                 "   RESULTAT=BOLTS,\n"
                 "   TOUT_CMP='OUI',\n"
                 "   TOUT_ORDRE='OUI'),\n")
        return post
    
    def write_concept(self,start:str, end:str, data:str):
        sz = len(start)

        dataline = data.splitlines()
        data_spaced = start
        for i in range(len(dataline)):
            if i == 0:
                data_spaced += dataline[i] + '\n'
            else:
                data_spaced += ' '*sz + dataline[i] + '\n'

        end = end.splitlines()
        for i in range(len(end)):
            data_spaced += ' '*sz + end[i] + '\n'
        return data_spaced
    
    def process(self, bolts:list) -> str:
        comm = dict(BOLTS_NO="", 
                    BOLTS_MODELE="",
                    BOLTS_PROP="" , 
                    BOLTS_RBE="",
                    BOLTS_PRE="",
                    BOLTS_ELNO="",
                    BOLTS_RELEVE="",)
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
                preload = bolt.preload
                
                grp_no_start = bolt.get_start_name()+"S"
                grp_no_end = bolt.get_end_name()+"S"

                # group size
                if str(radius) not in grp_bolt_size:
                    grp_bolt_size[str(radius)] = [ma_bolt]
                else:
                    grp_bolt_size[str(radius)].append(ma_bolt)

                
                comm["BOLTS_NO"] += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             start_name, 
                                                             start_height, 
                                                             start_radius, 
                                                             grp_no_start)

                comm["BOLTS_NO"] += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             end_name, 
                                                             end_height, 
                                                             end_radius, 
                                                             grp_no_end)
                
                comm["BOLTS_PRE"] += MakeComm.str_pre_espi(ma_bolt, radius, preload, 2.1e5)

                comm["BOLTS_RBE"] += MakeComm.str_rbe3(grp_no_start, start_name)

                comm["BOLTS_RBE"] += MakeComm.str_rbe3(grp_no_end, end_name)

                comm["BOLTS_RELEVE"] += MakeComm.str_post_releve_t(ma_bolt)

                
        comm["BOLTS_MODELE"] += MakeComm.str_affe_model(grp_bolt_name)
        comm["BOLTS_ELNO"] += MakeComm.str_bolts_elno(grp_bolt_name)

        for k,v in grp_bolt_size.items():
            comm["BOLTS_PROP"]+= MakeComm.str_affe_cara(v, float(k))

        # add begining and end string
        comm["BOLTS_NO"] = self.write_concept(self.start_no, self.end_no, comm["BOLTS_NO"])
        comm["BOLTS_MODELE"] = self.write_concept(self.start_model, self.end_model, comm["BOLTS_MODELE"])
        comm["BOLTS_PROP"] = self.write_concept(self.start_prop, self.end_prop, comm["BOLTS_PROP"])
        comm["BOLTS_RBE"] = self.write_concept(self.start_rbe, self.end_rbe, comm["BOLTS_RBE"])
        comm["BOLTS_PRE"] = self.write_concept(self.start_pre, self.end_pre, comm["BOLTS_PRE"])
        comm["BOLTS_ELNO"] = self.write_concept(self.start_elno, self.end_elno, comm["BOLTS_ELNO"])
        comm["BOLTS_RELEVE"] = self.write_concept(self.start_releve, self.end_releve, comm["BOLTS_RELEVE"])
        
        return comm
    
    def to_str(self, comm:dict) -> str:
        str_comm = ""
        for key, value in comm.items():
            str_comm += f"# {key}====================================================\n"
            str_comm += f"{value}\n\n"
            
        return str_comm
    