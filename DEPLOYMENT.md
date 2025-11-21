# 🚀 Deployment Guide - Structured Notes Tracker

This guide will walk you through deploying your Structured Notes Tracker to the cloud for production use.

## 📋 Table of Contents

1. [Quick Start (Easiest)](#quick-start-streamlit-cloud--supabase)
2. [Alternative Deployment Options](#alternative-deployment-options)
3. [Local Development Setup](#local-development-setup)
4. [Environment Variables](#environment-variables)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start: Streamlit Cloud + Supabase

**Estimated Time: 30 minutes**  
**Cost: FREE (with limitations)**

This is the easiest and recommended path for getting started.

### Step 1: Set Up Cloud Database (Supabase)

1. **Create Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Sign up with GitHub (easiest)
   - Click "New Project"

2. **Create Your Project**
   - Name: `structured-notes-tracker`
   - Database Password: **Save this password!** You'll need it
   - Region: Choose closest to you
   - Click "Create new project" (takes ~2 minutes)

3. **Get Your Database URL**
   - Go to Project Settings → Database
   - Find "Connection string" → "URI"
   - Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
   - **Replace `[YOUR-PASSWORD]` with your actual password**

4. **Set Up Tables**
   - Go to SQL Editor in Supabase dashboard
   - Paste the following SQL:
   ```sql
   CREATE TABLE IF NOT EXISTS structured_notes (
       id SERIAL PRIMARY KEY,
       customer_name TEXT NOT NULL,
       custodian_bank TEXT,
       type_of_structured_product TEXT NOT NULL,
       notional_amount REAL,
       isin TEXT,
       trade_date DATE,
       issue_date DATE,
       observation_start_date DATE,
       final_valuation_date DATE,
       coupon_payment_dates TEXT,
       coupon_per_annum REAL,
       coupon_barrier REAL,
       ko_type TEXT,
       ko_observation_frequency TEXT,
       ki_type TEXT,
       current_status TEXT DEFAULT 'Not Observed Yet',
       ko_event_occurred INTEGER DEFAULT 0,
       ko_event_date DATE,
       ki_event_occurred INTEGER DEFAULT 0,
       ki_event_date DATE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   CREATE TABLE IF NOT EXISTS note_underlyings (
       id SERIAL PRIMARY KEY,
       note_id INTEGER NOT NULL,
       underlying_sequence INTEGER NOT NULL,
       underlying_name TEXT,
       underlying_ticker TEXT,
       spot_price REAL,
       strike_price REAL,
       ko_price REAL,
       ki_price REAL,
       last_close_price REAL,
       last_price_update TIMESTAMP,
       FOREIGN KEY (note_id) REFERENCES structured_notes(id) ON DELETE CASCADE,
       UNIQUE(note_id, underlying_sequence)
   );

   CREATE INDEX IF NOT EXISTS idx_customer_name ON structured_notes(customer_name);
   CREATE INDEX IF NOT EXISTS idx_product_type ON structured_notes(type_of_structured_product);
   CREATE INDEX IF NOT EXISTS idx_note_underlyings_note_id ON note_underlyings(note_id);
   CREATE INDEX IF NOT EXISTS idx_underlying_ticker ON note_underlyings(underlying_ticker);
   ```
   - Click "Run" → You should see "Success"

### Step 2: Prepare Your Code for GitHub

1. **Create GitHub Account** (if you don't have one)
   - Go to [github.com](https://github.com)
   - Sign up for free

2. **Create New Repository**
   - Click "New repository"
   - Name: `structured-notes-tracker`
   - Make it **Private** (important for security!)
   - Don't initialize with README
   - Click "Create repository"

3. **Upload Your Code**
   
   **Option A: Use GitHub Desktop (Easier)**
   - Download [GitHub Desktop](https://desktop.github.com)
   - File → Add Local Repository → Select your project folder
   - Click "Publish repository"
   - Make sure "Keep this code private" is checked
   - Click "Publish Repository"

   **Option B: Use Command Line**
   ```bash
   cd "/Users/magicben/Desktop/Client portfolio"
   git init
   git add .
   git commit -m "Initial commit - Structured Notes Tracker"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/structured-notes-tracker.git
   git push -u origin main
   ```

### Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Click "Sign up" → Use your GitHub account
   - Authorize Streamlit

2. **Deploy Your App**
   - Click "New app"
   - Repository: Select `structured-notes-tracker`
   - Branch: `main`
   - Main file path: `app_new.py`
   - Click "Deploy!"

3. **Configure Secrets**
   - While app is deploying, click "Advanced settings" (gear icon)
   - Click "Secrets"
   - Paste the following (replace with YOUR values):
   ```toml
   # Database connection
   DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
   
   # Optional: Add password protection
   APP_PASSWORD = "your_secure_password_here"
   
   # Optional: Custom title
   APP_TITLE = "Structured Notes Tracker"
   ```
   - Click "Save"

4. **Wait for Deployment**
   - Takes 2-5 minutes
   - You'll see a URL like: `https://your-app.streamlit.app`

5. **🎉 Done! Your app is live!**
   - Visit your URL
   - If you set APP_PASSWORD, you'll need to login
   - Start adding your structured notes

---

## 🔄 Alternative Deployment Options

### Option 2: Railway (Good PostgreSQL Alternative)

**Cost: $5/month (includes database)**

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository

3. **Add PostgreSQL**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway automatically provisions it

4. **Configure Environment Variables**
   - Click your web service
   - Go to "Variables"
   - Add:
     - `DATABASE_URL`: (Railway auto-generates this)
     - `APP_PASSWORD`: your_password

5. **Deploy**
   - Railway auto-deploys on push
   - Get your URL from the deployment

### Option 3: Render (Free Tier Available)

**Cost: Free (with limitations) or $7/month**

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create PostgreSQL Database**
   - New → PostgreSQL
   - Name: `structured-notes-db`
   - Free tier is fine for testing
   - Copy the "Internal Database URL"

3. **Create Web Service**
   - New → Web Service
   - Connect your GitHub repo
   - Settings:
     - Name: `structured-notes-tracker`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `streamlit run app_new.py --server.port $PORT --server.address 0.0.0.0`

4. **Add Environment Variables**
   - Add `DATABASE_URL` with your Postgres URL
   - Add `APP_PASSWORD` if desired

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deploy

---

## 💻 Local Development Setup

To run and test locally before deploying:

1. **Install Python 3.9+**
   - Download from [python.org](https://python.org)

2. **Install Dependencies**
   ```bash
   cd "/Users/magicben/Desktop/Client portfolio"
   pip install -r requirements.txt
   ```

3. **Create .env File** (optional)
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` to add your settings
   - For local dev, you can leave DATABASE_URL empty (uses SQLite)

4. **Run the App**
   ```bash
   streamlit run app_new.py
   ```
   - Opens in browser at `http://localhost:8501`

5. **Test Changes**
   - Make your changes
   - App auto-reloads
   - When ready, commit and push to GitHub

---

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PASSWORD` | Password protection | None (no password) |
| `APP_TITLE` | Custom app title | "Structured Notes Tracker" |
| `PRICE_UPDATE_DELAY` | Delay between price fetches | 0.2 |

### How to Set Variables

**Streamlit Cloud:**
- Settings → Secrets → Add as TOML format

**Railway:**
- Variables tab → Add key-value pairs

**Render:**
- Environment → Add environment variables

**Local:**
- Create `.env` file in project root

---

## 🐛 Troubleshooting

### App Won't Start

**Error: "No module named 'psycopg2'"**
- Solution: Add `psycopg2-binary` to requirements.txt
- Redeploy

**Error: "Could not connect to database"**
- Check DATABASE_URL is correct
- Ensure password is URL-encoded (no special characters)
- Test connection from Supabase dashboard

**Error: "relation 'structured_notes' does not exist"**
- Tables not created
- Run SQL setup script in Supabase SQL editor
- See Step 1.4 above

### Performance Issues

**App is slow**
- Free tiers have limited resources
- Consider upgrading to paid plan
- Optimize database queries
- Add indexes (already included in setup)

**Yahoo Finance timeouts**
- Increase `PRICE_UPDATE_DELAY` in .env
- Update fewer stocks at once

### Authentication Problems

**Forgot password**
- Update `APP_PASSWORD` in secrets/environment variables
- Restart app

**Can't login**
- Check password has no special characters causing issues
- Try a simple alphanumeric password first

### Database Issues

**Data not saving**
- Check DATABASE_URL is correct
- Verify tables exist in Supabase
- Check app logs for errors

**Want to migrate from SQLite to PostgreSQL**
- Export data using Settings → Export
- Set up PostgreSQL
- Import data manually or re-enter

---

## 🔒 Security Checklist

Before going live:

- [ ] Set `APP_PASSWORD` in production
- [ ] Use HTTPS (automatic with Streamlit Cloud/Railway/Render)
- [ ] Keep GitHub repository **private**
- [ ] Don't commit `.env` file (it's in .gitignore)
- [ ] Use strong database password
- [ ] Regularly backup your database
- [ ] Monitor access logs

---

## 📈 Scaling Considerations

### When to Upgrade

**Free Tier Limits:**
- Streamlit Cloud: Limited resources, sleeps after inactivity
- Supabase: 500MB database, 2GB bandwidth/month
- Render: Limited memory, spins down after inactivity

**Signs You Need to Upgrade:**
- More than 10 concurrent users
- Database exceeds 500MB
- App feels slow
- Need 24/7 uptime

**Recommended Paid Plans:**
- Streamlit Cloud: $20/month per app
- Supabase: $25/month (8GB database)
- Railway: $5/month + usage
- Render: $7/month per service

---

## 🆘 Getting Help

**Common Issues:**
- Check deployment logs in your platform dashboard
- Test locally first: `streamlit run app_new.py`
- Verify all environment variables are set

**Resources:**
- [Streamlit Docs](https://docs.streamlit.io)
- [Supabase Docs](https://supabase.com/docs)
- [Railway Docs](https://docs.railway.app)

---

## 🎉 Next Steps After Deployment

1. **Test Everything**
   - Add a test note
   - Update prices
   - Export data
   - Test on mobile

2. **Customize**
   - Update APP_TITLE
   - Add your logo (modify app_new.py)
   - Customize colors in .streamlit/config.toml

3. **Invite Users**
   - Share your app URL
   - Provide the APP_PASSWORD
   - Collect feedback

4. **Monitor**
   - Check app regularly
   - Monitor database size
   - Update prices periodically

5. **Iterate**
   - Add requested features
   - Fix bugs
   - Optimize performance

---

**Congratulations! Your app is now live! 🚀**

For additional support or custom features, consult with a developer or reach out to the Streamlit community.


