from jaydebeapi import connect as JDBC_connexion
from os.path import sep as PATH_SEP
from os import getcwd as cwd
from sizes import *
from math import floor

class Configs : 
    param = {'bdd_ip':'192.168.1.65', 
             'bdd_port':'2399', 
             'bdd_name':'bdd_CDK_dossierDivers.fmp12', 
             'bdd_user':'admin', 'bdd_pwd':'x26E8Vtt6U', 
             'id_colis_len' : 4,
             'ftp_IP' : '192.168.1.222',
             'ftp_user' : 'FTP-User',
             'ftp_pwd' : 'Opensnz*teCH23',
             'exit_pwd' : 'admin',
             'check_time' : 90}

def connexion():
    cnn = JDBC_connexion('com.filemaker.jdbc.Driver',
                    'jdbc:filemaker://'+ Configs.param['bdd_ip'] +':'+ Configs.param['bdd_port'] +'/'+ Configs.param['bdd_name'],
                    {'user':Configs.param['bdd_user'], 'password':Configs.param['bdd_pwd']},
                    cwd() + PATH_SEP + 'fmjdbc.jar')
    return cnn

def retreive_from_DB(query, params = None, UM = None):
    liste = []
    cnx = None
    try :
        cnx = connexion()
    except Exception as ex:
        # print(ex)
#         print("can't connect to BDD")
        return []

    cursor = cnx.cursor()
    if params : 
        cursor.execute(query, params)
    else :
        cursor.execute(query)
    resp = cursor.fetchall()
    if UM == None :
        for (elt,) in resp :
            liste.append(elt)
    else :
        for (idcolis,) in resp :
            if not idcolis :
                continue
            dat = str(floor(idcolis))
            liste.append(dat)
    cnx.close()
    return liste

