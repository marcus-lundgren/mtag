import os, sys


def is_windows():
    return sys.platform == "win32"


def is_linux():
    return sys.platform.startswith("linux")


def get_userconfiguration_path():
    if is_linux():
        home_path = os.environ["HOME"]
        xdg_config_home = "XDG_CONFIG_HOME"
        base_path = os.environ[xdg_config_home] if xdg_config_home in os.environ else os.path.join(home_path,
                                                                                                   ".config")
    elif is_windows():
        base_path = os.environ["APPDATA"]
    else:
        raise OSError("Incompatible operative system")

    return get_mtag_path(base_path)


def get_userdata_path():
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

    return get_mtag_path(base_path)


def get_mtag_path(base_path: str) -> str:
    mtag_path = os.path.join(base_path, "mtag")
    if not os.path.exists(mtag_path):
        os.mkdir(mtag_path)

    return mtag_path
