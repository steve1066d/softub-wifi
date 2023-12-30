import time
import storage
import os
from ticks import calc_due_ticks_sec, is_due


logfile = None
lines = 0
cache = ""
due = calc_due_ticks_sec(60)

try:
    storage.remount("/", False)
    try:
        os.remove("/static/debug.bak")
    except Exception:
        pass
    os.rename("/static/debug.log", "/static/debug.bak")
except Exception:
    pass
try:
    logfile = open("/static/debug.log", "a")
except Exception:
    pass


def _write():
    global cache, lines, logfile, due
    if len(cache):
        logfile.write(cache)
        cache = ""
        logfile.flush()
        if lines > 5000:
            lines = 0
            logfile.close()
            os.rename("/static/debug.log", "/static/debug.bak")
            logfile = open("/static/debug.log", "a")


def log(*x):
    global lines, logfile, cache
    lt = time.localtime()
    time_str = "%4d-%02d-%02d %02d:%02d:%02d " % (
        lt[0],
        lt[1],
        lt[2],
        lt[3],
        lt[4],
        lt[5],
    )
    line = time_str + " ".join(map(str, x))
    if logfile:
        cache += f"{line}\n"
        lines += 1
        if len(cache) > 2048:
            _write()
    else:
        print(line)


def log_flush():
    global due
    if logfile:
        if is_due(due):
            due = calc_due_ticks_sec(60)
            _write()


def log_close():
    global lines
    if logfile:
        lines = 0
        _write()
        logfile.close()
        os.sync()
