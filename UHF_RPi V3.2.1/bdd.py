from jaydebeapi import connect as JDBC_connexion
from os.path import sep as PATH_SEP
from os import getcwd as cwd
from sizes import *

class Configs : 
    param = {'bdd_ip':'192.168.1.65', 
             'bdd_port':'2399', 
             'bdd_name':'bdd_CDK_dossierDivers.fmp12', 
             'bdd_user':'admin', 'bdd_pwd':'x26E8Vtt6U', 
             'id_colis_len' : 0x04,
             'ftp_IP' : '192.168.1.222',
             'ftp_user' : 'FTP-User',
             'ftp_pwd' : 'Opensnz*teCH23'}
# x26E8Vtt6U

def connexion():
    
    # path = cwd() + PATH_SEP
    cnn = JDBC_connexion('com.filemaker.jdbc.Driver',
                    'jdbc:filemaker://'+ Configs.param['bdd_ip'] +':'+ Configs.param['bdd_port'] +'/'+ Configs.param['bdd_name'],
                    {'user':Configs.param['bdd_user'], 'password':Configs.param['bdd_pwd']},
                    cwd() + PATH_SEP + 'fmjdbc.jar')
                    # 'UHF_RPi/fmjdbc.jar')
    # cnn = jdbc.connect('com.mysql.cj.jdbc.Driver',
    #                 'jdbc:filemaker://192.168.1.95:2399/bdd_CDK_test.fmp12',
    #                 {'user':'admin', 'password':'x26E8Vtt6U'},
    #                 # 'jdbc:mysql://192.168.1.222',
    #                 # {'user':'main_user', 'password':'Opensnz*teCH23'},
    #                 'UHF_RPi\\mysql-connector-java-8.0.30.jar')
    return cnn

def retreive_from_DB(query, params = None, UM = None):
    liste = []
    cnx = None
    try :
        cnx = connexion()
    except Exception as ex:
        # print(ex)
        #print("can't connect to BDD")
        return None

    cursor = cnx.cursor()
    # cursor.execute('USE rfid_data')
    if params : 
        cursor.execute(query, params)#(id,))
    else :
        cursor.execute(query)
    resp = cursor.fetchall()
    if UM == None :
        for (elt,) in resp :
            liste.append(elt)
    else :
        # for (idcolis, umid) in resp :
        for (idcolis,) in resp :
            # dat = "C_b_UM"+str(umid)+"_"+str(UM)+"_c_"+str(idcolis)
            if not idcolis :
                continue
            dat = str(floor(idcolis)) #+ '_' + str(UM)
            liste.append(dat)
    cnx.close()
    return liste

