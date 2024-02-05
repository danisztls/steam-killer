#!/usr/bin/env python
"""SteamKiller: Daemon that terminates Steam on Linux when certain conditions are met."""

import os
import datetime
from pathlib import Path
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

STEAM_PIDFILE = Path(os.path.expanduser("~/.steampid")).resolve()

"""Check if time based conditions are met"""
def check_time() -> bool:
    now = datetime.datetime.now()

    # Only Saturday is allowed
    if now.weekday() == 5:  # In Python, Monday is 0 and Sunday is 6
        is_saturday = True
    else:
        is_saturday = False
    
    # Only daytime is allowed
    # TODO: Get local sunrise/sunset time
    if (now.hour >= 6) and (now.hour <= 18): 
        is_daytime = True
    else:
        is_daytime = False

    if (is_saturday == True and is_daytime == True):
        return False
    else:
        return True # kill process

"""Check all processes for a matching name"""
def check_proc(pid: int, name: str):
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            if proc.name() == name:
                return proc

"""Check time conditions, running processes and terminate."""
def check() -> None:
    if check_time():
        pid = read_pidfile()
        proc = check_proc(pid, "steam")
        if proc:
            # TODO: Send Desktop notification
            terminate_proc(proc)

"""Read Steam PID file and return the PID"""
def read_pidfile() -> int:
    try:
        with open(STEAM_PIDFILE, 'r') as file:
            return int(file.read())
    except FileNotFoundError:
        print("Steam PID file not found.")
    except IOError:
        print("Error occurred while reading Steam PID file.")

"""Handle file system events on Steam PID file"""
class SteamEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            check()

    def on_created(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            check()

"""Terminate program, kill if needed"""
def terminate_proc(proc) -> None:
    try:
        print(f"SteamKiller: SIGTERM {proc}")
        proc.terminate()
        proc.wait(10)
    except psutil.TimeoutExpired:
        print(f"SteamKiller: SIGKILL {proc}")
        proc.kill()
    else:
        print(f"SteamKiller: process {proc} terminated.")

def main():
    print("SteamKiller: Initializing daemon.")
    check()
    observer = Observer()
    observer.schedule(SteamEventHandler(), STEAM_PIDFILE, recursive=False)
    observer.start()
    observer.join()

if __name__ == "__main__":
    main()
