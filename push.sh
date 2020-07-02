#! /bin/bash
# python3 ./build.py
git pull
git add .
git commit -a -m "`date +%Y%m%e%H%M%S`"
git push