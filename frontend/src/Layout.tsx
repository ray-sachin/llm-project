import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { Zap, Plus, Home, History, Settings, LogOut, Menu, X } from 'lucide-react';
import './Layout.css';

export const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Close menu on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

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
            <span>Madme</span>
          </Link>

          {/* Hamburger button — mobile only */}
          <button
            className="hamburger-btn"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>

          {/* Overlay for mobile */}
          {menuOpen && <div className="nav-overlay" onClick={() => setMenuOpen(false)} />}

          <div className={`nav-links${menuOpen ? ' open' : ''}`}>
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
        <p>&copy; 2026 Madme. Auto-generate and deploy web applications with AI.</p>
      </footer>
    </div>
  );
};
