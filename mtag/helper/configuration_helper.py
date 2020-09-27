import json
import os
from mtag.helper import filesystem_helper

WATCHER_MAX_DELTA_SECONDS_BEFORE_NEW = "watcher_max_delta_seconds_before_new"


def get_configuration():
    default_configuration = {
        WATCHER_MAX_DELTA_SECONDS_BEFORE_NEW: 10
    }

    userdata_path = filesystem_helper.get_userdata_path()
    configuration_path = os.path.join(userdata_path, "configuration.json")
    if not os.path.exists(configuration_path):
        with open(configuration_path, "w") as config_file:
            json.dump(default_configuration, fp=config_file, indent=2)

    with open(configuration_path, "r") as config_file:
        return json.load(fp=config_file)
