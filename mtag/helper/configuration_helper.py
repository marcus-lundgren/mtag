import json
import os
from typing import Dict

from mtag.helper import filesystem_helper


class Configuration:
    default_configuration = {
        "seconds_before_new_entry": 10,
        "inactive_after_idle_seconds": 600,
        "log_application_path": False
    }

    def __init__(self, inactive_after_idle_seconds: int, seconds_before_new_entry: int, log_application_path: bool):
        self.inactive_after_idle_seconds = inactive_after_idle_seconds
        self.seconds_before_new_entry = seconds_before_new_entry
        self.log_application_path = log_application_path

    def asdict(self) -> Dict:
        d = {k: self.__getattribute__(k) for k, v in Configuration.default_configuration.items()}
        return d


def get_configuration() -> Configuration:
    configuration_path = get_configuration_path()
    if not os.path.exists(configuration_path):
        save_configuration(Configuration.default_configuration)

    with open(configuration_path, "r") as config_file:
        read_configuration = json.load(fp=config_file)

    for k, v in Configuration.default_configuration.items():
        if k not in read_configuration:
            read_configuration[k] = v

    return Configuration(**read_configuration)


def save_configuration(configuration):
    with open(get_configuration_path(), "w") as config_file:
        json.dump(configuration, fp=config_file, indent=2)


def get_configuration_path():
    userconfig_path = filesystem_helper.get_userconfiguration_path()
    configuration_path = os.path.join(userconfig_path, "configuration.json")
    return configuration_path


def update_configuration(new_configuration: Configuration) -> None:
    configuration_to_save = new_configuration.asdict()
    save_configuration(configuration_to_save)
