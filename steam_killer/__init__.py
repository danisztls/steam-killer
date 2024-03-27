#!/usr/bin/env python

"""SteamKiller: Daemon that terminates Steam on Linux when certain conditions are met."""

import os
import subprocess
import datetime
import logging
import asyncio
from pathlib import Path
from dateutil.relativedelta import relativedelta
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

STEAM_DIR = os.path.expanduser("~/.steam")
STEAM_PIDFILE = Path(STEAM_DIR, "steam.pid").resolve()
ALLOWED_PERIOD = {
    "weekday": 5,
    "hour_start": 6,
    "hour_end": 18,
}  # Monday is 0 and Sunday is 6
PROC_TERM_TIMEOUT = 10  # waiting duration seconds, sends SIGKILL after


def check_steam() -> None:
    """Check if Steam is installed"""
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


def check_time(weekday, hour_start, hour_end) -> bool:
    """Check if time based conditions are met"""
    now = datetime.datetime.now()

    if now.weekday() == weekday:
        is_allowed_day = True
    else:
        is_allowed_day = False

    if (now.hour >= hour_start) and (now.hour <= hour_end):
        is_allowed_time = True
    else:
        is_allowed_time = False

    if (is_allowed_day is True) and (is_allowed_time is True):
        return True
    else:
        return False


def check_proc(pid: int, name: str):
    """Check all processes for a matching name"""
    if psutil.pid_exists(pid):
        proc = psutil.Process(pid)
        if proc.name() == name:
            return proc


def monitor() -> None:
    """Check conditions and act"""
    if not check_time(**ALLOWED_PERIOD):
        pid = read_pidfile()
        proc = check_proc(pid, "steam")
        if proc:
            terminate_proc(proc)


def read_pidfile() -> int:
    """Read Steam PID file and return the PID"""
    with open(STEAM_PIDFILE, "r") as file:
        pid = int(file.read())
        return pid


class SteamEventHandler(FileSystemEventHandler):
    """Handle file system events on Steam PID file"""

    def on_modified(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            monitor()

    def on_created(self, event):
        if event.src_path == str(STEAM_PIDFILE):
            monitor()


def notify_desktop() -> None:
    """Send notification to Desktop Environment"""
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


def terminate_proc(proc) -> None:
    """Terminate program, kill if needed"""
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


def calc_time_to_end():
    """Calculate time in seconds between now and the next end of allowed period."""
    ap=ALLOWED_PERIOD
    now = datetime.datetime.now()
    # relativedelta +1 a day so we have to -1 otherwise 0 ends up as Tuesday
    end = now + relativedelta(weekday=(ap["weekday"] - 1), hour=ap["hour_end"])
    delta = (end - now).total_seconds()
    return delta

def sched_monitor(loop):
    """Monitor when called and schedule a new call at the end of the allowed period."""
    # check first, in case steam was opened before the daemon was started
    monitor()
    delay = calc_time_to_end()
    loop.call_later(delay, sched_monitor, loop)

def main():
    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger()
    logger.info("Initializing daemon.")

    if not check_steam():
        logging.info("Exiting.")
        exit()

    # close at the end of next allowed period
    loop = asyncio.new_event_loop()
    sched_monitor(loop)

    # trigger whenever steam is opened
    pidfile_observer = Observer()
    pidfile_observer.schedule(SteamEventHandler(), STEAM_PIDFILE, recursive=False)
    pidfile_observer.start()
    pidfile_observer.join()

if __name__ == "__main__":
    main()
