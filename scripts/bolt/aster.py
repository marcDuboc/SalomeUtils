from bolt.shape import VirtualBolt
from bolt.properties import Point, Vector

class MakeComm:

    @staticmethod
    def _listNameToStrTuple(names:list) -> str:
        str_names =chr(40)
        if type(names) is str:
            str_names += "'{}',".format(names)

        elif type(names) is list:
            for n in names:
                str_names += "'{}',".format(n)
        str_names += chr(41)
        return str_names
    
    @staticmethod
    def str_defi_group_tunnel(ma_bolt:str, no_master:str, contact_height:float, contact_radius:float, name_grp_no:str) -> str:
        dft = f"_F(GROUP_MA_AXE={MakeComm._listNameToStrTuple(ma_bolt)},\n\
                \tGROUP_NO_ORIG={MakeComm._listNameToStrTuple(no_master)},\n\
                \tLONGUEUR={MakeComm._listNameToStrTuple(contact_height)},\
                \n\tNOM={MakeComm._listNameToStrTuple(name_grp_no)},\n\
                \tOPTION='TUNNEL',\n\
                \tRAYON={MakeComm._listNameToStrTuple(contact_radius)},\n\
                \tTOUT='OUI'),\n"
        return dft
    
    @staticmethod
    def str_affe_model(ma_bolts):
        afm = f"_F(GROUP_MA={ma_bolts},\n\
                \tMODELISATION='POU_D_T',\n\
                \tPHENOMENE='MECANIQUE'),\n"
        return afm
    
    @staticmethod
    def str_affe_cara(ma_bolt:str, bolt_radius:float):
        afc = f"_F(CARA=('R', ),\n\
                \tGROUP_MA={MakeComm._listNameToStrTuple(ma_bolt)},\n\
                \tSECTION='CERCLE',\n\
                \tVALE={MakeComm._listNameToStrTuple(bolt_radius)},\n\
                \tVARI_SECT='CONSTANT'),\n"
        return afc

    @staticmethod
    def str_rbe3(no_slave, no_master):
        rbe = f"_F(COEF_ESCL=(1.0,),\n\
                \tDDL_ESCL=('DX-DY-DZ',),\n\
                \tDDL_MAIT=('DX','DY','DZ','DRX','DRY','DRZ'),\n\
                \tGROUP_NO_ESCL={MakeComm._listNameToStrTuple(no_slave)},\n\
                \tGROUP_NO_MAIT={MakeComm._listNameToStrTuple(no_master)}),\n"
        return rbe
    
    def process(self, bolts:list) -> str:
        defi_group = ""
        affe_model = ""
        affe_cara = ""
        rbe3 = ""

        for bolt in bolts:
            if type(bolt) is VirtualBolt:
                # group name
                ma_bolt = bolt.get_bolt_name()
                start_name = bolt.get_start_name()
                end_name = bolt.get_end_name()

                # variable
                radius = bolt.radius
                start_radius = bolt.start_radius
                start_height = bolt.start_height
                end_radius = bolt.end_radius
                end_height = bolt.end_height,
                
                grp_no_start = bolt.get_start_name()+"S"
                grp_no_end = bolt.get_end_name()+"S"

                
                defi_group += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             start_name, 
                                                             start_height, 
                                                             start_radius, 
                                                             grp_no_start)
                defi_group += MakeComm.str_defi_group_tunnel(ma_bolt, 
                                                             end_name, 
                                                             end_height, 
                                                             end_radius, 
                                                             grp_no_end)
                affe_model += MakeComm.str_affe_model(ma_bolt)  
                affe_cara += MakeComm.str_affe_cara(ma_bolt, 
                                                    radius)
                rbe3 += MakeComm.str_rbe3(grp_no_start, 
                                          start_name)
                rbe3 += MakeComm.str_rbe3(grp_no_end, 
                                          end_name)

        return dict(CREA_GROUP_NO=defi_group, AFFE_MODELE=affe_model, POUTRE=affe_cara, LIAISON_RBE3=rbe3)
    


