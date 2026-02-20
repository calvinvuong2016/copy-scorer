# Fix Vercel 404

## 1. Root Directory must be the repo root

In Vercel: **Project → Settings → General → Root Directory**

- It must be **empty** (or `.`).
- If it’s set to `web` or anything else, Vercel won’t see `public/` or `api/` and you’ll get 404.

Leave it blank, then **Redeploy** (Deployments → … on latest → Redeploy).

---

## 2. Confirm these are in your GitHub repo

On GitHub, open your repo and check:

- There is a **`public`** folder.
- Inside it there is **`index.html`**.
- At the repo root you have **`api`** (folder), **`vercel.json`**.

If `public` or `public/index.html` is missing, add and push:

```powershell
cd "c:\Users\calvi\Claude - Test"
git add public/
git status
git commit -m "Add public folder for Vercel"
git push
```

Then in Vercel click **Redeploy**.

---

## 3. Build settings (optional)

In **Project → Settings → Build & Development**:

- **Framework Preset:** Other (or leave as detected).
- **Build Command:** leave empty.
- **Output Directory:** leave empty.

Save and redeploy.
