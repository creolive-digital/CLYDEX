#!/bin/sh
# Target must be an isolated migrated empty database, empty vault and empty keys directory.
set -eu
umask 077
if [ "$#" -ne 1 ]; then
    echo 'Usage: restore.sh /private/backups/recovery.clxrec' >&2
    exit 2
fi
exec python -m clydex_cloud.cli restore --file "$1"
