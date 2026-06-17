#!/bin/sh
# stand-in for ccache/sccache: record the compile it was asked to run, then run it
here=$(cd "$(dirname "$0")" && pwd)
echo "$@" >> "$here/launch.log"
exec "$@"
