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

class Reader:
    IP_addr = 'Searching'
    parse_ip = 0

def create_and_register_sock(ip, sel, event, data = None):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex((ip, READER_PORT))
    sel.register(sock, events = event, data = data)
    return (sel, sock)

def find_reader_ip(event, lock, ip4min, ip4max, ip_address, cmd):
    # global reader_IP
    pi_ip4 = ip_address.split('.')[3]
    ip_sum = 0
    for ip4 in range(ip4min, ip4max):
        ip_sum += ip4
        if ip4 == int(pi_ip4) :
            continue
        if(event.is_set()) :
            #print('stoping threads')
            break
        readerUHFip = '.'.join(ip_address.split('.')[:3]) + '.' + str(ip4)
        if ping_reader(readerUHFip, cmd):
            with lock :
                Reader.IP_addr =  readerUHFip
            path = cwd() + PATH_SEP
            with open(path + '.readerIP', 'w') as f :
                f.write(readerUHFip)
            event.set()
            return
    with lock :
        Reader.parse_ip += ip_sum
        # print(Reader.parse_ip)
        if Reader.IP_addr == 'Searching' and Reader.parse_ip == 32384: 
            Reader.IP_addr = 'Pas de Lecteur'

def find_click(ping_reader_cmd):
    Reader.IP_addr = 'Searching'
    Reader.parse_ip = 0
    try:
        path = cwd() + PATH_SEP
        rIP = ''
        with open(path + '.readerIP', 'r') as f :
            rIP = f.readline()
            # print(rIP)
        if ping_reader(rIP, ping_reader_cmd) :
            Reader.IP_addr = rIP
            return
    except:
        pass
    # print('starting search with many thread')
    ip4_min = 2
    ip4_max = 70
    event = Event()
    lock = Lock()
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
    while True:
        th = Thread(target=find_reader_ip, args=(event, lock, ip4_min, ip4_max, ip_address, ping_reader_cmd))
        th.start()
        if ip4_max == 255 or event.is_set():
            break
        ip4_min = ip4_max
        if ip4_max + 70 < 256 :
            ip4_max += 70
        else :
            ip4_max = 255
    return event

def ping_reader(ip_addr, cmd_to_ping):
    sel = DefaultSelector()
    sel, sock = create_and_register_sock(ip_addr, sel, EVENT_WRITE)
    return_value = False
    stop = False
    while True:
        events = sel.select(timeout=1)
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