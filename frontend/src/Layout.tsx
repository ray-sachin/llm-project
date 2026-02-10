import React from 'react';
import { Link, useNavigate, Outlet } from 'react-router-dom';
import { Zap, Plus, Home, History, Settings, LogOut } from 'lucide-react';
import './Layout.css';

export const Layout: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    navigate('/login');
  };

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-container">
          <Link to="/" className="nav-brand">
            <Zap size={24} />
            <span>LLM Deploy</span>
          </Link>
          <div className="nav-links">
            <Link to="/" className="nav-link">
              <Home size={18} />
              <span>Dashboard</span>
            </Link>
            <Link to="/history" className="nav-link">
              <History size={18} />
              <span>History</span>
            </Link>
            <Link to="/settings" className="nav-link">
              <Settings size={18} />
              <span>Settings</span>
            </Link>
            <Link to="/create" className="nav-link nav-link-primary">
              <Plus size={18} />
              <span>New Project</span>
            </Link>
            <button onClick={handleLogout} className="nav-link nav-logout">
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="footer">
        <p>&copy; 2026 LLM Deploy Platform. Auto-generate and deploy web applications with AI.</p>
      </footer>
    </div>
  );
};
