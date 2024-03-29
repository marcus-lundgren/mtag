import ctypes.util
import logging
import os
import re
import subprocess

from . import watcher_helper


class XScreenSaverInfo(ctypes.Structure):
    _fields_ = [('window', ctypes.c_ulong),  # screen saver window
                ('state', ctypes.c_int),  # off,on,disabled
                ('kind', ctypes.c_int),  # blanked,internal,external
                ('since', ctypes.c_ulong),  # milliseconds
                ('idle', ctypes.c_ulong),  # milliseconds
                ('event_mask', ctypes.c_ulong)]  # events


xlib_str = ctypes.util.find_library('X11')
xlib = ctypes.cdll.LoadLibrary(xlib_str)

xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
xlib.XOpenDisplay.restypes = ctypes.c_void_p
dpy = xlib.XOpenDisplay(os.environ["DISPLAY"].encode("utf-8"))

root = xlib.XDefaultRootWindow(dpy)
xss_str = ctypes.util.find_library('Xss')
xss = ctypes.cdll.LoadLibrary(xss_str)
logging.debug("Loaded XSS")
xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
xss_info = xss.XScreenSaverAllocInfo()


def get_idle_time():
    global xss, dpy, xss_info
    xss.XScreenSaverQueryInfo(dpy, root, xss_info)
    idle_seconds = xss_info.contents.idle // 1000
    return idle_seconds


whoiam = subprocess.run(["whoami"], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
session_id = subprocess.run(["loginctl", "show-user", "-pSessions", "--value", whoiam],
                            stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()

logging.debug(f"{whoiam} => {session_id}")


def get_locked_state():
    global session_id
    locked_hint = subprocess.run(["loginctl", "show-session", "-pLockedHint", "--value", session_id],
                                 stdout=subprocess.PIPE).stdout.strip()
    if locked_hint.lower() == b"no":
        logging.debug("Not locked")
        return False
    elif locked_hint.lower() == b"yes":
        logging.debug("Locked")
        return True
    else:
        logging.debug("Unknown lock hint:", locked_hint)
        return False


# Ensure that we get the value on the right. As a double quote might be escaped
# inside of the left hand side, ensure that we match the correct double quote characters.
wm_class_name_pattern = re.compile(r'[^\\]",\s*"\s*(.*)\s*"$')


def watch() -> None:
    logging.info("== STARTED ==")

    active_window_id_information = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                                                  stdout=subprocess.PIPE, universal_newlines=True,
                                                  encoding="UTF-8").stdout
    logging.debug(active_window_id_information)

    active_window_id = active_window_id_information[active_window_id_information.rfind(" ") + 1:].strip()
    logging.debug(active_window_id)
    idle_seconds = get_idle_time()

    locked_state = get_locked_state()

    # If the window handle id is 0, then make a logged entry with default values
    if active_window_id == "0x0":
        logging.info("No active window.")
        watcher_helper.register(window_title=None,
                                application_name=None,
                                application_path=None,
                                idle_period=idle_seconds,
                                locked_state=locked_state)
        return

    active_window_x11_information = subprocess.run(["xprop", "-id", active_window_id,
                                                    "_NET_WM_PID", "WM_CLASS", "WM_NAME", "_NET_WM_NAME"],
                                                   stdout=subprocess.PIPE, universal_newlines=True,
                                                   encoding="UTF-8").stdout.strip()
    logging.debug(active_window_x11_information)

    application_pid = None
    application_name = None
    active_window_title = None
    for line in active_window_x11_information.splitlines():
        if line.startswith("_NET_WM_PID"):
            application_pid = line[line.find("=") + 2:]
            logging.debug(application_pid)
        elif line.startswith("_NET_WM_NAME"):
            active_window_title = line[line.find("=") + 2:].strip('"')
            logging.debug(active_window_title)
        elif line.startswith("WM_NAME"):
            # Do not parse this if we already got a value
            if active_window_title is not None:
                logging.debug("Application window title already set")
                continue
            application_window_title = line[line.find("=") + 2:].strip('"')
            logging.debug(application_window_title)
        elif line.startswith("WM_CLASS"):
            global wm_class_name_pattern
            pattern_matches = wm_class_name_pattern.findall(line)
            if len(pattern_matches) > 0:
                application_name = pattern_matches[0]
            else:
                logging.debug("Unable to extract the right hand side WM_CLASS value.")

    logging.debug(application_pid)

    application_path = None
    if application_pid.isdigit() and application_pid != 0:
        logging.debug(f"We have an application id: {application_pid}")
        application_path = subprocess.run(["cat", f"/proc/{int(application_pid)}/cmdline"],
                                          stdout=subprocess.PIPE, universal_newlines=True,
                                          encoding="UTF-8").stdout
        application_path = application_path.replace("\0", " ")
        application_path = application_path.strip()

    watcher_helper.register(window_title=active_window_title,
                            application_name=application_name,
                            application_path=application_path,
                            idle_period=idle_seconds,
                            locked_state=locked_state)
