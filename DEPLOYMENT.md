# Deployment Guide: Network Anomaly Detector on Netlify

## Overview
This guide helps you deploy the Network Anomaly Detector with:
- **Frontend**: React dashboard (deployed on Netlify)
- **Backend**: Python Flask API (deployed separately)
- **Connection**: Netlify Functions → Flask API → Analysis Engine

## Step 1: Deploy the Frontend on Netlify

### Prerequisites
- GitHub account
- Netlify account (free tier available)
- Node.js installed locally

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: network anomaly detector"
   git remote add origin https://github.com/YOUR_USERNAME/netflow-anomaly-detector.git
   git branch -M main
   git push -u origin main
   ```

2. **Connect to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Click "New site from Git"
   - Select GitHub and authorize
   - Choose your repository
   - Set build command: `npm run build`
   - Set publish directory: `build`
   - Click "Deploy"

3. **Set Environment Variables in Netlify**
   - Go to Site Settings → Environment
   - Add variable: `PYTHON_API_URL` = `https://your-python-api.com`
   - (We'll set this after deploying the backend)

---

## Step 2: Deploy the Python Backend

### Option A: Deploy on Heroku (Recommended for Python)

1. **Create Heroku Account**
   - Sign up at [heroku.com](https://heroku.com)

2. **Install Heroku CLI**
   ```bash
   # Windows
   choco install heroku-cli
   
   # macOS
   brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create netflow-anomaly-detector
   git push heroku main
   ```

4. **Test the API**
   ```bash
   curl https://netflow-anomaly-detector.herokuapp.com/api/health
   ```

5. **Update Netlify Environment Variable**
   - In Netlify: `PYTHON_API_URL` = `https://netflow-anomaly-detector.herokuapp.com`

---

### Option B: Deploy on AWS Lambda + API Gateway

1. **Install AWS CLI**
   ```bash
   pip install awscli
   aws configure
   ```

2. **Use AWS SAM (Serverless Application Model)**
   ```bash
   pip install aws-sam-cli
   sam init
   sam build
   sam deploy --guided
   ```

3. **Update Netlify with your API Gateway URL**

---

### Option C: Deploy on DigitalOcean App Platform

1. **Create DigitalOcean Account** and create an App
2. **Connect your GitHub repo**
3. **Set build command**: `pip install -r requirements.txt`
4. **Set run command**: `python api.py`
5. **Add environment variables** as needed

---

## Step 3: Set Up CORS and Security

### Update Flask API (for production)
```python
# In api.py
app.config['CORS_ORIGINS'] = ['https://your-netlify-site.netlify.app']
```

---

## Step 4: Test the Full Integration

### Test Frontend
```bash
npm start
```

### Test Backend Locally
```bash
python api.py
# API will run at http://localhost:8000
```

### Test Netlify Functions Locally
```bash
npm install -g netlify-cli
netlify dev
# Netlify CLI will simulate functions at http://localhost:8888
```

---

## Step 5: Monitor & Logs

### Netlify Logs
- Dashboard → Deploys → Click latest deploy → Logs

### Python Backend Logs
- Heroku: `heroku logs --tail`
- AWS: CloudWatch Logs in AWS Console
- DigitalOcean: App Platform → Logs

---

## File Structure
```
netflow-anomaly-detector/
├── package.json              # Node/React dependencies
├── netlify.toml             # Netlify config
├── api.py                   # Flask API server
├── requirements.txt         # Python dependencies
├── public/
│   └── index.html
├── src/
│   ├── index.js
│   ├── App.js
│   ├── App.css
│   ├── components/          # React components
│   ├── alerting.py
│   ├── beacon_detector.py
│   ├── data_generator.py
│   ├── feature_extraction.py
│   └── model.py
├── netlify/
│   └── functions/           # Serverless functions
│       ├── get-alerts.js
│       └── analyze-flows.js
└── data/                    # Flow data
    └── flows.csv
```

---

## Troubleshooting

### "CORS Error" or "Cannot reach API"
1. Check that `PYTHON_API_URL` is set correctly in Netlify
2. Verify Python API is running: `curl {PYTHON_API_URL}/api/health`
3. Check Flask CORS is enabled

### "No alerts showing"
1. Check Python API logs for errors
2. Make sure `data/flows.csv` exists or demo data is generated
3. Verify model can load from requirements

### Functions returning 500 error
1. Check Netlify Functions logs: Netlify Dashboard → Functions → Logs
2. Verify axios dependency: `npm install axios` in package.json
3. Check timeout settings if large files are uploaded

---

## Optional: Custom Domain

1. Buy domain from GoDaddy, Namecheap, etc.
2. In Netlify: Site Settings → Domain Management → Add custom domain
3. Follow DNS configuration instructions

---

## Cost Estimates

- **Netlify**: Free (React dashboard)
- **Heroku**: $7/month (hobby dyno for Python API)
- **Total**: ~$7/month for full deployment

---

## Next Steps

1. ✅ Deploy frontend on Netlify
2. ✅ Deploy backend on Heroku/AWS/DigitalOcean
3. ✅ Configure environment variables
4. ✅ Test full integration
5. ✅ Set up monitoring/alerts
6. ✅ Create custom domain (optional)

Need help? Check the Netlify docs: https://docs.netlify.com/
