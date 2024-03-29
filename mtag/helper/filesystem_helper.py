import os
import sys
from typing import Optional
import logging


user_configuration_path: Optional[str] = None
user_data_path: Optional[str] = None
user_data_backup_path: Optional[str] = None


def is_windows():
    return sys.platform == "win32"


def is_linux():
    return sys.platform.startswith("linux")


def get_userconfiguration_path() -> str:
    global user_configuration_path
    if user_configuration_path is not None:
        return user_configuration_path

    if is_linux():
        home_path = os.environ["HOME"]
        xdg_config_home = "XDG_CONFIG_HOME"
        base_path = os.environ[xdg_config_home] if xdg_config_home in os.environ else os.path.join(home_path,
                                                                                                   ".config")
    elif is_windows():
        base_path = os.environ["APPDATA"]
    else:
        raise OSError("Incompatible operative system")

    user_configuration_path = _get_mtag_path(base_path)
    return user_configuration_path


def get_userdata_path() -> str:
    global user_data_path
    if user_data_path is not None:
        return user_data_path

    if is_linux():
        home_path = os.environ["HOME"]
        xdg_data_home = "XDG_DATA_HOME"
        base_path = os.environ[xdg_data_home] if xdg_data_home in os.environ else os.path.join(home_path,
                                                                                               ".local",
                                                                                               "share")
    elif is_windows():
        base_path = os.environ["APPDATA"]
    else:
        raise OSError("Incompatible operative system")

    user_data_path = _get_mtag_path(base_path)
    return user_data_path


def get_userdatabackup_path() -> str:
    global user_data_backup_path
    if user_data_backup_path is not None:
        return user_data_backup_path

    user_data_backup_path = os.path.join(get_userdata_path(), "backup")
    if not os.path.exists(user_data_backup_path):
        os.mkdir(user_data_backup_path)

    return user_data_backup_path


def purge_backups_if_needed() -> None:
    backup_directory_contents = [f for f in os.listdir(get_userdatabackup_path())
                                 if f.endswith(".db")]

    MAX_BACKUPS_TO_KEEP = 3
    if len(backup_directory_contents) <= MAX_BACKUPS_TO_KEEP:
        return

    backup_directory_contents.sort()
    global user_data_backup_path
    for f in backup_directory_contents[:-MAX_BACKUPS_TO_KEEP]:
        logging.info(f"Removing backup '{f}'")
        os.remove(os.path.join(user_data_backup_path, f))


def _get_mtag_path(base_path: str) -> str:
    mtag_path = os.path.join(base_path, "mtag")
    if not os.path.exists(mtag_path):
        os.mkdir(mtag_path)

    return mtag_path
