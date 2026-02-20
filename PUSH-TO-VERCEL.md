# Push to Vercel (one step)

The AI can't run `git push` from inside Cursor on your machine, so use this instead.

**Easiest:** Double-click **`push-to-vercel.bat`** in your project folder.

It will:
1. Stage all changes
2. Commit with message "Update Copy Scorer"
3. Push to GitHub (so Vercel can deploy)

Then hard-refresh your Vercel app (Ctrl+Shift+R) to see updates.

---

**From terminal (same result):**
```bash
cd "c:\Users\calvi\Claude - Test"
.\push-to-vercel.bat
```

Or run the commands yourself:
```bash
git add -A
git commit -m "Update Copy Scorer"
git push
```
