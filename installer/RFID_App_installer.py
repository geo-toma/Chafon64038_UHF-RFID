# type: ignore
from os import getlogin, remove
from os.path import join, abspath
from subprocess import call

def resource_path(relative_path) :
    base_path = ''
    try : 
        base_path = sys._MEIPASS
    except :
        base_path = abspath('.')
    return join(base_path, relative_path)

autostart_code = '[Desktop Entry]\nType=Application\nName=UHF_Reader_App\nExec=/home/{username}/snap/UHF_Reader_control/UHF_Reader_control\nStartupNotify=false\nHidden=false\n'

path = resource_path('UHF_Reader_control.tar.gz')
with open('UHF_Reader_control.desktop', 'w') as f :
    f.write(autostart_code.format(username = getlogin()))
autostart_path = abspath('UHF_Reader_control.desktop')
install_dir = '/home/' + getlogin() + '/snap/'
call('mkdir -p ' + install_dir, shell= True)
call('tar -zxvf ' + path + ' --directory ' + install_dir, shell=True)
autostart_config_path = ' /home/' + getlogin() + '/.config/autostart/'
call('mkdir -p ' + autostart_config_path, shell= True)
call('cp ' + autostart_path + autostart_config_path, shell=True)
call('sudo chmod +x ' + install_dir + 'UHF_Reader_control/UHF_Reader_control', shell=True)
remove(autostart_path)
call('reboot', shell=True)
