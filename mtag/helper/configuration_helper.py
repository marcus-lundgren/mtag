import json
import os
from mtag.helper import filesystem_helper


class Configuration:
    def __init__(self, inactive_after_idle_seconds: int, seconds_before_new_entry: int, log_application_path: bool):
        self.inactive_after_idle_seconds = inactive_after_idle_seconds
        self.seconds_before_new_entry = seconds_before_new_entry
        self.log_application_path = log_application_path


def get_configuration() -> Configuration:
    default_configuration = {
        "seconds_before_new_entry": 10,
        "inactive_after_idle_seconds": 600,
        "log_application_path": False
    }

    userconfig_path = filesystem_helper.get_userconfiguration_path()
    configuration_path = os.path.join(userconfig_path, "configuration.json")
    if not os.path.exists(configuration_path):
        with open(configuration_path, "w") as config_file:
            json.dump(default_configuration, fp=config_file, indent=2)

    with open(configuration_path, "r") as config_file:
        read_configuration = json.load(fp=config_file)

    for k, v in default_configuration.items():
        if k not in read_configuration:
            read_configuration[k] = v

    return Configuration(**read_configuration)
