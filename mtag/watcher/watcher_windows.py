from ctypes import *
import subprocess
import logging
from . import watcher_helper

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


# https://stackoverflow.com/a/912223
def get_idle_duration():
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = sizeof(last_input_info)
    windll.user32.GetLastInputInfo(byref(last_input_info))
    millis = windll.kernel32.GetTickCount() - last_input_info.dwTime
    return millis // 1000


def get_locked_state():
    global session_id
    locked_hint = subprocess.run(["tasklist", '/FI', "IMAGENAME eq LogonUI.exe"],
                                 stdout=subprocess.PIPE).stdout.strip()
    if locked_hint == b"INFO: No tasks are running which match the specified criteria.":
        logging.debug("Not locked")
        return False
    elif b"LogonUI.exe" in locked_hint:
        logging.debug("Locked")
        return True
    else:
        logging.warning("Unknown lock hint:", locked_hint)
        return False


def watch():
    logging.info("== STARTED ==")

    pid_param = c_ulong()
    idle_period = get_idle_duration()
    locked_state = get_locked_state()
    window_handle = windll.user32.GetForegroundWindow()
    logging.debug(f"Got window handle: {window_handle}")

    windll.user32.GetWindowThreadProcessId(windll.user32.GetForegroundWindow(), byref(pid_param))
    logging.debug(f"Got process ID: {pid_param}")

    window_title_size = windll.user32.GetWindowTextLengthW(window_handle) + 1
    logging.debug("Length of window title:", window_title_size)

    unicode_buffer = create_unicode_buffer(window_title_size)
    windll.user32.GetWindowTextW(window_handle, unicode_buffer, window_title_size)
    active_window_title = unicode_buffer.value
    logging.debug(unicode_buffer.value)

    sui = subprocess.STARTUPINFO()
    sui.dwFlags = subprocess.STARTF_USESTDHANDLES | subprocess.STARTF_USESHOWWINDOW
    with subprocess.Popen(["powershell.exe",
                           "Get-Process -Id " + str(pid_param.value)
                           + " | Format-List Name, Description, Path, Product"],
                          stdout=subprocess.PIPE,
                          startupinfo=sui,
                          shell=False,
                          creationflags=subprocess.CREATE_NEW_CONSOLE) as proc:
        ps_output_as_bytes, _ = proc.communicate()
        logging.debug(ps_output_as_bytes)

    ps_output = ps_output_as_bytes.decode('utf-8', errors="backslashreplace")
    logging.debug(ps_output)
    ps_values = {}

    if "Get-Process : Cannot find a process with the process identifier" in ps_output:
        logging.warning("Unable to find process data. Register what we have.")
        watcher_helper.register(window_title=active_window_title,
                                application_name=None,
                                application_path=None,
                                idle_period=idle_period,
                                locked_state=locked_state)
        return

    for line in ps_output.splitlines():
        stripped_line = line.strip()
        if len(stripped_line) == 0:
            continue

        try:
            colon_index = stripped_line.index(":")
            key = line[:colon_index].strip()
            value = line[colon_index + 1:].strip()
            ps_values[key] = value
        except:
            logging.error(ps_output)
            logging.error("Unable to parse ps_output line:")
            logging.error(stripped_line)
            logging.error(f"The following PID was found: {pid_param.value}")
            logging.error("Window title: {active_window_title}")

    path = ps_values["Path"]

    application_name = "N/A"
    naming_priority = ["Description", "Name", "Product"]
    for np in naming_priority:
        np_value = ps_values[np]
        if len(np_value) > 0:
            application_name = np_value
            break

    watcher_helper.register(window_title=active_window_title,
                            application_name=application_name,
                            application_path=path,
                            idle_period=idle_period,
                            locked_state=locked_state)
