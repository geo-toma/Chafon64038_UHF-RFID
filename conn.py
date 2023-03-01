from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, gethostname, gethostbyname
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ
from threading import Event, Lock, Thread
from sys import platform as PLATFORM
from os.path import sep as PATH_SEP
from os import getcwd as cwd, getlogin, chdir

if not PLATFORM == 'win32' :
    chdir('/home/' + getlogin() + '/snap/UHF_Reader_control')


READER_PORT = 27011
BUFFER_SIZE = 2048

class Reader(object):
    IP_addr = 'Searching...'
    event = Event()
    lock = Lock()

def create_and_register_sock(ip, sel, event, data = None):
    sock = socket(AF_INET, SOCK_STREAM)
    # sock.setblocking(False)
    sock.settimeout(0.2)
    res = sock.connect_ex((ip, READER_PORT))
    if res != 0 and data != None :
        return (sel, None)
    sel.register(sock, events = event, data = data)
    return (sel, sock)

def find_reader_ip(reader, ip4min, ip4max, ip_address, cmd):
    pi_ip4 = ip_address.split('.')[3]
    ip_sum = 0
    for ip4 in range(ip4min, ip4max):
        ip_sum += ip4
        if ip4 == int(pi_ip4) :
            continue
        if(Reader.event.is_set()) :
            ip_sum = 0
            break
        readerUHFip = '.'.join(ip_address.split('.')[:3]) + '.' + str(ip4)
        if ping_reader(readerUHFip, cmd):
            with Reader.lock :
                Reader.IP_addr =  readerUHFip
            path = cwd() + PATH_SEP
            with open(path + '.readerIP', 'w') as f :
                f.write(readerUHFip)
            Reader.event.set()
            return
    with Reader.lock :
        reader.parse_ip += ip_sum
        if Reader.IP_addr == 'Searching...' and reader.parse_ip == 32384:
            Reader.IP_addr = 'Pas de Lecteur'

def find_click(ping_reader_cmd):
    Reader.IP_addr = 'Searching...'
    Reader.event.clear()
    try:
        path = cwd() + PATH_SEP
        rIP = ''
        with open(path + '.readerIP', 'r') as f :
            rIP = f.readline()
        if ping_reader(rIP, ping_reader_cmd) :
            Reader.IP_addr = rIP
            Reader.event.set()
            return
    except:
        pass
    # print('starting search with many thread')
    ip4_min = 2
    ip4_max = 100
    ip_address = ''
    try :
        if PLATFORM == 'win32':
            hostname = gethostname()
            ip_address = gethostbyname(hostname)
        else :
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(("8.8.8.8",80))
            ip_address = s.getsockname()[0]
            s.close()
    except :
        Reader.IP_addr = 'Pas de Lecteur'
        return
    reader = Reader()
    setattr(reader, 'parse_ip', 0)
    while True:
        th = Thread(target=find_reader_ip, args=(reader, ip4_min, ip4_max, ip_address, ping_reader_cmd))
        th.start()
        if ip4_max == 255 or Reader.event.is_set():
            break
        ip4_min = ip4_max
        if ip4_max + 100 < 256 :
            ip4_max += 100
        else :
            ip4_max = 255

def ping_reader(ip_addr, cmd_to_ping):
    sel = DefaultSelector()
    sel, sock = create_and_register_sock(ip_addr, sel, EVENT_WRITE)
    return_value = False
    stop = False
    while True:
        events = sel.select(timeout=0.2)
        if events:
            for key, mask in events:
                s = key.fileobj
                if mask & EVENT_READ:
                    try :
                        rcv = s.recv(BUFFER_SIZE)
                        if rcv[3] == 0x00 and rcv[2] == 0x76:
                            return_value = True
                    except :
                        pass
                    stop = True
                if mask & EVENT_WRITE:
                    try :
                        s.send(bytearray(cmd_to_ping))
                        event = EVENT_READ
                        sel.modify(s, events = event)
                    except :
                        stop = True
        else :
            break
        if stop :
            break
    sel.unregister(sock)
    sock.close()
    sel.close()
    return return_value