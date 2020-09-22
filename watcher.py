import subprocess
import re
from mtag.helper import watcher_helper

print("== STARTED ==")

active_window_id_information = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                                              stdout=subprocess.PIPE, universal_newlines=True).stdout
# print(active_window_id_information)

active_window_id = active_window_id_information[active_window_id_information.rfind(" ") + 1:].strip()
# print(active_window_id)
if active_window_id == "0x0":
    print("No active window.")
    exit(0)

active_window_x11_information = subprocess.run(["xprop", "-id", active_window_id,
                                                "_NET_WM_PID", "WM_CLASS", "WM_NAME", "_NET_WM_NAME"],
                                               stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
# print(active_window_x11_information)

application_pid = ""
application_name = ""
active_window_title = ""
for line in active_window_x11_information.splitlines():
    if line.startswith("_NET_WM_PID"):
        application_pid = line[line.find("=") + 2:]
        # print(application_pid)
    elif line.startswith("_NET_WM_NAME"):
        active_window_title = line[line.find("=") + 2:].strip('"')
        # print(active_window_title)
    elif line.startswith("WM_NAME"):
        # Do not parse this if we already got a value
        if len(active_window_title) > 0:
            print("Application window title already set")
            continue
        application_window_title = line[line.find("=") + 2:].strip('"')
        # print(application_window_title)
    elif line.startswith("WM_CLASS"):
        # Ensure that we get the value on the right. As a double quote might be escaped
        # inside of the left hand side, ensure that we match the correct double quote characters.
        wm_class_name_pattern = re.compile(r'[^\\]",\s*"\s*(.*)\s*"$')
        pattern_matches = wm_class_name_pattern.findall(line)
        if len(pattern_matches) > 0:
            application_name = pattern_matches[0]
        else:
            print("Unable to extract the right hand side WM_CLASS value.")

# print(application_pid)
application_path = None

if application_pid.isdigit() and application_pid != 0:
    application_path = subprocess.run(["cat", f"/proc/{int(application_pid)}/cmdline"],
                                      stdout=subprocess.PIPE, universal_newlines=True).stdout
    application_path = application_path.replace("\0", " ")
    application_path = application_path.strip()

print(application_path)
print(f"{application_name} -> {active_window_title}")
watcher_helper.register(window_title=active_window_title,
                        application_name=application_name,
                        application_path=application_path)
