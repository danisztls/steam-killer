#!/usr/bin/env python
"""SteamKiller: Daemon that terminates Steam on Linux when certain conditions are met."""

import datetime
import psutil

"""Check if conditions to terminate program are met"""
def check_conditions() -> bool:
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
def check_procs(name: str) -> list:
    procs = []
    for proc in psutil.process_iter(['pid', 'name']):
        if (proc.is_running() and proc.name() == name):
            procs.append(proc)
    return procs

""" Notify on process termination"""
def on_terminate(proc) -> None:
    print(f"SteamKiller: process {proc} terminated.")

"""Terminate program, kill if needed"""
def terminate_procs(procs: list) -> None:
    for p in procs:
        p.terminate()
    
    gone, alive = psutil.wait_procs(procs, timeout=7, callback=on_terminate)

    for p in alive:
        p.kill()

def main():
    # TODO: Implement daemon to check conditions every minute. 
    # Can it be smarter than that? Should I use systemd instead?

    print("SteamKiller: Initializing daemon.")

    if check_conditions():
        procs = check_procs("steam")
        if procs:
            # TODO: Sent GNOME notification
            print("SteamKiller: Conditions are met.")
            for p in procs:
                print(f"SteamKiller: SIGTERM {p}")
            terminate_procs(procs)

if __name__ == "__main__":
    main()
