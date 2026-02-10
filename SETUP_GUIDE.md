# LLM Deploy - Full Stack Setup Guide

This project consists of:
- **Backend**: FastAPI server that generates web applications using LLM
- **Frontend**: React + TypeScript UI for submitting projects and viewing deployments

## 🚀 Quick Start

### Option 1: Run Both Locally (Recommended for Development)

#### Terminal 1 - Backend
```bash
cd llm-project
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m app.main
```

Backend will run on `http://localhost:8000`

#### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:5173`

### Option 2: Docker Setup (Coming Soon)

Create a `docker-compose.yml` in the project root to run both services.

## 📋 Project Structure

```
llm-project/
├── app/                          # Backend (FastAPI)
│   ├── main.py                  # FastAPI application
│   ├── llm_generator.py         # LLM code generation logic
│   ├── github_utils.py          # GitHub integration
│   ├── notify.py                # Notification module
│   ├── signature.py             # Digital signatures
│   └── __init__.py
├── frontend/                     # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── CreateProject.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   ├── Layout.tsx
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
├── requirements.txt              # Python dependencies
├── LICENCE                       # License file
└── README.md                     # This file
```

## 🔐 Environment Setup

### Backend Configuration

Create a `.env` file in the project root (for the app):

```env
SECRET=your_secret_key_here
USERCODE=your_github_username
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token
```

### Frontend Configuration

Create `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /deploy` - Submit a new project
  - Request body: Form data with brief, checks, and attachments
  - Response: `{ task_id: string }`

- `GET /projects` - Get all projects (currently returns empty, needs backend implementation)

- `GET /status/{taskId}` - Get project status

- `GET /health` - Health check

## 🎯 Development Workflow

1. **Backend Development**
   - Modify `app/main.py` for API changes
   - Update `app/llm_generator.py` for LLM generation logic
   - Update GitHub integration in `app/github_utils.py`

2. **Frontend Development**
   - Add new pages in `frontend/src/pages/`
   - Update API calls in `frontend/src/api.ts`
   - Modify types in `frontend/src/types.ts`
   - Update styles in component `.css` files

3. **Testing**
   - Backend: Use FastAPI Swagger UI at `/docs`
   - Frontend: Use browser DevTools and Vite HMR

## 🔄 Integration Flow

```
User Input (Frontend)
    ↓
Submit Project Request
    ↓
Backend API Endpoint
    ↓
LLM Generates Code (OpenAI)
    ↓
GitHub Repository Created
    ↓
GitHub Pages Enabled
    ↓
Project Status Updated
    ↓
Frontend Dashboard Refreshed
    ↓
Live Deployment Link Ready
```

## 🚀 Deployment

### Deploy Frontend

**Vercel** (Recommended):
```bash
cd frontend
npm install -g vercel
vercel
```

**Netlify**:
```bash
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

**GitHub Pages**:
```bash
cd frontend
npm run build
# Deploy dist folder
```

### Deploy Backend

**Heroku**:
```bash
heroku create your-app-name
git push heroku main
```

**PythonAnywhere**:
1. Upload code
2. Configure WSGI file
3. Set environment variables

**Railway**:
1. Connect GitHub repo
2. Set environment variables
3. Deploy

## 🔗 CORS Configuration

The backend must have CORS enabled for the frontend to work:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing

### Backend Testing
```bash
# Run with test data
python -m pytest app/
```

### Frontend Testing
```bash
cd frontend
npm run lint
```

## 📊 Monitoring

- **Backend Logs**: Check terminal output or use logging module
- **Frontend Logs**: Open browser DevTools console
- **GitHub**: Check repository for created deployments

## 🐛 Troubleshooting

### Backend Won't Start
1. Check Python version: `python --version` (requires 3.8+)
2. Verify dependencies: `pip install -r requirements.txt`
3. Check environment variables are set
4. Port 8000 may be in use: Change in `main.py`

### Frontend Won't Connect to Backend
1. Ensure backend is running
2. Check `VITE_API_URL` in `.env.local`
3. Check CORS headers in browser DevTools
4. Verify firewall/network settings

### LLM Generation Fails
1. Verify OpenAI API key is valid
2. Check API rate limits
3. Review OpenAI account balance
4. Check request format in `llm_generator.py`

### GitHub Integration Issues
1. Verify GitHub token has repo creation permissions
2. Check username in `USERCODE` env variable
3. Ensure PAT (Personal Access Token) is not expired

## 📞 Support & Contributing

For issues, questions, or contributions:
1. Check existing issues
2. Create a new issue with details
3. Submit pull requests for improvements

## 📄 License

MIT License - See LICENCE file for details

---

**Last Updated**: 2026-02-09
**Version**: 1.0.0
