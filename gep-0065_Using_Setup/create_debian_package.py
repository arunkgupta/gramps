#!/usr/bin/env python

import os, sys, subprocess

# determine if the debian directory is available, then run it?
if not os.path.isdir(os.path.join(os.getcwd(), 'debian')):
    sys.exit(1)

bash_string = "dpkg-buildpackage -b -d -tc"
subprocess.call(bash_string, shell=True)
