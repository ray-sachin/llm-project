# LLM Deploy - Frontend

A modern React + TypeScript frontend for the LLM-powered web application generator and deployment platform.

## 🎨 Features

- **Modern UI**: Built with React 19 and Vite for lightning-fast development
- **Project Dashboard**: View all your generated projects with real-time status updates
- **Create Projects**: Submit project briefs with optional attachments and requirements
- **GitHub Integration**: Direct links to live GitHub Pages deployments
- **Responsive Design**: Beautiful gradient UI that works on all devices
- **Real-time Updates**: Auto-refreshing project status

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file (copy from `.env.example`):
```bash
cp .env.example .env.local
```

4. Update `.env.local` with your backend URL:
```
VITE_API_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173/`

### Building for Production

Build the optimized production bundle:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api.ts                 # API client and endpoints
│   ├── types.ts               # TypeScript type definitions
│   ├── Layout.tsx             # Main layout component
│   ├── Layout.css             # Layout styles
│   ├── pages/
│   │   ├── Dashboard.tsx       # Projects dashboard
│   │   ├── Dashboard.css
│   │   ├── CreateProject.tsx   # Project creation form
│   │   └── CreateProject.css
│   ├── App.tsx                # Main app component
│   ├── App.css
│   ├── index.css              # Global styles
│   └── main.tsx               # Entry point
├── public/                    # Static assets
├── .env.example              # Environment variables template
├── package.json
├── tsconfig.json
├── vite.config.ts            # Vite configuration
└── index.html                # HTML entry point
```

## 🎯 Key Components

### Dashboard
- Displays all user projects with status badges
- Shows project briefs and creation dates
- Provides quick links to live deployments and GitHub repos
- Real-time status polling with 5-second intervals

### CreateProject Form
- Rich form for submitting new projects
- Project brief textarea with character count
- Optional requirements/checks input
- File upload support for attachments
- Form validation and error handling
- Success notifications with redirect

### API Integration
- Axios-based HTTP client
- Endpoints for project submission, retrieval, and status
- Error handling and response management
- Support for file uploads

## 🔧 Configuration

### Environment Variables

- `VITE_API_URL`: Backend API base URL (default: `http://localhost:8000`)

### Styling

The frontend uses a modern gradient design with:
- Primary colors: Purple to violet gradient (`#667eea` to `#764ba2`)
- Glassmorphism effects with backdrop blur
- Responsive grid layouts
- Smooth animations and transitions

## 📦 Dependencies

- **react**: ^19.2.0 - UI framework
- **react-dom**: ^19.2.0 - React DOM rendering
- **react-router-dom**: ^7.0.0 - Client-side routing
- **axios**: ^1.7.0 - HTTP client
- **lucide-react**: ^0.408.0 - Icon library

### Development Dependencies

- **vite**: ^7.3.1 - Build tool
- **typescript**: ~5.9.3 - Type safety
- **eslint**: ^9.39.1 - Code linting

## 🚀 Deployment

### Deploy to Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Deploy to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Deploy to GitHub Pages
1. Add to `vite.config.ts`:
```typescript
export default {
  base: '/repository-name/',
}
```

2. Build and deploy:
```bash
npm run build
# Deploy the dist folder
```

## 🔗 API Integration

The frontend expects the backend to provide these endpoints:

- `POST /deploy` - Submit new project
- `GET /projects` - Get all projects
- `GET /projects/{id}` - Get project details
- `GET /status/{taskId}` - Get project status
- `GET /health` - Health check

## 🎨 Customization

### Colors
Update the gradient in Layout.css and index.css:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Typography
Modify font family in index.css:
```css
font-family: 'Your Font', sans-serif;
```

### Layout
Adjust spacing and max-width in Layout.css:
```css
max-width: 1400px; /* Change container width */
padding: 3rem 2rem;  /* Change padding */
```

## 🐛 Troubleshooting

### CORS Issues
Make sure backend has CORS enabled:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Connection Issues
1. Check that backend is running on the correct port
2. Verify `VITE_API_URL` in `.env.local`
3. Check browser console for errors
4. Ensure CORS headers are configured

### Build Issues
1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf dist && npm run build`
3. Check TypeScript errors: `tsc --noEmit`

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

For issues and questions, please open an issue on GitHub.
