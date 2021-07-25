import datetime
from collections import namedtuple
from ctypes import *
import subprocess
import logging
from ctypes import cast
from ctypes.wintypes import HANDLE, MAX_PATH, DWORD

from . import watcher_helper


class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', DWORD),
    ]


class LANGANDCODEPAGE(Structure):
    _fields_ = [
        ("wLanguage", c_uint16),
        ("wCodePage", c_uint16)]


LastInputTimeTuple = namedtuple("LastInputTimeTuple", ["tick", "dt"])
last_input_time = LastInputTimeTuple(tick=None, dt=None)


# https://stackoverflow.com/a/912223
def get_idle_duration() -> int:
    global last_input_time
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = sizeof(last_input_info)
    windll.user32.GetLastInputInfo(byref(last_input_info))
    now = datetime.datetime.now()
    if last_input_info.dwTime != last_input_time.tick:
        last_input_time = LastInputTimeTuple(tick=last_input_info.dwTime, dt=now)
    return int((now - last_input_time.dt).total_seconds())


def get_locked_state():
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


PROCESS_QUERY_INFORMATION = 0x0400


def watch():
    logging.info("== STARTED ==")

    pid_param = c_ulong()
    idle_period = get_idle_duration()
    locked_state = get_locked_state()
    application_path = None
    application_name = None
    active_window_title = None

    if locked_state:
        watcher_helper.register(window_title=active_window_title,
                                application_name=application_name,
                                application_path=application_path,
                                idle_period=idle_period,
                                locked_state=locked_state)
        return

    try:
        # Get foreground window handle
        window_handle = windll.user32.GetForegroundWindow()
        logging.debug(f"Got window handle: {window_handle}")

        # Get the window title length
        window_title_size = windll.user32.GetWindowTextLengthW(window_handle) + 1
        logging.debug("Length of window title: {window_title_size}")

        # Get the window title
        unicode_buffer = create_unicode_buffer(window_title_size)
        windll.user32.GetWindowTextW(window_handle, unicode_buffer, window_title_size)
        active_window_title = unicode_buffer.value
        logging.debug(active_window_title)

        # Get the process id
        windll.user32.GetWindowThreadProcessId(window_handle, byref(pid_param))
        logging.debug(f"Got process ID: {pid_param.value}")

        # Get the path of the process exe
        process_handle: HANDLE = windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION,
                                                             False, pid_param)
        image_name = create_unicode_buffer(MAX_PATH)
        max_path_as_dword = DWORD(MAX_PATH*16)
        result = windll.kernel32.QueryFullProcessImageNameW(process_handle, 0,
                                                            image_name, byref(max_path_as_dword))
        if result == 0:
            raise OSError("Unable to find the application path")

        application_path = image_name.value
        logging.debug(application_path)

        # Get the file version info
        file_version_info_size = windll.version.GetFileVersionInfoSizeW(image_name, None)
        file_version_info_data = create_string_buffer(file_version_info_size)
        windll.version.GetFileVersionInfoW(image_name, None,
                                           file_version_info_size, byref(file_version_info_data))

        query_value_p = c_void_p(0)
        query_value_length = c_uint()
        windll.version.VerQueryValueW(file_version_info_data, "\\\\VarFileInfo\\Translation",
                                      byref(query_value_p), byref(query_value_length))
        value_as_lacp = cast(query_value_p, POINTER(LANGANDCODEPAGE))
        language = f"{value_as_lacp.contents.wLanguage:04x}{value_as_lacp.contents.wCodePage:04x}"

        query_value_p = c_void_p(0)
        for info in ["FileDescription", "OriginalFilename", "ProductName"]:
            ver_res = windll.version.VerQueryValueW(file_version_info_data,
                                                    f"\\StringFileInfo\\{language}\\{info}",
                                                    byref(query_value_p), byref(query_value_length))
            # Go to the next potential value if we got an error
            if ver_res == 0:
                continue

            current_value = wstring_at(query_value_p.value, query_value_length.value)
            # We really shouldn't need to, but I've seen some names with
            # a NUL character in them which then also includes e.g. the file version.
            # This happened with e.g. IBM Notes.
            if "\0" in current_value:
                current_value = current_value[0:current_value.index("\0")]

            # Ensure that we've got at least something as a value
            if 0 < len(current_value):
                logging.debug(f"Setting application name to {current_value}, fetched from {info}")
                application_name = current_value
                break

        logging.debug(application_name)
    except Exception as ex:
        logging.error(f"An unhandled error occurred in the Windows watcher: {ex}")

    watcher_helper.register(window_title=active_window_title,
                            application_name=application_name,
                            application_path=application_path,
                            idle_period=idle_period,
                            locked_state=locked_state)
