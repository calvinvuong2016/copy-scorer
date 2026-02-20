@echo off
REM One-click push so Vercel redeploys with your latest changes.
cd /d "%~dp0"
git add -A
git status
git commit -m "Update Copy Scorer" 2>nul || echo Nothing new to commit.
git push
echo.
echo Done. Check Vercel dashboard for the new deploy.
pause
