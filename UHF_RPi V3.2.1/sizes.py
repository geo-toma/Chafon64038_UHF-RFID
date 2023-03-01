from screeninfo import get_monitors
from math import floor

class Monitor(object):
    pass
        
monitor_size = Monitor()
try :
    monitor_size = get_monitors()[0]
except :
    setattr(monitor_size, 'width', 1920)
    setattr(monitor_size, 'height', 1080)


def crop(w,h):
    if w/h < 16/9:
        h_r = floor(w*9/16)
        return w,h_r
    else :
        w_r = floor(h*16/9)
        return w_r,h

WIDTH, HEIGHT = crop(monitor_size.width, monitor_size.height)

