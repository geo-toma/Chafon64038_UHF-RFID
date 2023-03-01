from conn import *
from bdd import *
from time import sleep

class Alternate_Color:
    def __init__(self, color1 : str, color2 : str):
        self._color1 = color1
        self._color2 = color2
        self._cursor = 1
    def set_colors(self, color1 : str, color2 : str):
        self._color1 = color1
        self._color2 = color2
    def get_color(self):
        self._cursor = 1 - self._cursor
        if self._cursor == 0:
            return self._color1
        else :
            return self._color2

class Timeout :
    Timeout = 0
    Restart_check = False
    Check_Status = False # Inform if the checking process is succeed or fail
    lock = Lock()

class Checking_Time(Thread):
    def __init__(self, timeout : int):
        super().__init__(target= Checking_Time.slp)
        with Timeout.lock :
            Timeout.Timeout = timeout
    def slp():
        while (Timeout.Check_Status == False and Timeout.Timeout > 0):
            sleep(1)
            with Timeout.lock :
                Timeout.Timeout -= 1
    def exec_win(win, check_state, window_, rows = None):
        if not check_state :
            win['Error_Tab'].update(values = rows['rows'], row_colors = rows['colors'])
        c_um = False
        while True :
            win.bring_to_front()
            e,_ = win.read(100)
            if e in ('Message_Acknowledgement',):
                break
            if e in ('_CHECK_',):
                Timeout.Restart_check = True
                break
            if e in ('ChangeUM',):
                c_um = True
                break
        win.close()
        if c_um :
            window_['UMs_sel'].click()
        
ANSWER_MODE_CMD = [0x05, 0x00, 0x76, 0x00]

checking_time = Checking_Time(20)

class Command : 
    m_ANSWER_MODE_INV_CMD1 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x0A]
    m_ANSWER_MODE_INV_CMD2 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x0A]
    m_ANSWER_MODE_INV_CMD3 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x82, 0x0A]
    def get(who : int):
        cmd = []
        if who == 0 :
            cmd = Command.m_ANSWER_MODE_INV_CMD1
        elif who == 2 :
            cmd = Command.m_ANSWER_MODE_INV_CMD2
        else :
            cmd = Command.m_ANSWER_MODE_INV_CMD3
        cmd[8] = floor(float(Configs.param['id_colis_len']))
        return cmd
    
class Request :
    counter = 0
    def simple():
        return bytearray([0x06, 0x00, 0x01, 0x04, 0xff, 0xd4, 0x39])
    
    def crc16(cmd):
        PRESET_VALUE = 0xFFFF
        POLYNOMIAL = 0x8408
        ui_crc_value = PRESET_VALUE
        for i in range(len(cmd)):
            ui_crc_value ^= cmd[i] 
            for _ in range(8):
                if(ui_crc_value % 2 == 0):
                    ui_crc_value >>= 1
                else :
                    ui_crc_value = (ui_crc_value >> 1)^POLYNOMIAL
        crc2 = int(ui_crc_value/256)
        crc1 = ui_crc_value - 256*crc2
        return cmd + [crc1, crc2]

    def update_counter() :
        Request.counter += 1
        if Request.counter >= 3 :
            Request.counter = 0
    
    def next() :
        req = Request.crc16(Command.get(Request.counter))
        Request.update_counter()
        return bytearray(req)

class Tag : 
    def __init__(self, tags):
        self.compared_tag_list = tags
        self.len = len(tags)
        self.error_tag_list = []
    
    def check (self, tag) : 
        if len(self.compared_tag_list) != 0 :
            l = len(self.compared_tag_list[0])
            if tag[:l] in self.compared_tag_list :
                self.compared_tag_list.remove(tag[:l])
                return (True, l)
            self.error_tag_list.append(tag[:l])
            lenght = 0
            for c in tag :
                if ord(c) in range(33, 126) :
                    lenght += 1
            return (False, lenght)
        return (False, 0)

def get_tags(dt):
    tag_list = []
    # while(len(data) > 12) : 
    #     # Check the reader response status
    #     if(data[3] == 0x01 or data[3] == 0xf8) :
    #         break

    #     packet_param = data[6] & 0x80

    #     if(packet_param == 0x80 and data[8] != 0x00) :
    #         pck_len = int(data[7])
    #         tag = data[8 : 8 + pck_len - 1]
    #         try : 
    #             tag = data[8 : 8 + pck_len - 1].decode('utf-8')
    #             end = tag.find('#')
    #             # print(tag)
    #             # if tag[0] == 'C' :
    #             #     tag_list.append(tag.strip())
    #             if (end > 0):
    #                 tag_list.append(tag[:end])
    #         except UnicodeDecodeError : 
    #             #print('error decoding tag')
    #             pass

    #     section_len = int(data[0] + 1)
    #     data = data[section_len:]
    data = list(dt)
    while len(data) >= 0x11:
        d_len = data[0] + 1
        res = data[:d_len]
        data = data[d_len:]
        epc_len = res[5]
        res = res[6:]
        for _ in range(epc_len):
            b = bytes(res[1:res[0]])
            tag = b.decode("ascii", errors="ignore")
            end = tag.find('#')
            if (end > 0):
                tag_list.append(tag[:end])
            res = res[res[0]:]
    return tag_list

