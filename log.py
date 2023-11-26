import time
import storage

logfile = None
try:
    storage.remount("/", False)
    logfile = open("/static/debug.log", "a")
except Exception:
    pass

def log(*x):
    l = time.localtime()
    time_str = "%4d-%02d-%02d %02d:%02d:%02d " % (l[0], l[1], l[2], l[3], l[4], l[5])
    line =  time_str + ' '.join(map(str, x))
    if logfile:
        logfile.write(f"{line}\n")
        logfile.flush()
    else:
        print(line)
