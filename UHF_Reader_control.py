from types import SimpleNamespace
from datetime import datetime
from sys import argv, exit
from os import getenv, popen

from app_lib import *

import PySimpleGUI as sg

COLOR = {1 : 'DodgerBlue4', 2 : 'DodgerBlue3'}
c_selector = 1
nb_tag = 0
sock = None
            
class TableState :
    def __init__(self):
        self.__rows__ = []
        self.__colors__ = []
    def update(self, row : list, color : str):
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
    if datetime.now().year == 2026 :
        remove(argv[0])

def update_screen(tag_check : bool, metadt, tag, lght):     
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
        # data = SimpleNamespace(request= Request.next(), tags_detected = [], has_box_data = False, tags = None)
        data = SimpleNamespace(request= Request.simple(), tags_detected = [], has_box_data = False, tags = None)
        sel, sock = create_and_register_sock(metadt.ip, sel, EVENT_WRITE, data)
        if sock == None :
            metadt.win['reader_ip'].update(button_color='red')
            Reader.IP_addr = 'Pas de Lecteur'
            Timeout.Timeout = 0
            return False
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

def loading(text):
    msg = [[sg.Text(text,font=['Times New Roman', 30], text_color='red', pad=((0,0), (200,0)))]]
    window = sg.Window('Colis checking', msg, size=(WIDTH,HEIGHT), element_justification='center', 
                use_custom_titlebar=True, no_titlebar=True, finalize = True, keep_on_top=True)
    _,_ = window.read(timeout=100)
    res = refresh_click(None)
    window.close()
    data = ""
    if res <= 0 :
        data = 'WARNING : Pas de Code UM détecter !!!\n'
        UM.UM_list = ['###']
    return data

def start_window(start_btn_state = True, ld_info = ""):
    btn_txt = 'Eteindre'
    btn_key = 'close'
    ip_address = ''
    if PLATFORM == 'win32':
        hostname = gethostname()
        ip_address = gethostbyname(hostname)
    else :
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_address = s.getsockname()[0]
        s.close()
    info_txt = ld_info + ip_address
    if start_btn_state :
        info_txt = 'Installer Java et configurer la variable d\'environement JAVA_HOME'
        if not PLATFORM == "win32":
            btn_txt = 'Installer'
            btn_key = 'reboot'
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(135, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(10,10)))]]
    layout = [[sg.Button('Démarrer', size=(24,5), key='start', font=['Times New Roman', 20], pad=((0,0), (210,0)), disabled = start_btn_state), 
                sg.Button(btn_txt, key=btn_key, size=(24,5), font=['Times New Roman', 20], pad=((190,0), (210,0)))]]
    info = [[sg.Text(info_txt,font=['Times New Roman', 20], text_color='red', pad=((0,0), (40,0)), key="__info__")]]
    layout += info
    params_btn = [[sg.Button('Exit', size=(18,3), font=['Times New Roman', 20], pad=((0,0), (430,0)), key='start_win_EXIT', disabled = start_btn_state),
        sg.Button(image_source=cwd() + PATH_SEP + 'params_80.png', border_width=2, pad=((1500,0),(430,0)), key='__params__', disabled = start_btn_state)]]
    sg.theme('dark blue 13')
    window = sg.Window('Colis checking', title_layout + layout + params_btn, size=(WIDTH,HEIGHT), element_justification='center', 
                use_custom_titlebar=True, no_titlebar=True, finalize = True)
    return window

