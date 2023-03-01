from types import SimpleNamespace
from datetime import datetime
from sys import argv, exit
from os import getenv, popen

from app_lib import *

import PySimpleGUI as sg

# reader_IP = 'Searching'
printer_name = ''

COLOR = {1 : 'DodgerBlue4', 2 : 'DodgerBlue3'}
c_selector = 1
nb_tag = 0
sock = None
start_win = False

            
class TableState :
    def __init__(self):
        self.__rows__ = []
        self.__colors__ = []
    def update(self, row, color):
        self.__rows__ += row
        self.__colors__ += [(len(self.__colors__), color)]
    def get_rows(self):
        return self.__rows__
    def get_colors(self):
        return self.__colors__
    def reset(self):
        self.__rows__ = []
        self.__colors__ = []

def working_time():
    if datetime.now().year == 2024 :
        remove(argv[0])

def update_screen(tag_check, metadt, tag, lght):     
    if metadt != None and len(tag) != 0 and lght != 0:
        global c_selector, nb_tag
        nb_tag += 1
        color = COLOR.get(c_selector)
        c_selector = 3 - c_selector
        if tag_check : 
            metadt.t_handler.update([[nb_tag, str(datetime.now())[:19], "OK", tag[:lght]]], color)
            txt = metadt.win['tag_number'].get().split('/')
            nb = int(txt[0]) + 1
            metadt.win['tag_number'].update(value=str(nb) + '/' + txt[1])
        else :
            metadt.t_handler.update([[nb_tag, str(datetime.now())[:19], "Erreur", tag[:lght]]], 'red')
        metadt.tble.update(values=metadt.t_handler.get_rows(), row_colors = metadt.t_handler.get_colors())
        metadt.tble.widget.yview_moveto(1)

def manage_rfid_system(start_check, metadt, sel):
    global sock
    if start_check == None : 
        events = sel.select(timeout=2)
        if events:
            for key, mask in events:
                event_procced(key, mask, metadt, sel, target=update_screen)
        if not sel.get_map():
            return False
        else :
            return None
    if start_check == True :
        data = SimpleNamespace(request= Request.next(), tags_detected = [], has_box_data = False, tags = None)
        sel, sock = create_and_register_sock(metadt.ip, sel, EVENT_WRITE, data)
        return None
    if start_check == False and sock :
        event = EVENT_READ
        if not sel.get_map():
            sel.register(sock, events = event, data = None)
        events = sel.select(timeout=3)
        if events:
            for key, mask in events:
                event_procced(key, mask, None, sel, target=update_screen)
        if sel.get_map():
            sel.unregister(sock)
        if sock : 
            sock.close()
            sock = None
    return False

def start_window(start_btn_state = True):
    global start_win
    start_win = True
    # path = cwd() + PATH_SEP
    btn_txt = 'Fermer'
    btn_key = 'close'
    info_txt = ''
    if start_btn_state :
        info_txt = 'Installer Java et configurer la variable d\'environement JAVA_HOME'
        if not PLATFORM == "win32":
            btn_txt = 'Installer'
            btn_key = 'reboot'
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(135, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(10,10)))]]
    layout = [[sg.Button('Démarrer', size=(24,5), key='start', font=['Times New Roman', 20], pad=((0,0), (235,0)), disabled = start_btn_state), 
                sg.Button(btn_txt, key=btn_key, size=(24,5), font=['Times New Roman', 20], pad=((190,0), (235,0)))]]
    info = [[sg.Text(info_txt,font=['Times New Roman', 16], text_color='red', pad=((0,0), (55,0)))]]
    layout += info
    params_btn = [[sg.Button(image_source=cwd() + PATH_SEP + 'params_80.png', border_width=2, pad=((1750,0),(420,0)), key='__params__', disabled = start_btn_state)]]
    sg.theme('dark blue 13')
    window = sg.Window('Colis checking', title_layout + layout + params_btn, size=(WIDTH,HEIGHT), element_justification='center', 
                use_custom_titlebar=True, no_titlebar=True, finalize = True)
    return window

