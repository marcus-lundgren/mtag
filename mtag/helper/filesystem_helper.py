import os


def get_userdata_path():
    home_path = os.environ["HOME"]
    userdata_path = f"{home_path}/.config/mtag/"
    if not os.path.exists(userdata_path):
        os.mkdir(userdata_path)
    return userdata_path
