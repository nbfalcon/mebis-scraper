import os
import time


def await_download(dir_watch):
    # the directory is dedicated to one download. As such it will
    # either be empty (download not started yet), or contain two files:
    # the main file and it's .part counterpart. Either way, we must
    # wait until all that remains is the main file.
    while len(os.listdir(dir_watch)) != 1:
        time.sleep(1)