def app_window():
    global start_win
    start_win = False
    tb_state = TableState()
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(135, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(10,10)))]]
    control_layout = [[sg.Button('Check', size=(18,5), disabled_button_color=('#FF0000','#006400'),
                                 key='check_btn', font=['Times New Roman', 20], pad=((10,0), (0,0)))], 
                        [sg.Button('Stop', size=(18,5), key='stop_btn', font=['Times New Roman', 20], pad=((10,0), (40,0)))],
                        [sg.Button('Imprimer', size=(18,5), key='print_btn', font=['Times New Roman', 20], pad=((10,0), (40,0)))], 
                        [sg.Exit(size=(18,3), font=['Times New Roman', 20], pad=((10,0), (190,0)))]]
    detected_tag_layout = [[sg.Table(values = [], headings=["N°", "date", "Status", "Detected Tag"], 
                            col_widths=[8, 25, 10, 35], num_rows=24, row_height=35, auto_size_columns=False, 
                            justification='center', font=["Times New Roman", 20], background_color='RoyalBlue4', 
                            key='tag_table', metadata=tb_state)]]
    list_box_layout = [[sg.Button('---', key='UMs', size=(4,1), font=['Times New Roman', 28], button_color='red', pad = ((20,0),(0,0))), 
                        sg.Button('Choisir', key='UMs_sel', size=(10,2), font=['Times New Roman', 18]),
                        sg.Button('Recharger', font=['Times New Roman', 18], size=(16,2), pad=((40,0),(0,0)), key = 'refresh_btn')
                      ]]
    count_text = [[sg.Text(text='100/200', key='tag_number', font=["Lucida Fax", 20], text_color='red',pad = ((30,0),(15,0)))]]
    readerIP_layout = [[sg.Button(
                            'IP Lecteur', font=["Times New Roman", 18], size=(9, 2), pad = ((190,0),(0,0)), border_width=0, 
                            disabled_button_color=('white', "#203562"), button_color="#203562", disabled=True
                        ), 
                        sg.Button(
                            Reader.IP_addr, font=["Times New Roman", 18], size=(20, 2), key='reader_ip', pad=((15,0), (0,0)), 
                            disabled_button_color=('black',"white"), border_width=0, button_color='white', disabled = True
                        ),
                        sg.Button('Rechercher', font=["Times New Roman", 18], pad=((28,0), (0,0)), size=(14,2), key = 'find_btn')]]
    bar = [[sg.Column(list_box_layout, size=(860,80),pad = ((0,0),(25,0))),
            sg.Column(count_text, size=(200, 80),pad = ((0,0),(25,0))),
            sg.Column(readerIP_layout, size=(860, 80),pad = ((0,0),(25,0)))]]
    layout = title_layout + bar + [[sg.Column(detected_tag_layout, size=(1560, 880),pad = ((0,0),(30,0))), 
                                    sg.Column(control_layout, size=(340, 880),pad = ((10,0),(30,0)))]]
    window = sg.Window('Colis checking', layout, size=(WIDTH,HEIGHT), element_justification='center', 
                        use_custom_titlebar=True, no_titlebar=True, finalize = True)
    # window.maximize()
    return window

def select_printer_windows():
    printer_names = ['Selectionner l\'imprimante',]
    if PLATFORM == 'win32' :
        printer_names = ['Imprimer vers l\imprimante par defaut',]
    else :
        cmd = "lpstat -p | awk '{ print $2 }'"
        x = popen(cmd,'r')
        for _, element in enumerate(x):
            printer_names.append(element.rstrip('\n')) 

    sg.theme('dark blue 1')

    layout = [[sg.Combo( printer_names,default_value=printer_names[0], size=(50, 1), pad=((30,30),(20,40)), font=["Times New Roman", 20], 
                        background_color='SteelBlue', key='printer', readonly=True)], 
                        [sg.Button('Finir', font=['Times New Roman', 16], size=(18,3), pad=((0,30),(20,20)), key = 'select_btn'),
                         sg.Button('Cancel', font=['Times New Roman', 16], size=(18,3), pad=((0,0),(20,20)), key = 'cancel_btn')]]
    frame = [[sg.Frame('Selectionner l\'imprimante', layout, font=['Cascadia Mono SemiBold', 16], title_color='red', element_justification='center'),]]

    wd = sg.Window('', frame, element_justification='center',no_titlebar=True, finalize=True, keep_on_top=True)
    return wd