def success_check(metadt,sel,sck,checking_time):
    Timeout.Check_Status = True
    metadt.win['tag_number'].update(text_color='green')
    metadt.win['check_btn'].update(disabled = False, text = 'Check')
    sel.unregister(sck)
    Checking_Time.exec_win(metadt.end_check_win(), True, window_=metadt.win)
    if checking_time.is_alive() :
        checking_time.join()

def failed_check(metadt,sel,sck,checking_time,data):
    sel.unregister(sck)
    if checking_time.is_alive() :
        checking_time.join()
    missed = data.tags.compared_tag_list
    over = data.tags.error_tag_list
    rws = []
    colors = []
    alt_colors = Alternate_Color('OrangeRed3','OrangeRed4')
    [(colors.append((count,alt_colors.get_color())),rws.append([missed[count],'Introuvable'])) for count in range(len(missed))]
    alt_colors = Alternate_Color('red3','red4')
    [(colors.append((count+len(missed),alt_colors.get_color())),rws.append([over[count],'Surplus'])) for count in range(len(over))]
    rows = {'rows': rws, 'colors' : colors}
    Checking_Time.exec_win(metadt.end_check_win(), False, window_=metadt.win, rows=rows)

def event_procced(key, mask, metadt, sel, target):
    global checking_time
    sck = key.fileobj
    data = key.data
    if mask & EVENT_READ:
        tags_data = sck.recv(BUFFER_SIZE)
        if(metadt == None):
            with Timeout.lock :
                Timeout.Timeout = 0
            return
        try : 
            resp = get_tags(tags_data)
        except Exception as _ :
            return
        if not data.has_box_data: 
            data.has_box_data = True
            data.tags = Tag(retreive_from_DB(query="SELECT coli.idColis from Destinataire as dest \
                                                    LEFT JOIN BonCommandeSortie as comm on dest.idDestinataire = comm.fk_Destinataire \
                                                    LEFT JOIN UniteManutentionSortie as ums on comm.idBonCommandeSortie = ums.fk_BonCommandeSortie \
                                                    LEFT JOIN Colis as coli on coli.fk_UniteManutentionSortie = ums.idUniteManutentionSortie \
                                                    WHERE dest.codeUM='{UM}' AND ums.dateFermeture is NULL AND ums.dateExpedition IS NULL AND \
                                                    ums.dateOuverture IS NOT NULL".format(UM = metadt.win['UMs'].get_text() or 'None'), params=None, UM=metadt.win['UMs'].get_text() or 'None'))
            metadt.win['tag_number'].update(value = '0/' + str(data.tags.len), text_color = 'red')
        for tag in resp :
            if data.tags.len <= 0 :
                with Timeout.lock :
                    Timeout.Timeout = 0
            if tag not in data.tags_detected and len(tag) != 0:
                tag_check, lght = data.tags.check(tag)
                data.tags_detected.append(tag)
                target(tag_check, metadt, tag, lght)
                pending = len (data.tags.compared_tag_list)
                detect = len(data.tags_detected)
                if  detect == data.tags.len and pending == 0:
                    success_check(metadt,sel,sck,checking_time)
                    break 
            if Timeout.Timeout <= 0 :
                failed_check(metadt,sel,sck,checking_time,data)
                break
        else : 
            if Timeout.Timeout > 0 :
                # data.request = Request.next()
                data.request = Request.simple()
                event = EVENT_WRITE
                sel.modify(sck, events = event, data = data)
            else :
                failed_check(metadt,sel,sck,checking_time,data)
    if mask & EVENT_WRITE :
        if data.request :
            sent = 0
            try :
                sent = sck.send(data.request)
            except Exception :
                sel.unregister(sck)
                metadt.win['reader_ip'].update(button_color='red',text='Pas de Lecteur')
                Reader.IP_addr = 'Pas de Lecteur'
                Timeout.Timeout = 0
                return
            if sent != len(data.request) : 
                data.request = data.request[sent:]
            else :
                event = EVENT_READ
                sel.modify(sck, events = event, data = data)
                
