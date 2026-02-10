# Quick Setup Guide

Get the LLM Deployment Platform up and running in 5 minutes.

## 🎯 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional, but recommended)
- Supabase account (free)
- GitHub account

## 📋 Step 1: Get Supabase Credentials (3 minutes)

1. Go to https://supabase.com and sign up
2. Create a new project
3. Wait for project to initialize
4. Go to **Settings > API**
5. Copy these three values:
   - `Project URL` → `SUPABASE_URL`
   - `Anon Key` → `SUPABASE_ANON_KEY`
   - `Service Role Key` → `SUPABASE_SERVICE_KEY`

## 🚀 Step 2: Using Docker (Recommended - 2 minutes)

```bash
# Clone project
git clone <repo-url>
cd llm-deployment-platform

# Create .env file
cp .env.example .env

# Edit .env and paste Supabase credentials
# Then set FRONTEND_URL=http://localhost:3000

# Start everything
docker-compose up --build

# Done! Backend running on http://localhost:8000
```

## 🛠️ Step 3: Manual Setup (Alternative - 2 minutes)

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with Supabase credentials

# Start backend
python -m uvicorn app.main:app --reload
```

### Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

## ✅ Verify Installation

- **Backend**: http://localhost:8000/health
  - Should return: `{"status":"ok","message":"Backend is running"}`
- **Frontend**: http://localhost:5173
  - Should show login page
- **API Docs**: http://localhost:8000/docs
  - Interactive API documentation

## 📝 First Time Setup

1. **Sign Up**
   - Go to http://localhost:5173/signup
   - Create account

2. **Configure GitHub**
   - Go to Settings
   - Create [GitHub PAT](https://github.com/settings/tokens?type=pat)
   - Required scopes: Administration, Contents, Pages
   - Paste token in Settings

3. **Create Project**
   - Click "New Project"
   - Describe your app
   - Click "Create"
   - Done! Platform generates and deploys

## 🆘 Troubleshooting

### Port already in use
```bash
# Kill process using port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### pip install fails
```bash
# Update pip
pip install --upgrade pip

# Try install again
pip install -r requirements.txt
```

### Node modules issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Git issues
```bash
# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

## 📚 Next Steps

- Read [README.md](README.md) for features overview
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Check [API documentation](http://localhost:8000/docs) when running

## 💡 Tips

- **Hot reload**: Code changes auto-reload in development
- **Browser DevTools**: Open DevTools to see API requests
- **API Explorer**: Use `/docs` endpoint to test API
- **Database**: View data in Supabase dashboard

---

**Done!** You now have a working multi-user LLM deployment platform.
