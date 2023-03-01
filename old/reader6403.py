from conn import *
from bdd import *


ANSWER_MODE_INV_CMD1 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, params_['id_colis_len'], 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x14]
ANSWER_MODE_INV_CMD2 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, params_['id_colis_len'], 0x00, 0x00, 0x00, 0x00, 0x00, 0x81, 0x14]
ANSWER_MODE_INV_CMD3 = [0x11, 0x00, 0x19, 0x07, 0x00, 0x01, 0x00, 0x02, params_['id_colis_len'], 0x00, 0x00, 0x00, 0x00, 0x00, 0x82, 0x14]
ANSWER_MODE_CMD = [0x05, 0x00, 0x76, 0x00]

class Request :
    request = [ANSWER_MODE_INV_CMD1, ANSWER_MODE_INV_CMD2, ANSWER_MODE_INV_CMD3]
    counter = 0

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
        req = Request.crc16(Request.request[Request.counter])
        Request.update_counter()
        return bytearray(req)

class Tag : 
    def __init__(self, tags):
        self.compared_tag_list = tags
        self.len = len(tags)
    
    def check (self, tag) : 
        if len(self.compared_tag_list) != 0 :
            l = len(self.compared_tag_list[0])
            if tag[:l] in self.compared_tag_list :
                self.compared_tag_list.remove(tag[:l])
                return (True, l)
            lenght = 0
            for c in tag :
                if ord(c) in range(33, 126) :
                    lenght += 1
            return (False, lenght)
        return (False, 0)

def get_tags(data):
    tag_list = []
    while(len(data) > 12) : 
        # Check the reader response status
        if(data[3] == 0x01 or data[3] == 0xf8) :
            break

        packet_param = data[6] & 0x80

        if(packet_param == 0x80 and data[8] != 0x00) :
            pck_len = int(data[7])
            tag = data[8 : 8 + pck_len - 1]
            try : 
                tag = data[8 : 8 + pck_len - 1].decode('utf-8')
                end = tag.find('#')
                # print(tag)
                # if tag[0] == 'C' :
                #     tag_list.append(tag.strip())
                if (end > 0):
                    tag_list.append(tag[:end])
            except UnicodeDecodeError : 
                #print('error decoding tag')
                pass

        section_len = int(data[0] + 1)
        data = data[section_len:]
    return tag_list

def event_procced(key, mask, metadt, sel, target):
    sck = key.fileobj
    data = key.data
    if mask & EVENT_READ:
        tags_data = sck.recv(BUFFER_SIZE)
        if(metadt == None):
            return
        resp = get_tags(tags_data)
        if not data.has_box_data and resp: 
            data.has_box_data = True
            # data.tags = Tag(retreive_from_DB(query="SELECT idColis,idUniteManutentionSortie FROM Colis_UniteManutentionSortie_Destinataire WHERE codeUM = '{UM}'".format(UM = metadt.box), params=None, UM=metadt.box))
            data.tags = Tag(retreive_from_DB(query="SELECT coli.idColis from Destinataire as dest \
                                                    LEFT JOIN BonCommandeSortie as comm on dest.idDestinataire = comm.fk_Destinataire \
                                                    LEFT JOIN UniteManutentionSortie as ums on comm.idBonCommandeSortie = ums.fk_BonCommandeSortie \
                                                    LEFT JOIN Colis as coli on coli.fk_UniteManutentionSortie = ums.idUniteManutentionSortie \
                                                    WHERE dest.codeUM='{UM}' AND ums.dateFermeture is NULL and ums.dateExpedition IS NULL and ums.dateOuverture IS NOT NULL".format(UM = metadt.box), params=None, UM=metadt.box))
            # print(len(data.tags.compared_tag_list[0]))
            # print(data.tags.compared_tag_list[0])
            # print(metadt.box)
            metadt.tag_counter.update(value = '0/' + str(data.tags.len), text_color = 'red')
        for tag in resp : 
            if tag not in data.tags_detected and len(tag) != 0:
                tag_check, lght = data.tags.check(tag)
                # print(lght)
                data.tags_detected.append(tag)
                target(tag_check, metadt, tag, lght)
                pending = len (data.tags.compared_tag_list)
                detect = len(data.tags_detected)
                if  detect == data.tags.len and pending == 0:
                    metadt.tag_counter.update(text_color='green')
                    sel.unregister(sck)
                    break
        else : 
            data.request = Request.next()
            event = EVENT_WRITE
            sel.modify(sck, events = event, data = data)
    if mask & EVENT_WRITE :
        if data.request :
            sent = sck.send(data.request)
            if sent != len(data.request) : 
                data.request = data.request[sent:]
            else :
                event = EVENT_READ
                sel.modify(sck, events = event, data = data)