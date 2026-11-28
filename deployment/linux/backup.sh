#!/bin/sh
# Run with API/worker stopped for maintenance; passphrase prompted, never an argument/env/log.
set -eu
umask 077
if [ "$#" -ne 1 ]; then
    echo 'Usage: backup.sh /private/backups/new-recovery.clxrec' >&2
    exit 2
fi
exec python -m clydex_cloud.cli backup --file "$1"
