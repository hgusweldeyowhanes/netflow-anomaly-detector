# Quick Start: Deploy to Netlify in 5 Minutes

## What's Included

✅ **React Dashboard** - Beautiful web UI for viewing alerts  
✅ **Netlify Functions** - Serverless API layer  
✅ **Flask Backend** - Python analysis engine  
✅ **Full Integration** - Everything connected and ready to go

---

## Fastest Path to Deployment

### 1️⃣ **Prepare Local Environment** (2 min)
```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Test backend locally
python api.py
# Should say: "Starting Network Anomaly Detector API" at localhost:8000

# In another terminal, test frontend
npm start
# Should open dashboard at localhost:3000
```

### 2️⃣ **Push to GitHub** (1 min)
```bash
git add .
git commit -m "Add Netlify deployment"
git push origin main
```

### 3️⃣ **Deploy Frontend to Netlify** (1 min)
1. Go to [netlify.com](https://netlify.com)
2. Click **"New site from Git"**
3. Select your GitHub repo
4. Click **Deploy** (Netlify auto-detects React settings)
5. Your site is LIVE at `https://your-project-name.netlify.app` ✨

### 4️⃣ **Deploy Backend** (Choose ONE)

#### **Option A: Heroku (Easiest for Python)**
```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
heroku login
heroku create
git push heroku main
```
Your API is now at: `https://your-app.herokuapp.com`

#### **Option B: Railway.app (Very Simple)**
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select your GitHub repo
4. It auto-detects Python and deploys in 2 min!

#### **Option C: DigitalOcean (Most Affordable)**
1. Create account at [digitalocean.com](https://www.digitalocean.com)
2. Create "App Platform" > Connect GitHub repo
3. Set run command: `python api.py`
4. Deploy!

### 5️⃣ **Connect Frontend to Backend** (1 min)
1. In Netlify: **Site Settings → Build & Deploy → Environment**
2. Add variable:
   - Key: `PYTHON_API_URL`
   - Value: `https://your-heroku-app.herokuapp.com` (or Railway/DO URL)
3. **Redeploy** your Netlify site
4. Done! ✅

---

## Test It Works

Visit your Netlify site and:
- ✅ See the dashboard load
- ✅ Click "Upload Flow Data" to test
- ✅ View alerts and statistics

---

## Pricing

| Service | Price | Why |
|---------|-------|-----|
| Netlify | FREE | React dashboard |
| Heroku | $7/mo | Python API (Eco dyno) |
| Railway | $5/mo | Python API |
| DigitalOcean | $6/mo | Python API (basic droplet) |
| **Total** | **~$7/mo** | Full production deployment |

---

## Environment Variables Reference

Frontend (Netlify):
```
PYTHON_API_URL = https://your-backend-url.com
```

Backend (Heroku/Railway/DO):
```
FLASK_ENV = production
PORT = 8000
```

---

## Need Help?

- **Netlify Docs**: https://docs.netlify.com/
- **Heroku Docs**: https://devcenter.heroku.com/
- **Flask Docs**: https://flask.palletsprojects.com/

---

## What's Next?

After deployment, you can:
- 📊 Upload real network flow data
- 📧 Add email alerts
- 🔐 Add authentication
- 📱 Build mobile app
- 📈 Add more visualizations

See [DEPLOYMENT.md](./DEPLOYMENT.md) for advanced configuration.
