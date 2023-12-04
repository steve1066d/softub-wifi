import time
import storage
import os

logfile = None
lines = 0

try:
    storage.remount("/", False)
    os.rename("/static/debug.log", "/static/debug.bak")
    logfile = open("/static/debug.log", "a")
except Exception:
    pass

def log(*x):
    global lines, logfile
    l = time.localtime()
    time_str = "%4d-%02d-%02d %02d:%02d:%02d " % (l[0], l[1], l[2], l[3], l[4], l[5])
    line =  time_str + ' '.join(map(str, x))
    if logfile:
        logfile.write(f"{line}\n")
        lines += 1
        if lines > 5000:
            logfile.close()
            os.rename("/static/debug.log", "/static/debug.bak")
            logfile = open("/static/debug.log", "a")
        logfile.flush()
    else:
        print(line)
