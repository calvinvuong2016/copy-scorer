# Host Copy Scorer so you can use it from a link

You can host on **Vercel** or **Render**. No commands to run—just connect the repo and open the link.

---

## Option A: Vercel (recommended)

1. Push the project to **GitHub** (see step 1 below if needed).
2. Go to **[vercel.com](https://vercel.com)** and sign in (e.g. with GitHub).
3. Click **Add New…** → **Project**.
4. **Import** your GitHub repo (the one that contains `api/`, `public/`, and `vercel.json`).
5. Leave the default settings (Vercel will detect the structure). Click **Deploy**.
6. When it’s done, you get a URL like **`https://your-project-xxx.vercel.app`**. Use that link anytime.

No build or start commands needed. The `api/` folder runs as serverless functions; `public/index.html` is served at the root.

**Rewrite with Claude:** To use framework-driven rewrites (not the template fallback), set **`ANTHROPIC_API_KEY`** in the project: **Settings → Environment Variables** → add `ANTHROPIC_API_KEY` with your key → redeploy. (Local runs use the `.env` file in the project root.)

---

## Option B: Render

## 1. Put the project on GitHub

If it’s not there yet:

1. Create a new repo on [github.com](https://github.com) (e.g. `copy-scorer`).
2. In your project folder (`Claude - Test`), run:

   ```bash
   git init
   git add .
   git commit -m "Copy Scorer app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

   (Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your repo.)

---

## 2. Deploy on Render

1. Go to **[render.com](https://render.com)** and sign up (free; GitHub login is fine).
2. **Dashboard** → **New** → **Web Service**.
3. **Connect** your GitHub account if needed, then select the repo you pushed (e.g. `copy-scorer`).
4. Use these settings:

   | Field | Value |
   |--------|--------|
   | **Name** | `copy-scorer` (or any name) |
   | **Root Directory** | `web` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

5. Click **Create Web Service**.
6. Wait for the first deploy to finish (a few minutes).
7. Your app will be at a URL like:  
   **`https://copy-scorer-xxxx.onrender.com`**

That’s the link you can use from anywhere—no commands to run.

---

## Free tier notes (Render)

- The app **spins down** after about 15 minutes of no use. The first visit after that may take up to a minute to load.
- You get a limited number of free hours per month; for light use it’s usually enough.

---

## Optional: other hosts (Railway, Fly.io)

- **Railway** – [railway.app](https://railway.app): New Project → Deploy from GitHub → choose repo, set **Root Directory** to `web`, **Start Command** to `uvicorn server:app --host 0.0.0.0 --port $PORT`. Add `requirements.txt` in `web/` if needed.
- **Fly.io** – You’d add a `Dockerfile` and run `fly launch` once; then the app is available at a `*.fly.dev` URL.

If you tell me which host you prefer (Render vs Railway vs Fly), I can tailor the steps or add config files for it.
