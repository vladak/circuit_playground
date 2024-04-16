"""
safe mode handling with storing the reason to a file
"""

import json
import time

import microcontroller

# pylint: disable=import-error
import storage

# pylint: disable=import-error
import supervisor


def precode_file_write(file, data):
    """
    remount storage for writing here, write the data, remount for writing elsewhere
    """
    storage.remount("/", False)  # writeable by CircuitPython
    with open(file, "w", encoding="utf-8") as file_obj:
        file_obj.write(f"{data}\n")
        file_obj.flush()
    storage.remount("/", True)  # writeable by USB host


# set up the safemode dict
safemode_dict = {}
safemode_dict["safemode_reason"] = str(supervisor.runtime.safe_mode_reason)
safemode_dict["safemode_time"] = time.monotonic()
safemode_dict["safemode_time_ns"] = time.monotonic_ns()

# write dict as JSON. This will overwrite any pre-existing file.
precode_file_write("/safemode.json", json.dumps(safemode_dict))  # use storage.remount()

if False:  # check for any safemode conditions where we shouldn't RESET
    # Do nothing. The safe mode reason will be printed in the console,
    # and nothing will run.
    pass
else:
    # RESET out of safe mode
    microcontroller.reset()  # or alarm.exit_and_deep_sleep()
