import PySimpleGUI as sg
from reader6403 import *

# layout = [[sg.Button('IP Lecteur', font=["Times New Roman", 18], size=(9, 2), pad = ((190,0),(0,0)), key='end'), 
#                     sg.Button(
#                         Reader.IP_addr, font=["Times New Roman", 18], size=(20, 2), key='reader_ip', pad=((15,0), (0,0)), 
#                         disabled_button_color=('black',"white"), border_width=0, button_color='white', disabled = True
#                     ),
#                     sg.Button('Rechercher', font=["Times New Roman", 18], pad=((28,0), (0,0)), size=(14,2), key = 'find_btn')]]

# window = sg.Window('test', layout, element_justification='center', 
#                         use_custom_titlebar=True, no_titlebar=True, finalize = True)

# while True : 
#     e,_ = window.read(timeout=500)
#     if e in ('end',):
#         window.close()
#         break
#     if e in ('find_btn',):
#         find_click(Request.crc16(ANSWER_MODE_CMD))

# print(Reader.IP_addr)

# sock = socket(AF_INET, SOCK_STREAM)
# sock.connect(('192.168.1.101', 27011))

# sel = DefaultSelector()
# sel, sock = create_and_register_sock('192.168.1.93', sel, EVENT_WRITE)

blank = sg.Window('', [[]], size = (1920,1080), use_custom_titlebar=True, no_titlebar=True, finalize=True)
blank.read(timeout=50)
sleep(5)
blank.close()