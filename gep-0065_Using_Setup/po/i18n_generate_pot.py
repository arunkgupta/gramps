#!/usr/bin/env python

import os, subprocess

const_file = os.path.join("..", "src", "const.py")
const_in_file = os.path.join("..", "src", "const.py.in")
if (not os.path.isfile(const_file) and os.path.isfile(const_in_file)):

    bash_string = 'mv %s %s' % (const_in_file, const_file)
    subprocess.call(bash_string, shell=True)

# Make translation files
bash_string = "intltool-update -g gramps -o gramps.pot -p"
subprocess.call(bash_string, shell=True)
