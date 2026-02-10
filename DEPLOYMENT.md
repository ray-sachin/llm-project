# LLM Deployment Platform - Deployment Guide

A complete guide for deploying the LLM Deployment Platform with Supabase backend, multi-user authentication, and GitHub integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Setup](#manual-setup)
4. [Configuration](#configuration)
5. [Supabase Setup](#supabase-setup)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- **Supabase** - Backend database (free tier available)
- **GitHub** - For repository creation and GitHub Pages hosting
- **AIPIPE** - LLM provider for code generation (free tier available at https://aipipe.org)

### Local Development
- **Docker & Docker Compose** (recommended) OR
- **Python 3.11+** and **Node.js 18+**

---

## Quick Start (Docker)

### Option 1: Using Docker Compose (Recommended)

1. **Clone and navigate to project:**
   ```bash
   git clone <repository-url>
   cd llm-deployment-platform
   ```

2. **Create `.env` file with your credentials:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add:
   ```env
   # Supabase credentials (required)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   SUPABASE_SERVICE_KEY=your_service_key_here

   # Frontend URL
   FRONTEND_URL=http://localhost:3000

   # Optional: GitHub & AIPIPE tokens
   # Leave empty for per-user configuration
   GITHUB_TOKEN=
   AIPIPE_TOKEN=
   USERCODE=
   ```

3. **Build and run:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: Serve from your domain with reverse proxy

---

## Manual Setup

### Option 2: Local Development (Python + Node)

### Backend Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r app/requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Start backend:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Create `.env` file:**
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access frontend:**
   - http://localhost:5173 (or port displayed by Vite)

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key |
| `FRONTEND_URL` | ✅ | Frontend URL (for CORS) |
| `GITHUB_TOKEN` | ❌ | GitHub PAT for team repo creation |
| `AIPIPE_TOKEN` | ❌ | AIPIPE API token |
| `USERCODE` | ❌ | GitHub username (if using team token) |
| `SECRET` | ❌ | Secret for signing (auto-generated) |

### Per-User Configuration

For multi-user deployments:
1. Leave `GITHUB_TOKEN` and `AIPIPE_TOKEN` empty
2. Users configure their own credentials via Settings page:
   - GitHub Personal Access Token (required scopes: Administration, Contents, Pages)
   - AIPIPE API token (get from https://aipipe.org/login)

---

## Supabase Setup

### Create Supabase Project

1. Go to https://supabase.com and sign up
2. Create a new project in your organization
3. Wait for project to initialize (2-3 minutes)

### Get Credentials

1. Go to **Settings > API** to find:
   - **Project URL**: `https://your-project.supabase.co`
   - **Anon Key**: (public key)
   - **Service Role Key**: (secret key - keep safe)

2. Copy these into your `.env` file

### Database Schema

The database schema is automatically created on first backend startup. It includes:

**Tables:**
- `users` - User profiles
- `github_tokens` - Encrypted GitHub PATs per user
- `projects` - Project records with deployment status
- `project_history` - Audit trail of all project actions

**Security:**
- Row Level Security (RLS) enabled on all tables
- Users can only access their own data
- Service key used for admin operations only

---

## Production Deployment

### Using Docker (AWS ECS, Google Cloud Run, Heroku, etc.)

1. **Build Docker image:**
   ```bash
   docker build -t llm-platform:latest .
   ```

2. **Push to registry (e.g., Docker Hub):**
   ```bash
   docker tag llm-platform:latest your-registry/llm-platform:latest
   docker push your-registry/llm-platform:latest
   ```

3. **Deploy container** with your cloud provider
   - Set all environment variables
   - Expose port 8000
   - Enable HTTPS

### Using Vercel/Netlify (Frontend Only)

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy `frontend/dist` folder:**
   - Vercel: Connect GitHub repo → Auto-deploy
   - Netlify: Connect GitHub repo → Auto-deploy

3. **Set environment variables:**
   - `VITE_API_URL=https://your-api-domain.com`

### Production Checklist

- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Database backups enabled
- [ ] Environment variables secured
- [ ] Rate limiting configured
- [ ] Error logging enabled
- [ ] Monitoring/alerting setup
- [ ] Custom domain configured

---

## Troubleshooting

### Backend Issues

**Backend won't start:**
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process and retry
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Supabase connection error:**
- Verify `SUPABASE_URL` format: `https://project-id.supabase.co`
- Check that keys are correct (not truncated)
- Ensure Supabase project is active

**Auth errors:**
- Check that database schema exists (check Supabase SQL editor)
- Verify RLS policies are enabled
- Clear browser localStorage and try again

### Frontend Issues

**Frontend can't connect to backend:**
- Check `VITE_API_URL` in `.env`
- Verify backend is running on correct port
- Check browser console for CORS errors

**Login page not loading:**
- Clear browser cache (Ctrl+Shift+Delete)
- Check that frontend built correctly (`npm run build`)
- Verify TypeScript compilation: `npm run type-check`

**GitHub token errors:**
- Ensure token has correct scopes: Administration, Contents, Pages
- Token must be a Personal Access Token (PAT), not OAuth token
- Check token expiration date

### Docker Issues

**Image build fails:**
```bash
# Clear Docker cache
docker system prune

# Rebuild without cache
docker build --no-cache -t llm-platform:latest .
```

**Container exits immediately:**
```bash
# Check logs
docker logs llm-deployment-platform

# Run container with interactive shell for debugging
docker run -it llm-platform:latest bash
```

---

## Support & Resources

- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **GitHub Pages**: https://pages.github.com/
- **Docker Docs**: https://docs.docker.com/

---

## Performance Tips

1. **Use CDN** for frontend assets (Cloudflare, AWS CloudFront)
2. **Enable Supabase caching** for read-heavy operations
3. **Set up automatic backups** in Supabase
4. **Monitor API usage** on AIPIPE
5. **Use regional deployment** for lower latency

---

## Security Notes

- Never commit `.env` files with real credentials
- Use secret management (AWS Secrets Manager, HashiCorp Vault)
- Rotate GitHub Personal Access Tokens periodically
- Enable MFA on Supabase and GitHub accounts
- Monitor logs for suspicious activity
- Keep dependencies updated (`pip list --outdated`, `npm outdated`)

---

**Last Updated:** February 2026