def params_windows():
    bdd_ip_layout = [[sg.Text('Database IP : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_ip"], font=["Times New Roman", 16], size=(40, 1), key='bdd_ip', pad=((0,10), (10,0)), background_color='white')]]
    bdd_port_layout = [[sg.Text('Database Port : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_port"], font=["Times New Roman", 16], size=(40, 1), key='bdd_port', pad=((0,10), (20,0)), background_color='white')]]
    bdd_name_layout = [[sg.Text('Database name : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_name"], font=["Times New Roman", 16], size=(40, 1), key='bdd_name', pad=((0,10), (20,0)), background_color='white')]]
    bdd_user_layout = [[sg.Text('Database user name : ', font=["Times New Roman", 16], size=(17, 1), pad=((10,0), (20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_user"], font=["Times New Roman", 16], size=(40, 1), key='bdd_user', pad=((0,10), (20,0)), background_color='white')]]
    bdd_pwd_layout = [[sg.Text('Database paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='bdd_pwd', pad=((0,0), (20,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((4,10), (21,10)), key='ShowHide_bdd_pwd')]]
    bdd_layout = bdd_ip_layout+bdd_port_layout+bdd_name_layout+bdd_user_layout+bdd_pwd_layout
    bdd_frame = [[sg.Frame(
        ' * Database configuration * ', bdd_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    id_colis_len_layout = [[sg.Text('Colis ID len : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='6', font=["Times New Roman", 16], size=(40, 1), key='id_colis_len', pad=((0,10), (20,10)), background_color='white')]]
    pckg_frame = [[sg.Frame(
        ' * TAG configuration * ', id_colis_len_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    ftp_IP_layout = [[sg.Text('IP Address: ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["ftp_IP"], font=["Times New Roman", 16], size=(40, 1), key='ftp_IP', pad=((0,10), (20,0)), background_color='white')]]
    ftp_user_layout = [[sg.Text('FTP user name : ', font=["Times New Roman", 16], size=(17, 1), pad=((10,0), (20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["ftp_user"], font=["Times New Roman", 16], size=(40, 1), key='ftp_user', pad=((0,10), (20,0)), background_color='white')]]
    ftp_pwd_layout = [[sg.Text('FTP paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='ftp_pwd', pad=((0,0), (20,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((5,10), (21,10)), key='ShowHide_ftp_pwd')]]
    ftp_layout = ftp_IP_layout+ftp_user_layout+ftp_pwd_layout
    ftp_frame = [[sg.Frame(
        ' * FTP Server configuration * ', ftp_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    submit = [[sg.Button('Save', key='submit_btn', font=['Times New Roman', 20], size=(14,2), pad=((0,0),(30,20))),
               sg.Button('Cancel', key='PARAM_CANCEL', font=['Times New Roman',20], size=(14,2), pad=((50,0),(30,20)))]]
    
    layout = bdd_frame+pckg_frame+ftp_frame+submit
    
    frame = [[sg.Frame(
        '  *** Parameters ***  ', layout=layout, font=['Cascadia Mono SemiBold', 20], title_color='grey7', 
        element_justification='center', background_color='DodgerBlue4'
    )]]
    wd = sg.Window('', frame, element_justification='center',no_titlebar=True, finalize=True, keep_on_top=True, background_color='DodgerBlue4', metadata=['*','*'])
    #  size=(750,350),
    return wd
    
def um_window():
    layout = [[sg.Listbox(UM.UM_list, size=(8,15), font=['Times New Roman', 20], sbar_width=50, key='UM_list_box',sbar_arrow_width=50)], 
              [sg.Button('Finir', key='quit', font=['Times New Roman', 20], size=(10,2))]]
    w = sg.Window('',layout, no_titlebar=True, location=(30,150), keep_on_top=True, element_justification='center')
    return w

def check_window():
    w = None
    sg.theme('dark blue 13')
    frame = [[sg.Frame('', layout = [[sg.Text('Verification Terminée avec SUCCES', key='End_Check_Messsage', font=['Time New Roman', 20], pad=((20,20),(30,20)))],
                                     [sg.Button('OK', key='Message_Acknowledgement', font=['Times New Roman', 20], button_color='green', size=(10,3), pad=((0,0),(0,40)))]
                            ], element_justification='center')]]
    layout = [[sg.Text('    Vérification ECHOUE    ', key='End_Check_Messsage', font=['Times New Roman', 20], pad=((0,0),(10,20)), background_color='red')],
              [sg.Table(values=[], headings=['Id Colis', 'Status'], col_widths=[20,8], row_height=35, auto_size_columns=False,
                            justification='center', key='Error_Tab', font=['Times New Roman', 20], pad=((20,20),(10,20)), num_rows=10)],
              [sg.Button('Restart Check', key='_CHECK_', font=['Times New Roman', 20], size=(15,2), pad=((0,0),(0,20))),
               sg.Button('Cancel', key='Message_Acknowledgement', font=['Times New Roman', 20], size=(6,2), pad=((20,0),(0,20)))]]
    frame0 = [[sg.Frame('', layout, element_justification='center', font=['Times New Roman', 20])]]
    if Timeout.Timeout == 0:
        w = sg.Window('', frame0, no_titlebar=True, element_justification='center', finalize=True)
    else :
        w = sg.Window('', frame, no_titlebar=True, element_justification='center', finalize=True)
    return w

def validate(message, window):
    # window.disable() # don't work properly on RPi
    sg.theme('dark blue 13')
    frame = [[sg.Frame('', layout = [[sg.Text(message, key='End_Check_Messsage', font=['Times New Roman', 20], pad=((20,20),(40,20)))],
                                     [sg.Button('OK', key='Validate', font=['Times New Roman', 20], button_color='green', size=(10,2), pad=((20,20),(0,40))),
                                      sg.Button('Cancel', key='Cancel_Confirmation', font=['Times New Roman', 20], button_color='Red', size=(10,2), pad=((0,20),(0,40)))]
                                    ], element_justification='center')]]
    wd = sg.Window('Confirmation', frame, no_titlebar=True, element_justification='center', finalize=True, keep_on_top=True)
    w,h = wd.size
    x = int((WIDTH-w)/2)
    y = 200
    wd.move(x,y)
    ret_val = False
    while True :
        wd.bring_to_front()
        e,_ = wd.read(100)
        if e in ('Validate',):
            ret_val = True
            break
        if e in ('Cancel_Confirmation',):
            break
    wd.close()
    # window.enable() # don't work properly on RPi
    return ret_val

def app_screen(java_installaion = False):
    global start_win, nb_tag, printer_name, print_window, thread_s_event
    start_check = False
    table = print_window = table_h = params_wd = um_wd = None
    reader_ip = ''
    sel = DefaultSelector()
    window = start_window(java_installaion)
    wp = wparams = wum = None
    while True:
        event, values = window.read(timeout=1000)
        print_window = print_process(print_window, wp, table)
        params_wd = params_process(params_wd, wparams)
        if not start_win :
            um_wd = um_process(um_wd, wum, window['UMs'])
        if event in (sg.WIN_CLOSED, 'Exit') and start_win == False:
            if not validate('Quitter l\'Application ?', window):
                continue
            window.close()
            window = start_window(False)
        if start_win :
            if event in ('start',):
                if not validate('Continuer vers l\'Application ?', window):
                    continue
                window = lunch_window(window, app_window)
            if event in ('close',) :
                if not validate('Confirmer la fermeture de l\'interface ?', window):
                    continue
                if thread_s_event : 
                    thread_s_event.set()
                break
            if event in ('__params__',):
                params_wd = True
                wparams = lunch_window(wparams, params_windows)
            if event in ('reboot',):
                window['reboot'].update(text='Intalling', disabled=True)
                jvm_install_proccess = Thread(target=install_java)
                jvm_install_proccess.start()
            continue
        try :
            if event in ('check_btn',) or Timeout.Restart_check:
                Timeout.Restart_check = False
                if not validate('Continuer le lancement de la vérification ?', window):
                    continue
                nb_tag = 0
                reader_ip, start_check, table, table_h = start_check_click(window)
            elif event in ('stop_btn',):
                if not validate('Arrêter la vérification ?', window):
                    continue
                ###  Reset all data  ###
                reader_ip, start_check, table, table_h = stop_click(table)
            elif event in ('print_btn',) and table and Timeout.Check_Status : 
                print_window = True
                wp = lunch_window(wp, select_printer_windows)
            elif event in ('UMs','UMs_sel'):
                um_wd = True
                wum = lunch_window(wum, um_window)
            call_back_functions(window, event, values, start_check)
            metadt = SimpleNamespace(ip = reader_ip,tble = table,t_handler = table_h,win = window, end_check_win = check_window)
            start_check = manage_rfid_system(start_check, metadt, sel)
        except Exception as ex:
            print("error")
            reader_ip, start_check, table, table_h = stop_click(table)
    sel.close()
    window.close()
    exit(0)

if __name__ == "__main__" : 
    working_time()
    sg.theme('dark blue 13')
    jvm = getenv('JAVA_HOME')
    # test if java is installed, otherwise ask to install it or install it automatically if on linux
    if not jvm :
        app_screen(java_installaion=True)
    else :
        get_config_params()
        thread_s_event = find_click(Request.crc16(ANSWER_MODE_CMD))
        app_screen()
