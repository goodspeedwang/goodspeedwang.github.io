::python ./build.py
git pull
git add .
git commit -a -m "%date:~0,10% %time%"
git push