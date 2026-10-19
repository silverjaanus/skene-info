@echo off
cd /d C:\Users\Silver\Documents\skene-info
git rm --cached _tmp_commit.bat
git commit -m "eemalda kogemata commititud ajutine skript _tmp_commit.bat"
git push origin main
del _tmp_commit.bat
