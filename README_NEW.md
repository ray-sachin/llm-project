# 🚀 LLM Deploy - AI-Powered Web App Generation

> **Automatically generate, deploy, and host web applications using AI**

A full-stack platform that leverages Large Language Models (LLMs) to create complete web applications from natural language descriptions.

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Built with](https://img.shields.io/badge/Built%20with-React%20%7C%20FastAPI%20%7C%20OpenAI-blueviolet)

## ✨ Features

### 🎨 **AI-Powered Generation**
- Describe your web app in plain English
- AI generates complete HTML, CSS, and JavaScript
- Support for custom requirements and design specifications
- Reference images and documents for inspiration

### 🚀 **Automatic Deployment**
- Generated code automatically pushed to GitHub
- GitHub Pages hosting enabled instantly
- Live URLs ready in minutes
- Version history maintained in Git

### 📱 **Modern UI**
- Beautiful, responsive frontend interface
- Real-time project status tracking
- Glassmorphism design with smooth animations
- Mobile-friendly dashboard

### 🔄 **Iterative Development**
- Support for project updates (multiple rounds)
- Previous code context for refinements
- Continuous improvement workflow

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                   │
│         http://localhost:5173                        │
├─────────────────────────────────────────────────────┤
│                  REST API (FastAPI)                  │
│         http://localhost:8000                        │
├─────────────────────────────────────────────────────┤
│  OpenAI API (GPT)  │  GitHub API  │  Storage         │
└─────────────────────────────────────────────────────┘
                          ↓
              Generated Web Apps on GitHub Pages
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API Key
- GitHub Personal Access Token

### Option 1: Automated Setup (Windows)

**PowerShell:**
```powershell
./setup.ps1
```

**Command Prompt:**
```cmd
setup.bat
```

### Option 2: Manual Setup

#### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
# Create .env file with:
# SECRET=your_secret
# USERCODE=your_github_username
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...

# Start backend
python -m app.main
```

Backend will run on: `http://localhost:8000`

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on: `http://localhost:5173`

## 📖 Usage

### Creating a Project

1. **Open the App**
   - Navigate to http://localhost:5173
   - Click "New Project"

2. **Write a Brief**
   ```
   Example: "Create a portfolio website for a software engineer. 
   Include a header with navigation, hero section, projects showcase 
   with cards, about section, and a contact form. Use modern design 
   with dark theme and smooth animations."
   ```

3. **Add Requirements** (Optional)
   ```
   - Mobile responsive
   - Dark mode support
   - Smooth animations
   - Fast loading
   ```

4. **Upload References** (Optional)
   - Design mockups
   - Brand guidelines
   - Inspiration images

5. **Submit**
   - AI generates the code
   - Pushed to GitHub
   - Live on GitHub Pages
   - Status displays in dashboard

### Viewing Results

Each project shows:
- **Status**: Processing → Completed
- **Live Link**: Direct to GitHub Pages
- **GitHub Repo**: Source code repository
- **Error Details**: If generation fails

## 📁 Project Structure

```
llm-project/
├── app/                          # Backend (FastAPI)
│   ├── main.py                  # Main API server
│   ├── llm_generator.py         # LLM code generation
│   ├── github_utils.py          # GitHub integration
│   ├── notify.py                # Notifications
│   └── signature.py             # Digital signatures
│
├── frontend/                     # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── api.ts              # API client
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── Layout.tsx          # Layout wrapper
│   │   └── App.tsx             # Router setup
│   ├── package.json
│   ├── vite.config.ts
│   └── README_FRONTEND.md       # Frontend documentation
│
├── requirements.txt             # Python dependencies
├── SETUP_GUIDE.md              # Detailed setup guide
├── FRONTEND_README.md          # Frontend feature overview
├── setup.bat / setup.ps1       # Quick start scripts
└── LICENCE                     # MIT License
```

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **OpenAI API** - GPT for code generation
- **PyGithub** - GitHub API interaction
- **Python 3.8+** - Runtime

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide Icons** - Icon library

### Deployment
- **GitHub** - Source control & Pages hosting
- **Vercel / Netlify** - Frontend hosting
- **Heroku / Railway** - Backend hosting

## 📚 Documentation

- [Full Setup Guide](./SETUP_GUIDE.md) - Detailed installation & configuration
- [Frontend Documentation](./FRONTEND_README.md) - UI features & customization
- [Frontend README](./frontend/README_FRONTEND.md) - Development guide
- [Original Project README](./README.md) - Backend architecture

## 🔐 Environment Variables

### Backend (`.env`)
```env
SECRET=your_secret_key              # For authentication
USERCODE=your_github_username       # GitHub user
OPENAI_API_KEY=sk-...               # OpenAI API key
GITHUB_TOKEN=ghp_...                # GitHub Personal Access Token
```

### Frontend (`.env.local`)
```env
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## 🌐 API Endpoints

### Create Project
```http
POST /deploy
Content-Type: multipart/form-data

form data:
  - brief: string (required)
  - checks: string (comma-separated, optional)
  - attachments: file[] (optional)

Response: { task_id: string }
```

### Get Projects
```http
GET /projects
Response: { projects: Project[] }
```

### Get Project Status
```http
GET /status/{taskId}
Response: { status, githubUrl, pagesUrl }
```

### Health Check
```http
GET /health
Response: { status: "ok" }
```

## 🚀 Deployment

### Backend Deployment

**Heroku:**
```bash
heroku create your-app
git push heroku main
heroku config:set OPENAI_API_KEY=sk-...
```

**Railway:**
1. Connect GitHub repo
2. Set environment variables
3. Auto-deploys on push

**PythonAnywhere:**
1. Upload code
2. Configure WSGI
3. Set env variables

### Frontend Deployment

**Vercel (Recommended):**
```bash
npm install -g vercel
vercel
```

**Netlify:**
```bash
npm run build
netlify deploy --prod --dir=dist
```

**GitHub Pages:**
1. Set `base` in `vite.config.ts`
2. Build: `npm run build`
3. Deploy `dist` folder

## 🔄 Project Workflow

```
1. User Input
   ↓
2. Submit Brief & Files
   ↓
3. API Receives Request
   ↓
4. LLM Generates Code
   ↓
5. Create GitHub Repository
   ↓
6. Commit Generated Files
   ↓
7. Enable GitHub Pages
   ↓
8. Update Status
   ↓
9. Display Live URL
   ↓
10. User Sees Result
```

## 🎨 Customization

### Change Colors
Edit `frontend/src/Layout.css`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Modify LLM Prompts
Edit `app/llm_generator.py`:
```python
# Update system prompts for different code styles
```

### Add New Routes
1. Create page in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add API method in `frontend/src/api.ts`

## 🐛 Troubleshooting

### "CORS Error"
Add CORS middleware to FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### "Port Already in Use"
Change port in backend or frontend config

### "OpenAI API Error"
- Verify API key is valid
- Check rate limits
- Ensure account has credits

### "GitHub Integration Failed"
- Verify token has repo permissions
- Check token is not expired
- Verify username is correct

## 📊 Monitoring

### Backend Logs
Check FastAPI console output for:
- Request logs
- LLM generation status
- GitHub operations
- Errors and exceptions

### Frontend Logs
Open browser DevTools (F12) for:
- API call logs
- Component errors
- Network requests
- State debugging

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push and create PR

## 📄 License

MIT License - See [LICENCE](./LICENCE) file

## 🙋 Support

- **Issues**: Open GitHub issue
- **Docs**: Check documentation files
- **Questions**: Review README files

## 🎯 Roadmap

- [ ] User authentication
- [ ] Project sharing
- [ ] Advanced settings page
- [ ] Project editing/updates
- [ ] WebSocket real-time updates
- [ ] Database for persistence
- [ ] Admin dashboard
- [ ] Analytics tracking
- [ ] Rate limiting
- [ ] Subscription tiers

## 📞 Contact

For questions, suggestions, or issues:
- Check existing issues
- Open a new issue
- Review documentation

---

**Built with ❤️ for developers who want to build fast**

**Version**: 1.0.0  
**Last Updated**: February 9, 2026  
**Status**: ✅ Production Ready
