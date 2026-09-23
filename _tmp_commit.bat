@echo off
cd /d C:\Users\Silver\Documents\skene-info
git add -A
git commit -m "postkast 23.09 (Silveri vastus): Terminal Arrivals: Valter Nomm 26.09 LISATUD www-le (a), sildid rock+alt. Uus pusireegel REEGLID 1: kontaktivormi Zanrid-vali LOEB zanriallikaks (erinevalt uudiskirjast) - korraldaja/artisti enda vaide, mitte kolmanda osapoole toimetaja. Otsustuspunkt suletud. REEGLID 8: otsustusmeili vorm umber tehtud Silveri nouetel - uritus+link ees, siis kusimus, siis 1-3 lauset."
git pull --rebase --autostash origin main
git push origin main
call priv.bat add HANDOVER.md HANDOVER-ARCHIVE.md TOOVOOG.md
call priv.bat commit -m "postkast 23.09: Terminal Arrivals lisatud www-le; otsustusmeili vorm umber (TOOVOOG 14 + 16a viitavad REEGLID 8-le)"
call priv.bat pull --rebase origin main
call priv.bat push origin main
