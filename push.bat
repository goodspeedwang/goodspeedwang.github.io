::python ./build.py
git pull --rebase --autostash
git add .
git commit -a -m "%date:~0,10% %time%"
git push