from datetime import datetime
from reader6403 import *
from os import remove, system
from subprocess import call
from ftplib import FTP

searching_box = False
thread_s_event = None

class UM :
    UM_list = []

class Table :
    LCH  = '┌'
    LCB  = '└'
    RCH  = '┐'
    RCB  = '┘'
    MH   = '┬'
    MM   = '┼'
    MB   = '┴'
    HS   = '─'
    VS   = '│'
    HBSL = '├'
    HBSR = '┤'

    def __init__(self, header):
        self.head = header
        self.tab = self.create_header(header)
        pass

    def insert_in_case(self, value, case_space):
        if len(value) > case_space:
            return '*'*case_space
        s_lght = int((case_space-len(value))/2)
        return ' '*s_lght + value + ' '*(case_space - len(value) - s_lght)

    def list2dict(self, row):
        d = dict()
        for i in range(len(self.head)) :
            d[list(self.head.keys())[i]] = row[i]
        return d
        
    def create_header(self, tab_headeader) :
        high_line    = Table.LCH
        bottom_line  = Table.HBSL
        head = ''
        for header, h_len in tab_headeader.items():
            high_line += Table.HS*(h_len + 4)
            bottom_line += Table.HS*(h_len + 4)
            head += Table.VS + self.insert_in_case(str(header).rstrip(), h_len + 4)
            if header != list(tab_headeader.keys())[-1]:
                high_line += Table.MH
                bottom_line += Table.MM
            else :
                high_line += Table.RCH
                bottom_line += Table.HBSR
        head_str = high_line + '\n' + head + Table.VS + '\n' + bottom_line 
        return head_str + '\n'

    def add_row(self, row_, is_last_row):
        row = self.list2dict(row_)
        bottom_line = righ_conner = sep = middle =''
        if is_last_row :
            bottom_line = Table.LCB
            righ_conner = Table.RCB
            sep = Table.HS
            middle = Table.MB
        # else :
        #     bottom_line = Table.HBSL
        #     righ_conner = Table.HBSR
        #     sep = Table.HS
        #     middle = Table.MM
        str_row = ''
        for col, val in row.items() :
            len = int(self.head[col] + 4)
            str_row += Table.VS + self.insert_in_case(str(val), len)
            if col != list(self.head.keys())[-1]:
                bottom_line += sep*len + middle
            else :
                bottom_line += sep*len + righ_conner
                #print(len)
        str_row += Table.VS
        if bottom_line != '' :
            str_row += '\n' + bottom_line
        self.tab += str_row + '\n'

HEADER = {'N°' : 3, 'Date' : 20, 'Status' : 7, 'Colis' : 20}

def sendByFTP(ftp_path : str, file_path : str, file_name : str) :
    ftp = None
    try :
        ftp = FTP(Configs.param['ftp_IP'],Configs.param['ftp_user'],Configs.param['ftp_pwd'])
    except :
        remove(file_path)
        # print('text'+Configs.param['ftp_IP']+Configs.param['ftp_user']+Configs.param['ftp_pwd'])
        return
    liste = ftp_path.replace('\\','/').split('/')
    for pth in liste:
        try:
            ftp.cwd(pth+'/')
        except:
            ftp.mkd(pth+'/')
            ftp.cwd(pth+'/')
    f = open(file_path, 'rb')
    ftp.storbinary('STOR ' + file_name, f)
    ftp.close()
    f.close()
    remove(file_path)

def save_verify(tab, printer_name):
    path = cwd() + PATH_SEP
    d = str(datetime.now())[:19].replace('-','_').replace(' ','_').replace(':','_')
    path += d + '.txt'
    print_tab = Table(HEADER)
    for line in tab :
        if line != tab[-1] :
            print_tab.add_row(line, False)
        else : 
            print_tab.add_row(line, True)
    with open(path, 'ab') as f :
        f.write(print_tab.tab.encode('utf8'))
    if PLATFORM == "win32":
        from os import startfile
        startfile(path, "print")
    else :
        print_cmd = "lp -d " + printer_name + ' ' + path.replace(' ','\\ ')
        system (print_cmd)
    sendByFTP('/RFID/Checking_Folder', path, d)

def stop_click(tab):
    return ('',False,tab,None)

def refresh_click(window):
    UM.UM_list = retreive_from_DB(query="SELECT DISNTINCT.dest.codeUM from Destinataire as dest")
    if UM.UM_list :
        window['UMs'].update(text = UM.UM_list[0])
    else :
        window['UMs'].update(text = '###')
        UM.UM_list = ['###']
    # boxes = retreive_from_DB(query="SELECT DISNTINCT.dest.codeUM from Destinataire as dest")
    # if boxes :
    #     window['boxes'].update(value = boxes[0], values = boxes)
    # else :
    #     window['boxes'].update(value = 'Pas de UM Sortie')
    #print('end box searching')

