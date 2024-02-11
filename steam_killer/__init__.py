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
from apscheduler.schedulers.blocking import BlockingScheduler

STEAM_DIR = os.path.expanduser("~/.steam")
STEAM_PIDFILE = Path(STEAM_DIR, "steam.pid").resolve()
ALLOWED_PERIOD={"weekday": 5, "hour_start": 6, "hour_end": 18} # Monday is 0 and Sunday is 6
PROC_TERM_TIMEOUT=10 # waiting duration seconds, sends SIGKILL after

"""Check if Steam is installed"""
def check_steam() -> None:
    if os.path.isdir(STEAM_DIR):
        logging.debug("Steam directory found.")

        if os.path.isfile(STEAM_PIDFILE):
            logging.debug("Steam PID file found.")
            return True
        else:
            logging.error("Steam PID file not found! This is weird.")
    else:
        logging.error("Steam directory not found! Is Steam installed?")

    return False

"""Check if time based conditions are met"""
def check_time(weekday=5, hour_start=6, hour_end=18) -> bool:
    now = datetime.datetime.now()

    if now.weekday() == weekday:
        is_allowed_day = True
    else:
        is_allowed_day = False
    
    if (now.hour >= hour_start) and (now.hour <= hour_end): 
        is_allowed_time = True
    else:
        is_allowed_time = False

    if (is_allowed_day == True and is_allowed_time == True):
        return True 
    else:
        return False

"""Check all processes for a matching name"""
def check_proc(pid: int, name: str):
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            if proc.name() == name:
                return proc

"""Check conditions and act"""
def monitor() -> None:
    if not check_time(ALLOWED_PERIOD):
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
            monitor()

    def on_created(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            monitor()

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
        proc.wait(PROC_TERM_TIMEOUT)
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

    if not check_steam():
        logging.info("Exiting.")
        exit()

    # in case steam was opened before the daemon was started 
    monitor()

    # trigger whenever steam is opened 
    pidfile_observer = Observer()
    pidfile_observer.schedule(SteamEventHandler(), STEAM_PIDFILE, recursive=False)
    pidfile_observer.start()
    pidfile_observer.join()

    # close steam at the end of allowed period
    scheduler = BlockingScheduler()
    scheduler.add_job(monitor, 'interval', weeks=1)
    scheduler.start()

if __name__ == "__main__":
    main()
