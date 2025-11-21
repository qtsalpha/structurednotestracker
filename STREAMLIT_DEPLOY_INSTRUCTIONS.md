# ☁️ Deploy to Streamlit Cloud

## Follow These Steps:

### Step 1: Create Streamlit Cloud Account

1. Go to: https://streamlit.io/cloud
2. Click **"Sign up"**
3. Choose **"Continue with GitHub"**
4. Authorize Streamlit to access your GitHub

### Step 2: Create New App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository**: `qtsalpha/structurednotestracker`
   - **Branch**: `main`
   - **Main file path**: `app_new.py`
   - **App URL**: Choose a name (e.g., `qts-structured-notes`)

### Step 3: Configure Secrets (CRITICAL!)

⚠️ **BEFORE clicking Deploy**, click **"Advanced settings"**

Find the **"Secrets"** section and paste this EXACTLY:

```toml
DATABASE_URL = "postgresql://postgres.soinvgzykhdkhtmywoiq:Trading2025$@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
APP_PASSWORD = "StructuredNotes2025!"
APP_TITLE = "Structured Notes Tracker"
PRICE_UPDATE_DELAY = "0.2"
```

⚠️ **IMPORTANT:**
- Use `Trading2025$` (NOT `Trading2025%24`)
- Keep the quotes
- Copy exactly as shown

### Step 4: Deploy!

1. Click **"Deploy!"**
2. Wait 2-3 minutes
3. Your app will be live!

### Step 5: Get Your URL

After deployment, you'll get a URL like:
```
https://qts-structured-notes.streamlit.app
```

**Copy this URL** - you'll share it with your team!

---

## 🔐 Login Credentials for Your Team:

**URL**: https://YOUR-APP-NAME.streamlit.app
**Password**: `StructuredNotes2025!`

---

## ✅ Testing Your Deployed App

1. Open the URL in incognito/private window
2. Enter password: `StructuredNotes2025!`
3. Check Settings page - should show "POSTGRESQL"
4. Try adding a note
5. Try importing Excel

---

## 🎉 You're Live!

Share these with your team:
- App URL
- Password
- Instructions on how to use

---

Need help? Return to the chat and let me know!



