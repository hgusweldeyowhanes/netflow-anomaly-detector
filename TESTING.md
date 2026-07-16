# Testing Guide: Dashboard Functionality

## ✅ Quick Health Check (2 minutes)

### Test 1: Backend is Running
```bash
# Test API is responding
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2026-07-16T10:30:45.123456"}
```

### Test 2: Frontend is Running
```bash
# Should open http://localhost:3000 automatically
npm start

# ✅ You should see:
# - Purple gradient header with "🔍 Network Anomaly Detection"
# - Upload button and Refresh button
# - Statistics panel with 4 cards (Total Flows, Unique Sources, Anomalies, Beacons)
# - Alerts panel on the right
# - Network Flow visualization at the bottom
```

### Test 3: Dashboard Loads
1. Open browser to `http://localhost:3000`
2. Wait 3 seconds for data to load
3. You should see:
   - ✅ Header displays
   - ✅ Statistics showing numbers (Total Flows, etc.)
   - ✅ Alerts panel (showing mock data if no alerts)
   - ✅ No console errors (open DevTools: F12)

---

## 🔧 Detailed Testing

### Test Backend API Endpoints

Open **PowerShell** and run these commands:

#### 1. Health Check
```powershell
curl.exe -X GET http://localhost:8000/api/health

# Expected: {"status":"healthy","timestamp":"..."}
```

#### 2. Get Alerts
```powershell
curl.exe -X GET http://localhost:8000/api/alerts

# Expected: JSON with "alerts" array and "stats" object
```

#### 3. Get Configuration
```powershell
curl.exe -X GET http://localhost:8000/api/config

# Expected: Your config.yaml data as JSON
```

---

### Test Frontend Components

#### 1. Open Browser DevTools (F12)
Go to **Console** tab and check for:
- ✅ No red errors
- ✅ No CORS errors about "Cannot reach API"
- ✅ Messages like "Fetching data..."

#### 2. Check Each Component

**Statistics Panel:**
- [ ] Shows 4 cards with icons
- [ ] Numbers display correctly
- [ ] "Last updated" time shows at bottom

**Alerts Panel:**
- [ ] Shows "No alerts detected" if none exist (normal!)
- [ ] If alerts exist, shows IP addresses, risk scores, timestamps
- [ ] Risk score colors: Red (85+), Orange (70-84), Yellow (50-69), Green (<50)

**Upload Button:**
- [ ] Click "📁 Upload Flow Data (CSV)"
- [ ] File picker opens
- [ ] Can select a CSV file

**Refresh Button:**
- [ ] Click "🔄 Refresh"
- [ ] Button shows "Loading..."
- [ ] Data updates

**Flow Visualization:**
- [ ] SVG diagram displays
- [ ] Shows source nodes (S1, S2, S3) and destinations (D1, D2, D3)
- [ ] Has blue and orange lines

---

## 🧪 Integration Testing

### Test Full Flow: Upload Data → Analyze → View Alerts

#### Step 1: Prepare Test Data
```bash
# Your sample data exists at:
# c:\Users\HP\Pictures\HgProject\netflow-anomaly-detector\data\flows.csv

# Or generate test data:
python -c "from src.data_generator import generate_dataset; generate_dataset('test_flows.csv')"
```

#### Step 2: Upload via Dashboard
1. Open dashboard at `http://localhost:3000`
2. Click **"📁 Upload Flow Data (CSV)"**
3. Select your CSV file
4. See **"✅ File uploaded and analyzed successfully!"** message
5. Statistics should update with real data

#### Step 3: Verify Results
- [ ] Alerts panel updates
- [ ] Statistics show actual flow counts
- [ ] No error messages

---

## 🚨 Common Issues & Fixes

### Issue: "Cannot connect to server" or CORS error in console

