# ⚡ Quick Deploy Guide (5 Minutes)

For experienced users who want to deploy fast.

---

## 1️⃣ Set App Password (30 seconds)

Edit `.env`:
```bash
APP_PASSWORD=YourTeamPassword123
```

---

## 2️⃣ Push to GitHub (2 minutes)

```bash
cd "/Users/magicben/Desktop/Client portfolio"

# Initialize
git init
git add .
git commit -m "Initial commit"

# Push (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/structured-notes-tracker.git
git branch -M main
git push -u origin main
```

**Note:** Use Personal Access Token as password (https://github.com/settings/tokens)

---

## 3️⃣ Deploy to Streamlit Cloud (2 minutes)

1. Go to: https://streamlit.io/cloud
2. Sign up with GitHub
3. Click "New app"
4. Select your repo → `app_new.py`
5. **Advanced Settings** → **Secrets**:

```toml
DATABASE_URL = "postgresql://postgres.soinvgzykhdkhtmywoiq:Trading2025$@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
APP_PASSWORD = "YourTeamPassword123"
```

6. Click "Deploy!"

---

## 4️⃣ Share with Team

URL: `https://YOUR-APP.streamlit.app`
Password: `YourTeamPassword123`

---

## ✅ Done!

Your app is live and accessible worldwide! 🌍

---

## 🔄 Update App Later

```bash
git add .
git commit -m "Update message"
git push origin main
```

Auto-deploys in 1-2 minutes.

