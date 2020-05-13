#!/usr/bin/env bash
git pull
git add .
git commit -a -m "`date +%Y%m%e%H%M%S`"
git push
