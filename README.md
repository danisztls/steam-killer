# Steam Killer

Monitors for Steam and game processes and send SIGTERM/SIGKILL if conditions are met.

## Use case

Manage procastination.

## How it wokrs 

It uses a filesystem observer to watch `.steampid` for changes so it's triggered immediately after Steam is opened and barely use system resources. 

Conditions are hardcoded for days except Saturday or when outside daytime. Please let me know if you want want to use this with different conditions.
