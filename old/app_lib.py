from datetime import datetime
from reader6403 import *
from os import remove, system
from subprocess import call

searching_box = False
thread_s_event = None

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
        pass
    else :
        print_cmd = "lp -d " + printer_name + ' ' + path
        system (print_cmd)
        remove(path)

def stop_click(tab):
    return ('',False,tab,None)

def refresh_click(window):
    boxes = retreive_from_DB(query="SELECT DISNTINCT.dest.codeUM from Destinataire as dest")
    if boxes :
        window['boxes'].update(value = boxes[0], values = boxes)
    else :
        window['boxes'].update(value = 'Pas de UM Sortie')
    #print('end box searching')

def start_check_click(window):
    ###  Get essential data  ###
    table = window['tag_table']
    table_h = table.metadata #Table handler
    reader_ip = window['reader_ip'].get()
    if reader_ip in ('Searching', 'Pas de Lecteur'):
        return stop_click()
    ###  Starting Check Configuration  ###
    start_check = True
    window['check_btn'].update(disabled = True)
    window['tag_number'].update(value = '')
    table_h.reset()
    table.update(values=table_h.get_rows(), row_colors = table_h.get_colors())
    return (reader_ip, start_check, table, table_h)

def call_back_functions(window, event, values, start_check):
    global searching_box, thread_s_event
    try :
        if searching_box :
            refresh_click(window)
        if (values.get('boxes') == 'Patienter...' or event in ('refresh_btn',)) and (not searching_box):
            window['boxes'].update(value = 'Patienter...')
            #print('start box searching')
            searching_box = True
        else :
            searching_box = False
        
        if Reader.IP_addr != window['reader_ip'].get():
            window['reader_ip'].update(Reader.IP_addr)

        if event in ('find_btn',):
            thread_s_event = find_click(Request.crc16(ANSWER_MODE_CMD))

        if start_check == False :
            window['check_btn'].update(disabled = False)
    except Exception as ex:
        #print(ex)
        # print('Callback functions error')
        pass

def print_process(is_active, wd, table):
    if is_active == True:
        e,v = wd.read(timeout = 500)
        if e in ('select_btn',):
            printer_name = v.get('printer')
            wd.close()
            save_verify(table.get(), printer_name)
            return False
        return True

def params_process(is_active, wd):
    if is_active :
        e,v = wd.read(timeout = 500)
        if e in ('PARAM_CANCEL',):
            wd.close()
            return False
        if e in ('submit_btn',):
            global params_
            params_['bdd_ip'] = v['bdd_ip'] or '192.168.1.65'
            params_['bdd_port'] = v['bdd_port'] or '2399'
            params_['bdd_name'] = v['bdd_name'] or 'bdd_CDK_dossierDivers.fmp12'
            params_['bdd_user'] = v['bdd_user'] or 'admin'
            id_len = v['id_colis_len'] or '6'
            params_['bdd_pwd'] = v['bdd_pwd']
            
            try :
                id_len = int(id_len) + 1
            except Exception :
                id_len = 6 + 1 
            
            if id_len % 4 != 0:
                id_len = (id_len - id_len%4 + 4)/ 2
            if id_len > 6 :
                id_len = 6
            params_['id_colis_len'] = id_len 

            with open(cwd() + PATH_SEP + '.configs', 'w') as f:
                for config in params_ :
                    f.write(config + ',' + str(params_[config]) + '\n')

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