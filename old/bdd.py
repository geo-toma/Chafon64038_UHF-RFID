from jaydebeapi import connect as JDBC_connexion
from math import floor
from os.path import sep as PATH_SEP
from os import getcwd as cwd

params_ = {'bdd_ip':'192.168.1.65', 'bdd_port':'2399', 'bdd_name':'bdd_CDK_dossierDivers.fmp12', 'bdd_user':'admin', 'bdd_pwd':'x26E8Vtt6U', 'id_colis_len' : 0x04}
# x26E8Vtt6U

def connexion():
    global params_
    try:
        with open(cwd() + PATH_SEP + '.configs', 'r') as f:
            configs = f.readlines()
            for config in configs :
                key_value = config.split(',')
                params_[key_value[0]] = str(key_value[1]).strip()           
    except:
        #print(cwd() + PATH_SEP)
        pass
    # path = cwd() + PATH_SEP
    cnn = JDBC_connexion('com.filemaker.jdbc.Driver',
                    'jdbc:filemaker://'+ params_['bdd_ip'] +':'+ params_['bdd_port'] +'/'+ params_['bdd_name'],
                    {'user':params_['bdd_user'], 'password':params_['bdd_pwd']},
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

