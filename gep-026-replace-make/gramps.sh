#! /bin/sh
export GRAMPSDIR=/usr/lib/python2.7/site-packages/gramps
exec /usr/bin/python -O $GRAMPSDIR/gramps.py "$@"
