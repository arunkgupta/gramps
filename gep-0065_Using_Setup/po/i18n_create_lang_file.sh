#!/bin/sh

if [ $# -eq 1 ]
then
   msginit --input=gramps.pot --locale=$1
else
   echo "Please provide the language code as one and only argument (e.g. 'fr' for French)"
fi
