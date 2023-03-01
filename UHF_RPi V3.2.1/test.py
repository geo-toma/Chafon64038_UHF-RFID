import PySimpleGUI as sg
# 
# val = []
# 
# for _ in range(30):
#     val.append('test')
# for _ in range(30):
#     val.append('OTHER')
#     
# layout = [[sg.Listbox(val, size=(10,20), font=('Time New Roman', 16), sbar_width=30, key='ls')], [sg.Button('Quit', key='quit')]]
# 
# w = sg.Window('',layout, size = (1024,600), no_titlebar=True)
# 
# while True:
#     e,v = w.read(timeout=500)
#     print(v)
#     if e in ('quit',None):
#         break
# 
# w.close()

# class Monitor(object):
#     pass
        
# monitor_size = Monitor()
# setattr(monitor_size, 'width', 1600)
# setattr(monitor_size, 'height', 1200)
# print(monitor_size.width)


# def check_window():
#     w1 = w2 = None
#     sg.theme('dark blue 13')
#     frame = [[sg.Frame('', layout = [[sg.Text('Verification Terminée avec SUCCES', key='End_Check_Messsage', font=('Time New Roman', 20), pad=((20,20),(10,20)))],
#                                      [sg.Button('OK', key='Message_Acknowledgement', font=('Time New Roman', 20), button_color='green', size=(10,3))
#                             ]], element_justification='center')]]
#     w1 = sg.Window('', frame, no_titlebar=True, element_justification='center', finalize=True, keep_on_top=True)
#     layout = [[sg.Text('    Vérification ECHOUE    ', key='End_Check_Messsage', font=('Time New Roman', 20), pad=((0,0),(10,20)), background_color='red')],
#               [sg.Table(values=[], headings=['Id Colis', 'Status'], col_widths=[20,8], row_height=35, auto_size_columns=False,
#                             justification='center', key='Error_Tab', font=('Time New Roman', 20), pad=((20,20),(10,20)), num_rows=10)],
#               [sg.Button('Restart Check', key='_CHECK_', font=('Time New Roman', 20), size=(15,2))]]
#     frame0 = [[sg.Frame('', layout, element_justification='center', font=('Time New Roman', 20))]]
#     w2 = sg.Window('', frame0, no_titlebar=True, element_justification='center', finalize=True, keep_on_top=True)
#     return w1,w2

# def exec_win(w, check_state):
#     win = None
#     if check_state :
#         w[1].close()
#         win = w[0]
#     else :
#         w[0].close()
#         win = w[1]
#     while True :
#         e,v = win.read()
#         if e in ('Message_Acknowledgement','_CHECK_'):
#             break
#     win.close()

# exec_win(check_window(), False)
# lst = ['orange' for _ in range(5)]
# print(lst)

# missed = ['a','b']
# over = ['c']
# rws = []
# colors = []
# [(colors.append((count,'orange')),rws.append([missed[count],'Introuvable'])) for count in range(len(missed))]
# [(colors.append((count+len(missed),'red')),rws.append([over[count],'Surplus'])) for count in range(len(over))]
# print(rws)
# print(colors)

# from socket import gethostname, gethostbyname
# hostname = gethostname()
# ip_address = gethostbyname(hostname)

# print(hostname)



from jaydebeapi import connect as JDBC_connexion
cnn = JDBC_connexion('com.filemaker.jdbc.Driver',
                    'jdbc:filemaker://192.168.1.184:2399/bdd_CDK_dossierDivers.fmp12',
                    {'user':'admin', 'password':'x26E8Vtt6U'},
                    'fmjdbc.jar')
cursor = cnn.cursor()
l = ['z72']
# query="SELECT coli.idColis from Destinataire as dest \
#     LEFT JOIN BonCommandeSortie as comm on dest.idDestinataire = comm.fk_Destinataire \
#     LEFT JOIN UniteManutentionSortie as ums on comm.idBonCommandeSortie = ums.fk_BonCommandeSortie \
#     LEFT JOIN Colis as coli on coli.fk_UniteManutentionSortie = ums.idUniteManutentionSortie \
#     WHERE dest.codeUM='{UM}' AND ums.dateFermeture is NULL AND ums.dateExpedition IS NULL AND \
#     ums.dateOuverture IS NOT NULL".format(UM = l)
query = 'WITH cte AS (SELECT test_duplicate.dupl, ROW_NUMBER() OVER (PARTITION BY test_duplicate.dupl ORDER BY test_duplicate.dupl) row_num FROM test_duplicate) DELETE FROM cte WHERE row_num > 1'
# query="SELECT DISNTINCT.dest.codeUM from Destinataire as dest"
cursor.execute(query)
resp = cursor.fetchall()
print(resp)
cnn.close()