def start_check_click(window):
    global checking_time
    checking_time = Checking_Time(20)
    Timeout.Check_Status = False
    ###  Get essential data  ###
    table = window['tag_table']
    table_h = table.metadata #Table handler
    reader_ip = window['reader_ip'].get_text()
    if reader_ip in ('Searching...', 'Pas de Lecteur'):
        return stop_click(table)
    ###  Starting Check Configuration  ###
    start_check = True
    window['check_btn'].update(disabled = True, text = 'En Cour...')
    window['tag_number'].update(value = '')
    table_h.reset()
    table.update(values=table_h.get_rows(), row_colors = table_h.get_colors())
    checking_time.start()
    return (reader_ip, start_check, table, table_h)

def call_back_functions(window, event, values, start_check):
    global searching_box, thread_s_event
    try :
        if searching_box :
            refresh_click(window)

        if (window['UMs'].get_text() == '---' or event in ('refresh_btn',)) and (not searching_box):
            window['UMs'].update(text = '---')
            searching_box = True
        else :
            searching_box = False
            
        if Reader.IP_addr != window['reader_ip'].get_text():
            window['reader_ip'].update(text=Reader.IP_addr)

        if event in ('find_btn',):
            thread_s_event = find_click(Request.crc16(ANSWER_MODE_CMD))

        if start_check == False  and window['check_btn'].get_text() != 'Check' :
            window['check_btn'].update(disabled = False, text = 'Check')
    except Exception as ex:
        #print(ex)
        # print('Callback functions error')
        pass

def print_process(is_active, wd, table):
    if is_active == True:
        wd.bring_to_front()
        e,v = wd.read(timeout = 500)
        if e in ('select_btn',):
            printer_name = v.get('printer')
            wd.close()
            save_verify(table.get(), printer_name)
            return False
        if e in ('cancel_btn',):
            wd.close()
            return False
        return True

def params_process(is_active, wd):
    if is_active :
        wd.bring_to_front()
        e,v = wd.read(timeout = 500)
        if e in ('PARAM_CANCEL',):
            wd.close()
            return False
        if e in ('ShowHide_bdd_pwd'):
            pchar = ''
            if wd.metadata[0] == '*' :
                pchar = ''
            else : 
                pchar = '*'
            wd['bdd_pwd'].update(password_char=pchar)
            wd.metadata[0] = pchar
        if e in ('ShowHide_ftp_pwd'):
            pchar = ''
            if wd.metadata[1] == '*' :
                pchar = ''
            else : 
                pchar = '*'
            wd['ftp_pwd'].update(password_char=pchar)
            wd.metadata[1] = pchar
        if e in ('submit_btn',):
            Configs.param['bdd_ip'] = v['bdd_ip'] or Configs.param['bdd_ip'] or ''
            Configs.param['bdd_port'] = v['bdd_port'] or Configs.param['bdd_port'] or ''
            Configs.param['bdd_name'] = v['bdd_name'] or Configs.param['bdd_name'] or ''
            Configs.param['bdd_user'] = v['bdd_user'] or Configs.param['bdd_user'] or ''
            id_len = v['id_colis_len'] or '6'
            Configs.param['bdd_pwd'] = v['bdd_pwd'] or Configs.param['bdd_pwd'] or ''
            Configs.param['ftp_IP'] = v['ftp_IP'] or Configs.param['ftp_IP'] or ''
            Configs.param['ftp_user'] = v['ftp_user'] or Configs.param['ftp_user'] or ''
            Configs.param['ftp_pwd'] = v['ftp_pwd'] or Configs.param['ftp_pwd'] or ''
            
            try :
                id_len = int(id_len) + 1
            except Exception :
                id_len = 6 + 1 
            
            if id_len % 4 != 0:
                id_len = (id_len - id_len%4 + 4)/ 2
            if id_len > 6 :
                id_len = 6
            Configs.param['id_colis_len'] = id_len 

            with open(cwd() + PATH_SEP + '.configs', 'w') as f:
                for config in Configs.param :
                    f.write(config + ',' + str(Configs.param[config]) + '\n')

            wd.close()
            return False
        return True

def lunch_window(window, lunch_screen):
    if window :
        window.close()
    return lunch_screen()

def install_java():
    # path = cwd() + PATH_SEP
    path = cwd() + PATH_SEP +'java_install.sh'
    call('sudo chmod +x ' + path, shell=True)
    call(path)
    call('reboot', shell=True)
    
def um_process(is_active, wd, um_btn):
    if is_active : 
        e,v = wd.read(timeout=100)
        wd.bring_to_front()
        if e in ('quit',None):
            um = v['UM_list_box']
            if um :
                um_btn.update(text=um[0])
            wd.close()
            return False
        return True

def get_config_params():
    try:
        with open(cwd() + PATH_SEP + '.configs', 'r') as f:
            configs = f.readlines()
            for config in configs :
                key_value = config.split(',')
                Configs.param[key_value[0]] = str(key_value[1]).strip()           
    except:
        #print(cwd() + PATH_SEP)
        pass