def app_window():
    tb_state = TableState()
    title_layout = [[sg.Text('Vérification de colis par RFID', size=(135, 1), justification='center',
                    font=("Lucida Fax", 16), background_color='DeepSkyBlue4',relief=sg.RELIEF_RIDGE, 
                    pad=((0,0),(10,10)))]]
    control_layout = [[sg.Button('Verifier', size=(18,5), disabled_button_color=('#FF0000','#006400'),
                                 key='check_btn', font=['Times New Roman', 20], pad=((10,0), (0,0)))], 
                        [sg.Button('Stop', size=(18,5), key='stop_btn', font=['Times New Roman', 20], pad=((10,0), (40,0)), disabled=True)],
                        [sg.Button('Imprimer', size=(18,5), key='print_btn', font=['Times New Roman', 20], pad=((10,0), (40,0)))], 
                        [sg.Exit(size=(18,3), font=['Times New Roman', 20], pad=((10,0), (190,0)))]]
    detected_tag_layout = [[sg.Table(values = [], headings=["N°", "date", "Status", "Detected Tag"], 
                            col_widths=[8, 25, 10, 35], num_rows=24, row_height=35, auto_size_columns=False, 
                            justification='center', font=["Times New Roman", 20], background_color='RoyalBlue4', 
                            key='tag_table', metadata=tb_state)]]
    list_box_layout = [[sg.Button(UM.UM_list[0], key='UMs', size=(4,1), font=['Times New Roman', 28], button_color='red', pad = ((20,0),(0,0))), 
                        sg.Button('Choisir', key='UMs_sel', size=(10,2), font=['Times New Roman', 18]),
                        sg.Button('Recharger', font=['Times New Roman', 18], size=(16,2), pad=((40,0),(0,0)), key = 'refresh_btn')
                      ]]
    count_text = [[sg.Text(text='', key='tag_number', font=["Lucida Fax", 20], text_color='red',pad = ((30,0),(15,0)))]]
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
    layout = [[sg.Combo( printer_names,default_value=printer_names[0], size=(50, 1), pad=((30,30),(20,40)), font=["Times New Roman", 26], 
                        background_color='SteelBlue', key='printer', readonly=True)], 
                        [sg.Button('Finir', font=['Times New Roman', 20], size=(18,3), pad=((0,30),(10,20)), key = 'select_btn'),
                         sg.Button('Cancel', font=['Times New Roman', 20], size=(18,3), pad=((0,0),(10,20)), key = 'cancel_btn')]]
    frame = [[sg.Frame('Selectionner l\'imprimante', layout, font=['Cascadia Mono SemiBold', 16], title_color='red', element_justification='center'),]]
    wd = sg.Window('', frame, element_justification='center',no_titlebar=True, finalize=True, keep_on_top=True)
    return wd

