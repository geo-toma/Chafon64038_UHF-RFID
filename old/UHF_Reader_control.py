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
            txt = metadt.tag_counter.get().split('/')
            nb = int(txt[0]) + 1
            metadt.tag_counter.update(value=str(nb) + '/' + txt[1])
        else :
            metadt.t_handler.update([[nb_tag, str(datetime.now())[:19], "Erreur", tag[:lght]]], 'red')
        metadt.tble.update(values=metadt.t_handler.get_rows(), row_colors = metadt.t_handler.get_colors())
        metadt.tble.widget.yview_moveto(1)

def manage_rfid_system(start_check, metadt, sel):
    global sock
    if start_check == None : 
        events = sel.select(timeout=3)
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
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(77, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(5,5)))]]
    layout = [[sg.Button('Démarrer', size=(15,2), key='start', font=['Cascadia Mono SemiBold', 16], pad=((0,0), (130,0)), disabled = start_btn_state), 
                sg.Button(btn_txt, key=btn_key, size=(10,2), font=['Cascadia Mono SemiBold', 16], pad=((40,0), (130,0)))]]
    info = [[sg.Text(info_txt,font=['Times New Roman', 16], text_color='red', pad=((0,0), (30,0)))]]
    layout += info
    params_btn = [[sg.Button(image_source=cwd() + PATH_SEP + 'params.png', border_width=2, pad=((900,0),(200,0)), key='__params__', disabled = start_btn_state)]]
    sg.theme('dark blue 13')
    window = sg.Window('Colis checking', title_layout + layout + params_btn, size=(1024,600), element_justification='center', 
                use_custom_titlebar=True, no_titlebar=True, finalize = True)
    return window

def app_window():
    global start_win
    start_win = False
    tb_state = TableState()
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(77, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(5,5)))]]
    control_layout = [[sg.Button('Check', size=(10,2), key='check_btn', font=['Cascadia Mono SemiBold', 16], pad=((0,0), (5,15)))], 
                        [sg.Button('Stop', size=(10,2), key='stop_btn', font=['Cascadia Mono SemiBold', 16], pad=((0,0), (0,15)))],
                        [sg.Button('Imprimer', size=(10,2), key='print_btn', font=['Cascadia Mono SemiBold', 16], pad=((0,0), (0,15)))], 
                        [sg.Exit(size=(10,1), font=['Cascadia Mono SemiBold', 16], pad=((0,0), (200,0)))]]
    detected_tag_layout = [[sg.Table(values = [], headings=["N°", "date", "Status", "Detected Tag"], 
                            col_widths=[5, 16, 10, 35], num_rows=22, row_height=21, auto_size_columns=False, 
                            justification='center', font=["Times New Roman", 12], background_color='RoyalBlue4', 
                            key='tag_table', metadata=tb_state)]]
    list_box_layout = [[sg.Combo([], default_value = 'Patienter...', size=(18, 1), pad=((30,0),(0,0)), font=["Times New Roman", 16], 
                            background_color='SteelBlue', key='boxes', readonly=True), 
                        sg.Button('Recharger', font=['Times New Roman', 14], size=(14,1), pad=((10,0),(0,0)), key = 'refresh_btn'),
                        sg.Text(text='', pad=((30,0),(0,0)), key='tag_number', font=["Lucida Fax", 16], text_color='red')]]
    readerIP_layout = [[sg.Text('IP Lecteur', font=["Times New Roman", 14], size=(9, 1), pad = ((30,0),(0,0))), 
                        sg.Input(default_text=Reader.IP_addr, font=["Times New Roman", 14], size=(15, 1), key='reader_ip', pad=((15,0), (0,0)), disabled = True),
                        sg.Button('Rechercher', font=["Times New Roman", 14], pad=((15,0), (0,0)), size=(10,1), key = 'find_btn')]]
    bar = [[sg.Column(list_box_layout, size=(580, 35),pad = ((0,0),(15,0))), 
            sg.Column(readerIP_layout, size=(430, 35),pad = ((0,0),(15,0)))]]
    layout = title_layout + bar + [[sg.Column(detected_tag_layout, size=(830, 490),pad = ((0,0),(15,0))), 
                                    sg.Column(control_layout, size=(180, 490),pad = ((5,0),(15,0)))]]
    window = sg.Window('Colis checking', layout, size=(1024,600), element_justification='center', 
                        use_custom_titlebar=True, no_titlebar=True, finalize = True)
    # window.maximize()
    return window

