#!/usr/bin/env python

"""SteamKiller: Daemon that terminates Steam on Linux when certain conditions are met."""

import os
import subprocess
import datetime
import logging
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
            terminate_proc(proc)

"""Read Steam PID file and return the PID"""
def read_pidfile() -> int:
    with open(STEAM_PIDFILE, 'r') as file:
        pid = int(file.read())
        return pid

"""Handle file system events on Steam PID file"""
class SteamEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            check()

    def on_created(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            check()

"""Send notification to Desktop Environment"""
def notify_desktop() -> None:
    summary = "Steam Killer"
    body = "Terminating Steam."
    cmd_list = ["notify-send", summary, body]

    icon = "/usr/share/icons/hicolor/256x256/apps/steam.png"
    if os.path.isfile(icon):
        cmd_list.append("--icon")
        cmd_list.append(icon)

    try:
        subprocess.run(cmd_list, check=True)
    except OSError:
        logging.warning("Failed to send desktop notification.")

"""Terminate program, kill if needed"""
def terminate_proc(proc) -> None:
    notify_desktop()

    try:
        logging.info(f"SIGTERM {proc}")
        proc.terminate()
        proc.wait(10)
    except psutil.TimeoutExpired:
        logging.warning(f"SIGKILL {proc}")
        proc.kill()
    else:
        logging.info(f"process {proc} terminated.")

def main():
    logging.basicConfig(
                        format='[%(levelname)s] %(message)s',
                        level=logging.DEBUG,
                        handlers=[logging.StreamHandler()])
    logger = logging.getLogger()
    logger.info("Initializing daemon.")

    # initial check
    check()

    # continuous watch
    observer = Observer()
    observer.schedule(SteamEventHandler(), STEAM_PIDFILE, recursive=False)
    observer.start()
    observer.join()

if __name__ == "__main__":
    main()
