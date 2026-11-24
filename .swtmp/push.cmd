@echo off
cd /d C:\Users\Silver\Documents\skene-info
set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0
git -c credential.helper= -c "credential.helper=!gh auth git-credential" push origin main %* > .swtmp\pu2.log 2>&1
echo exit %errorlevel% >> .swtmp\pu2.log