def select_printer_windows():
    global printer_name
    cmd = "lpstat -p | awk '{ print $2 }'"
    x = popen(cmd,'r')
    printer_names = ['Selectionner l\'imprimante',]
    for _, element in enumerate(x):
        printer_names.append(element.rstrip('\n')) 
    
    # print('printer test')
    # printer_names = ['test', 'printer']

    sg.theme('dark blue 1')

    layout = [[sg.Combo( printer_names, size=(41, 1), pad=((30,0),(20,0)), font=["Times New Roman", 16], 
                        background_color='SteelBlue', key='printer'), 
                        sg.Button('Done', font=['Times New Roman', 14], size=(10,1), pad=((10,0),(20,0)), key = 'select_btn')]]
    frame = [[sg.Frame('Selectionner l\'imprimante', layout, size=(700, 100), font=['Cascadia Mono SemiBold', 14], title_color='red'),]]

    wd = sg.Window('', frame, size=(700, 120), element_justification='center',no_titlebar=True, finalize=True)
    # wd.maximize()
    return wd

def params_windows():
    bdd_ip_layout = [[sg.Text('Database IP : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(30,0))), 
                    sg.Input(default_text='192.168.1.65', font=["Times New Roman", 14], size=(50, 1), key='bdd_ip', pad=((0,0), (30,0)), background_color='white')]]
    bdd_port_layout = [[sg.Text('Database Port : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(10,0))), 
                    sg.Input(default_text='2399', font=["Times New Roman", 14], size=(50, 1), key='bdd_port', pad=((0,0), (10,0)), background_color='white')]]
    bdd_name_layout = [[sg.Text('Database name : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(10,0))), 
                    sg.Input(default_text='bdd_CDK_dossierDivers.fmp12', font=["Times New Roman", 14], size=(50, 1), key='bdd_name', pad=((0,0), (10,0)), background_color='white')]]
    bdd_user_layout = [[sg.Text('Database user name : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(10,0))), 
                    sg.Input(default_text='admin', font=["Times New Roman", 14], size=(50, 1), key='bdd_user', pad=((0,0), (10,0)), background_color='white')]]
    bdd_pwd_layout = [[sg.Text('Database paswword : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(10,0))), 
                    sg.Input(default_text='', font=["Times New Roman", 14], size=(50, 1), key='bdd_pwd', pad=((0,0), (10,0)), background_color='white')]]
    id_colis_len_layout = [[sg.Text('Colis ID len : ', font=["Times New Roman", 14], size=(20, 1), pad = ((30,0),(10,0))), 
                    sg.Input(default_text='6', font=["Times New Roman", 14], size=(50, 1), key='id_colis_len', pad=((0,0), (10,0)), background_color='white')]]
    submit = [[sg.Button('Save', key='submit_btn', font=['Times New Roman', 14], size=(14,1), pad=((350,0),(40,0))),
               sg.Button('Cancel', key='PARAM_CANCEL', font=['Times New Roman',14], size=(14,1), pad=((15,0),(40,0)))]]
    layout = bdd_ip_layout+bdd_port_layout+bdd_name_layout+bdd_user_layout+bdd_pwd_layout+id_colis_len_layout+submit
    frame = [[sg.Frame('Parameters', layout=layout, font=['Cascadia Mono SemiBold', 14], size=(750,350), title_color='red')]]
    wd = sg.Window('', frame, size=(750, 370), element_justification='center',no_titlebar=True, finalize=True)
    return wd
    
def app_screen(java_installaion = False):
    global start_win, nb_tag, printer_name, print_window, thread_s_event
    start_check = False
    table = print_window = table_h = params_wd = None
    reader_ip = ''
    sel = DefaultSelector()
    window = start_window(java_installaion)
    wp = wparams = None
    while True:
        event, values = window.read(timeout=1000)
        print_window = print_process(print_window, wp, table)
        params_wd = params_process(params_wd, wparams)
        if event in (sg.WIN_CLOSED, 'Exit') and start_win == False:
            window.close()
            window = start_window(False)
        if start_win :
            if event in ('start',):
                # window.close()
                # window = app_window()
                window = lunch_window(window, app_window)
            if event in ('close',) :
                #print('ending app')
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
            if event in ('check_btn',):
                nb_tag = 0
                reader_ip, start_check, table, table_h = start_check_click(window)
            elif event in ('stop_btn',): 
                ###  Reset all data  ###
                reader_ip, start_check, table, table_h = stop_click(table)
            elif event in ('print_btn',) and table: 
                print_window = True
                wp = lunch_window(wp, select_printer_windows)
        except Exception as ex:
            #print(ex)
            # print('Print or Cheching Error')
            reader_ip, start_check, table, table_h = stop_click(table)
        call_back_functions(window, event, values, start_check)
        metadt = SimpleNamespace(ip = reader_ip,tble = table,t_handler = table_h,box = values.get('boxes') or 'None',tag_counter = window['tag_number'])
        start_check = manage_rfid_system(start_check, metadt, sel)
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
        thread_s_event = find_click(Request.crc16(ANSWER_MODE_CMD))
        app_screen()
