import time

from mtag.helper import filesystem_helper


def watcher_main():
    if filesystem_helper.is_windows():
        import mtag.watcher.watcher_windows as watcher
    elif filesystem_helper.is_linux():
        import mtag.watcher.watcher_linux_x11 as watcher
    else:
        raise NotImplementedError("The platform is unsupported.")

    while True:
        try:
            watcher.watch()
        except:
            print("An exception was throwned from the watcher.")

        time.sleep(2)


if __name__ == "__main__":
    watcher_main()