**Check:**
```bash
# Is backend running?
curl http://localhost:8000/api/health

# If NO response: Backend isn't running
# Fix: Open new terminal and run:
python api.py

# If YES response but still CORS error:
# Frontend is looking at wrong URL. Check:
# 1. npm start is using http://localhost:3000
# 2. api.py is using http://localhost:8000
# 3. No firewall blocking port 8000
```

### Issue: Statistics show "undefined" or "0"

**Check:**
```bash
# Get sample alerts:
curl http://localhost:8000/api/alerts | python -m json.tool

# Should show JSON with data. If empty:
# 1. Check if flows.csv exists at: data/flows.csv
# 2. If missing, backend will auto-generate demo data
# 3. Wait 10 seconds and refresh dashboard
```

### Issue: Upload button doesn't work

**Check:**
```bash
# Test upload endpoint directly:
curl -X POST http://localhost:8000/api/analyze `
  -F "file=@test_flows.csv"

# Should succeed. If not, check error message
```

### Issue: Dashboard is blank or shows errors

**Open DevTools (F12) and check:**
- Go to **Console** tab
- Look for red errors
- Check **Network** tab to see if API calls are successful

---

## 📊 Verification Checklist

- [ ] Backend starts without errors: `python api.py`
- [ ] Frontend starts: `npm start`
- [ ] Dashboard loads at http://localhost:3000
- [ ] Header displays correctly
- [ ] Statistics panel shows numbers
- [ ] Alerts panel displays (even if empty)
- [ ] Refresh button works
- [ ] Upload button responds
- [ ] No console errors (F12)
- [ ] No CORS errors
- [ ] API responds to: `/api/health`, `/api/alerts`, `/api/config`

---

## 🌐 Testing on Netlify (Production)

### After deploying to Netlify:

1. **Test Frontend**
   ```bash
   # Visit your Netlify URL
   https://your-project.netlify.app
   
   # Check:
   # - Page loads
   # - No 404 errors
   # - Dashboard displays
   ```

2. **Check Netlify Functions**
   ```powershell
   # Test the function endpoint
   curl https://your-project.netlify.app/.netlify/functions/get-alerts
   
   # Should return mock alerts (if backend not connected yet)
   ```

3. **Check Network Requests**
   - Open DevTools (F12)
   - Go to **Network** tab
   - Click Refresh button on dashboard
   - Should see requests to:
     - `/.netlify/functions/get-alerts` (200 OK)
     - Or `https://your-backend-api.com/api/alerts` (200 OK)

4. **Verify Backend Connection**
   - Update `PYTHON_API_URL` in Netlify environment variables
   - Redeploy site
   - Real data should appear (not mock data)

---

## 📝 Debugging Tips

### Enable debug logging in Flask:

Edit `api.py` and change:
```python
if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Set debug=True
```

Then check terminal output when making requests.

### Check browser console logs:

In DevTools Console, you'll see:
```javascript
// Successful request
Fetching alerts from http://localhost:8000/api/alerts
// Response received
```

### Monitor API calls in real-time:

```bash
# In one terminal:
python api.py

# In another:
# Open DevTools and watch Console/Network tabs
# Make requests and see real-time logs
```

---

## ✅ Success Indicators

You'll know everything is working when you see:

1. **Dashboard loads without errors** ✅
2. **Statistics show real numbers** ✅
3. **Can upload CSV files** ✅
4. **Alerts display when anomalies detected** ✅
5. **Refresh button updates data** ✅
6. **No red errors in console** ✅
7. **No CORS errors** ✅

---

## 🆘 Still Having Issues?

Run this diagnostic script:

```bash
# Check all components
echo "=== BACKEND ==="
curl http://localhost:8000/api/health

echo "=== FRONTEND ==="
curl http://localhost:3000

echo "=== CHECK FLOWS DATA ==="
dir data\flows.csv

echo "=== CHECK PYTHON ==="
python --version

echo "=== CHECK NODE ==="
npm --version
```

Share the output if you need help!