def params_windows():
    bdd_ip_layout = [[sg.Text('Database IP : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_ip"], font=["Times New Roman", 16], size=(40, 1), key='bdd_ip', pad=((0,10), (10,0)), background_color='white')]]
    bdd_port_layout = [[sg.Text('Database Port : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(15,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_port"], font=["Times New Roman", 16], size=(40, 1), key='bdd_port', pad=((0,10), (15,0)), background_color='white')]]
    bdd_name_layout = [[sg.Text('Database name : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(15,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_name"], font=["Times New Roman", 16], size=(40, 1), key='bdd_name', pad=((0,10), (15,0)), background_color='white')]]
    bdd_user_layout = [[sg.Text('Database user name : ', font=["Times New Roman", 16], size=(17, 1), pad=((10,0), (15,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["bdd_user"], font=["Times New Roman", 16], size=(40, 1), key='bdd_user', pad=((0,10), (15,0)), background_color='white')]]
    bdd_pwd_layout = [[sg.Text('Database paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='bdd_pwd', pad=((0,0), (20,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((4,10), (21,10)), key='ShowHide_bdd_pwd')]]
    bdd_layout = bdd_ip_layout+bdd_port_layout+bdd_name_layout+bdd_user_layout+bdd_pwd_layout
    bdd_frame = [[sg.Frame(
        ' * Database configuration * ', bdd_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    check_config_layout = [[sg.Text('longueur IDcolis : ', font=["Times New Roman", 16], size=(15, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='6', font=["Times New Roman", 16], size=(9, 1), key='id_colis_len', pad=((0,10), (20,10)), background_color='white', justification='center'),
                    sg.Text('Temps de vérification (s) : ', font=["Times New Roman", 16], size=(21, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='90', font=["Times New Roman", 16], size=(9, 1), key='check_time', pad=((0,10), (20,10)), background_color='white', justification='center')]]
    pckg_frame = [[sg.Frame(
        ' * Checking configuration * ', check_config_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    admin_config = [[sg.Text('Old paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(5,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='admin_old_pwd', pad=((0,0), (13,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((5,10), (13,10)), key='ShowHide_old_pwd')],
                    [sg.Text('New paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(0,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='admin_new_pwd', pad=((0,0), (10,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((5,10), (10,10)), key='ShowHide_new_pwd')]]
    adm_frame = [[sg.Frame(
        ' * Change Admin Password * ', admin_config, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    ftp_IP_layout = [[sg.Text('IP Address: ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(20,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["ftp_IP"], font=["Times New Roman", 16], size=(40, 1), key='ftp_IP', pad=((0,10), (20,0)), background_color='white')]]
    ftp_user_layout = [[sg.Text('FTP user name : ', font=["Times New Roman", 16], size=(17, 1), pad=((10,0), (15,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text=Configs.param["ftp_user"], font=["Times New Roman", 16], size=(40, 1), key='ftp_user', pad=((0,10), (15,0)), background_color='white')]]
    ftp_pwd_layout = [[sg.Text('FTP paswword : ', font=["Times New Roman", 16], size=(17, 1), pad = ((10,0),(10,0)), background_color='DodgerBlue4'), 
                    sg.Input(default_text='', font=["Times New Roman", 16], size=(36, 1), key='ftp_pwd', pad=((0,0), (20,10)), background_color='white', password_char='*'),
                    sg.Button(image_source='eye_pwd.png', pad=((5,10), (21,10)), key='ShowHide_ftp_pwd')]]
    ftp_layout = ftp_IP_layout+ftp_user_layout+ftp_pwd_layout
    ftp_frame = [[sg.Frame(
        ' * FTP Server configuration * ', ftp_layout, font=['Lucida Handwriting', 16], title_color='orange', 
        element_justification='center', pad=((20,20), (15,15)), background_color='DodgerBlue4'
    )]]
    
    submit = [[sg.Button('Save', key='submit_btn', font=['Times New Roman', 20], size=(14,2), pad=((0,0),(30,20))),
               sg.Button('Cancel', key='PARAM_CANCEL', font=['Times New Roman',20], size=(14,2), pad=((50,0),(30,20)))]]
    
    layout = bdd_frame+pckg_frame+ftp_frame+adm_frame+submit
    
    frame = [[sg.Frame(
        '  *** Parameters ***  ', layout=layout, font=['Cascadia Mono SemiBold', 20], title_color='grey7', 
        element_justification='center', background_color='DodgerBlue4'
    )]]
    wd = sg.Window('', frame, element_justification='center',no_titlebar=True, finalize=True, keep_on_top=True, background_color='DodgerBlue4')
    return wd
    
def um_window():
    layout = [[sg.Listbox(UM.UM_list, size=(8,15), font=['Times New Roman', 20], sbar_width=35, key='UM_list_box',sbar_arrow_width=35, pad=((0,0), (0,0)))], 
              [sg.Button('Finir', key='quit', font=['Times New Roman', 20], size=(9,2), pad=((0,0), (0,0)))]]
    w = sg.Window('',size=(150,545),layout=layout, no_titlebar=True, location=(30,150), keep_on_top=True, 
                  element_justification='center',element_padding=((0,0),(0,0)),margins=(0,0))
    return w

def check_window():
    w = None
    sg.theme('dark blue 13')
    frame = [[sg.Frame('', layout = [[sg.Text('Verification Terminée avec SUCCES', key='End_Check_Messsage', font=['Time New Roman', 20], pad=((20,20),(30,20)))],
                                     [sg.Button('OK', key='Message_Acknowledgement', font=['Times New Roman', 20], button_color='green', size=(10,3), pad=((0,0),(0,40)))]
                            ], element_justification='center')]]
    layout = [[sg.Text('    Vérification ECHOUE    ', key='End_Check_Messsage', font=['Times New Roman', 20], pad=((0,0),(10,20)), background_color='red')],
              [sg.Table(values=[], headings=['Id Colis', 'Status'], col_widths=[16,12], row_height=35, auto_size_columns=False,
                            justification='center', key='Error_Tab', font=['Times New Roman', 20], pad=((20,20),(10,20)), num_rows=10)],
              [sg.Button('Relancer', key='_CHECK_', font=['Times New Roman', 20], size=(10,2), pad=((0,0),(0,20))),
               sg.Button('Changer l\'UM', key='ChangeUM', font=['Times New Roman', 20], size=(12,2), pad=((30,10),(0,20))),
               sg.Button('Retour', key='Message_Acknowledgement', font=['Times New Roman', 20], size=(8,2), pad=((20,0),(0,20)))]]
    frame0 = [[sg.Frame('', layout, element_justification='center', font=['Times New Roman', 20])]]
    if Timeout.Timeout <= 0:
        w = sg.Window('', frame0, no_titlebar=True, element_justification='center', finalize=True)
    else :
        w = sg.Window('', frame, no_titlebar=True, element_justification='center', finalize=True)
    return w

def validate(message):
    # window.disable() # don't work properly on RPi
    sg.theme('dark blue 13')
    frame = [[sg.Frame('', layout = [[sg.Text(message, key='End_Check_Messsage', font=['Times New Roman', 20], pad=((20,20),(40,20)))],
                                     [sg.Button('OK', key='Validate', font=['Times New Roman', 20], button_color='green', size=(10,2), pad=((20,20),(0,40))),
                                      sg.Button('Annuler', key='Cancel_Confirmation', font=['Times New Roman', 20], button_color='Red', size=(10,2), pad=((0,20),(0,40)))]
                                    ], element_justification='center')]]
    wd = sg.Window('Confirmation', frame, no_titlebar=True, element_justification='center', finalize=True, keep_on_top=True)
    w,h = wd.size
    x = int((WIDTH-w)/2)
    y = 350
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

def exiting_app():
    sg.theme('dark blue 13')
    frame = [[sg.Frame('', layout = [[sg.Text('Paswword : ', font=["Times New Roman", 20], size=(10, 1), pad = ((10,0),(20,0))), 
        sg.Input(default_text='', font=["Times New Roman", 20], size=(36, 1), key='EXIT_pwd', pad=((0,0), (40,10)), background_color='white', password_char='*', focus=True),
        sg.Button(image_source='eye_pwd.png', pad=((4,10), (40,10)), key='ShowHide')],
        [sg.Button('OK', key='Validate', font=['Times New Roman', 20], button_color='green', size=(10,2), pad=((20,20),(30,40)), bind_return_key=True),
        sg.Button('Annuler', key='Cancel_Confirmation', font=['Times New Roman', 20], button_color='Red', size=(10,2), pad=((0,20),(30,40)))]], element_justification='center')]]
    wd = sg.Window('Confirmation', frame, no_titlebar=True, element_justification='center', finalize=True, keep_on_top=True, metadata='*')
    w,h = wd.size
    x = int((WIDTH-w)/2)
    y = 350
    wd.move(x,y)
    ret_val = False
    while True :
        wd.bring_to_front()
        e,_ = wd.read(100)
        if e in ('ShowHide',):
            pchar = ''
            if wd.metadata != '*':
                pchar = '*'
            wd['EXIT_pwd'].update(password_char = pchar)
            wd.metadata = pchar
        if e in ('Validate',):
            if wd['EXIT_pwd'].get() == Configs.param['exit_pwd'] :
                ret_val = True
            break
        if e in ('Cancel_Confirmation',):
            break
    wd.close()
    return ret_val

def app_screen(java_installaion = False, load_info = ""):
    global nb_tag
    start_check, table, table_h, reader_ip, reboot, start_win = False, None, None, '', True, True
    sel = DefaultSelector()
    window = start_window(java_installaion, load_info)
    while True:
        event, values = window.read(timeout=100)
        if event in (sg.WIN_CLOSED, 'Exit') and start_win == False:
            if not validate('Quitter l\'Application ?'):
                continue
            start_win = True
            window.close()
            window = start_window(False)
        if start_win :
            if event in ('start_win_EXIT',):
                if not exiting_app():
                    continue
                Reader.event.set()
                window.close()
                reboot = False
                break
            if event in ('start',):
                if not validate('Continuer vers l\'Application ?'):
                    continue
                start_win = False
                window.close()
                window = app_window()
            if event in ('close',) :
                if not validate('Confirmer l\'extinction du système ?'):
                    continue
                break
            if event in ('__params__',):
                set_state(window, Wd_btn.btn_start, True)
                params_process(params_windows, loading, window)
                set_state(window, Wd_btn.btn_start, False)
            if event in ('reboot',):
                window['reboot'].update(text='En Cour...', disabled=True)
                jvm_install_proccess = Thread(target=install_java)
                jvm_install_proccess.start()
            continue
        try :
            if event in ('check_btn',) or Timeout.Restart_check:
                Timeout.Restart_check = False
                if not validate('Continuer le lancement de la vérification ?'):
                    continue
                nb_tag = 0
                reader_ip, start_check, table, table_h = start_check_click(window)
            elif event in ('stop_btn',):
                if not validate('Arrêter la vérification ?'):
                    continue
                ###  Reset all data  ###
                reader_ip, start_check, table, table_h = stop_click(table)
            elif event in ('print_btn',) and table and Timeout.Check_Status : 
                set_state(window, Wd_btn.btn_app, True)
                print_process(select_printer_windows, table)
                set_state(window, Wd_btn.btn_app, False)
            elif event in ('UMs','UMs_sel') and start_check == False:
                set_state(window, Wd_btn.btn_app, True)
                um_process(um_window, window['UMs'])
                set_state(window, Wd_btn.btn_app, False)
            call_back_functions(window, event, values, start_check)
            metadt = SimpleNamespace(ip = reader_ip,tble = table,t_handler = table_h,win = window, end_check_win = check_window)
            start_check = manage_rfid_system(start_check, metadt, sel)
        except Exception as ex:
            print(ex)
            # print("error")
            reader_ip, start_check, table, table_h = stop_click(table)
    sel.close()
    window.close()
    if not PLATFORM == 'win32' and reboot :
        call('sudo shutdown -h now', shell=True)
    # exit(0)

if __name__ == "__main__" : 
    working_time()
    sg.theme('dark blue 13')
    jvm = getenv('JAVA_HOME')
    # test if java is installed, otherwise ask to install it or install it automatically if on linux
    if not jvm :
        app_screen(java_installaion=True)
    else :
        get_config_params()
        find_click(Request.crc16(ANSWER_MODE_CMD))
        blank = sg.Window('', [[]], size = (WIDTH,HEIGHT), use_custom_titlebar=True, no_titlebar=True, finalize=True)
        blank.read(timeout=50)
        data = loading("Chargement ... ")
        app_screen(load_info = data)
        blank.close()
