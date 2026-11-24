@echo off
cd /d C:\Users\Silver\Documents\skene-info
set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0
set G=git --git-dir=C:\Users\Silver\Documents\skene-info-priv.git --work-tree=.
%G% add HANDOVER.md HANDOVER-ARCHIVE.md > .swtmp\pp.log 2>&1
%G% commit -q -m "sweep 2026-11-20: ylekontroll" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_0184nh7SPMJwvwQYHSokqJQL" >> .swtmp\pp.log 2>&1
%G% -c credential.helper= -c "credential.helper=!gh auth git-credential" push >> .swtmp\pp.log 2>&1
echo exit %errorlevel% >> .swtmp\pp.log

