// frontend/src/pages/Settings.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/Settings.css';

interface GithubToken {
  github_username: string;
  configured: boolean;
}

interface AipipeConfig {
  configured: boolean;
  masked_token?: string;
}

export default function Settings() {
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [githubConfig, setGithubConfig] = useState<GithubToken | null>(null);
  const [showToken, setShowToken] = useState(false);

  // AIPIPE state
  const [aipipeToken, setAipipeToken] = useState('');
  const [aipipeConfig, setAipipeConfig] = useState<AipipeConfig | null>(null);
  const [aipipeLoading, setAipipeLoading] = useState(false);
  const [aipipeSaved, setAipipeSaved] = useState(false);
  const [aipipeError, setAipipeError] = useState<string | null>(null);
  const [showAipipeToken, setShowAipipeToken] = useState(false);

  const accessToken = localStorage.getItem('access_token');

  useEffect(() => {
    if (!accessToken) {
      navigate('/login');
      return;
    }
    loadGithubConfig();
    loadAipipeConfig();
  }, []);

  const loadGithubConfig = async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/github-token`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setGithubConfig(response.data);
      setUsername(response.data.github_username);
    } catch (err: any) {
      if (err.response?.status !== 404) {
        setError('Failed to load GitHub configuration');
      }
    }
  };

  const handleSaveToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);

    if (!token || !username) {
      setError('Please provide both GitHub token and username');
      return;
    }

    setLoading(true);

    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/github-token`,
        {
          token,
          github_username: username,
        },
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );

      setSaved(true);
      setToken('');
      setGithubConfig({ github_username: username, configured: true });
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save GitHub token');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveToken = async () => {
    if (!window.confirm('Are you sure you want to remove your GitHub token?')) {
      return;
    }

    try {
      await axios.delete(`${import.meta.env.VITE_API_URL}/api/auth/github-token`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setGithubConfig(null);
      setUsername('');
      setError(null);
    } catch (err: any) {
      setError('Failed to remove GitHub token');
    }
  };

  // === AIPIPE Token Functions ===
  const loadAipipeConfig = async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/aipipe-token`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setAipipeConfig(response.data);
    } catch (err: any) {
      if (err.response?.status !== 404) {
        console.error('Failed to load AIPIPE config');
      }
    }
  };

  const handleSaveAipipeToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setAipipeError(null);
    setAipipeSaved(false);

    if (!aipipeToken) {
      setAipipeError('Please enter your AIPIPE token');
      return;
    }

    setAipipeLoading(true);

    try {
      await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/aipipe-token`,
        { token: aipipeToken },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );

      setAipipeSaved(true);
      setAipipeToken('');
      loadAipipeConfig();
      setTimeout(() => setAipipeSaved(false), 3000);
    } catch (err: any) {
      setAipipeError(err.response?.data?.detail || 'Failed to save AIPIPE token');
    } finally {
      setAipipeLoading(false);
    }
  };

  const handleRemoveAipipeToken = async () => {
    if (!window.confirm('Are you sure you want to remove your AIPIPE token?')) {
      return;
    }

    try {
      await axios.delete(`${import.meta.env.VITE_API_URL}/api/auth/aipipe-token`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setAipipeConfig(null);
      setAipipeError(null);
    } catch (err: any) {
      setAipipeError('Failed to remove AIPIPE token');
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>⚙️ Account Settings</h1>
        <button className="btn-back" onClick={() => navigate('/')}>
          ← Back to Dashboard
        </button>
      </div>

      <div className="settings-content">
        {/* GitHub Token Section */}
        <div className="settings-section">
          <h2>GitHub Configuration</h2>
          <p className="section-description">
            Add your personal GitHub token to deploy projects to your repositories.
          </p>

          {githubConfig?.configured && (
            <div className="success-banner">
              ✅ GitHub token configured for <strong>{username}</strong>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
          {saved && <div className="success-message">✅ GitHub token saved successfully!</div>}

          <form onSubmit={handleSaveToken} className="settings-form">
            <div className="form-group">
              <label htmlFor="github-username">GitHub Username</label>
              <input
                type="text"
                id="github-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your-github-username"
              />
              <small>Your GitHub account where repositories will be created</small>
            </div>

            <div className="form-group">
              <label htmlFor="github-token">GitHub Personal Access Token</label>
              <div className="token-input-wrapper">
                <input
                  type={showToken ? 'text' : 'password'}
                  id="github-token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="btn-toggle-visibility"
                >
                  {showToken ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              <small>
                Get your token at{' '}
                <a href="https://github.com/settings/tokens?type=pat" target="_blank" rel="noopener noreferrer">
                  GitHub Settings
                </a>
              </small>
              <small style={{ display: 'block', marginTop: '8px' }}>
                <strong>Required permissions:</strong> Administration, Contents, Pages
              </small>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Saving...' : 'Save GitHub Token'}
              </button>
              {githubConfig?.configured && (
                <button type="button" onClick={handleRemoveToken} className="btn-danger">
                  Remove Token
                </button>
              )}
            </div>
          </form>
        </div>

        {/* AIPIPE Token Section */}
        <div className="settings-section">
          <h2>LLM Provider Token</h2>
          <p className="section-description">
            Add your AIPIPE token for AI-powered code generation.
          </p>

          {aipipeConfig?.configured && (
            <div className="success-banner">
              ✅ AIPIPE token configured ({aipipeConfig.masked_token})
            </div>
          )}

          {aipipeError && <div className="error-message">{aipipeError}</div>}
          {aipipeSaved && <div className="success-message">✅ AIPIPE token saved successfully!</div>}

          <form onSubmit={handleSaveAipipeToken} className="settings-form">
            <div className="form-group">
              <label htmlFor="aipipe-token">AIPIPE API Token</label>
              <div className="token-input-wrapper">
                <input
                  type={showAipipeToken ? 'text' : 'password'}
                  id="aipipe-token"
                  value={aipipeToken}
                  onChange={(e) => setAipipeToken(e.target.value)}
                  placeholder="eyJhbGciOiJIUzI1NiIs..."
                />
                <button
                  type="button"
                  onClick={() => setShowAipipeToken(!showAipipeToken)}
                  className="btn-toggle-visibility"
                >
                  {showAipipeToken ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              <small>
                Get your token at{' '}
                <a href="https://aipipe.org/login" target="_blank" rel="noopener noreferrer">
                  aipipe.org
                </a>
              </small>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={aipipeLoading}>
                {aipipeLoading ? 'Saving...' : 'Save AIPIPE Token'}
              </button>
              {aipipeConfig?.configured && (
                <button type="button" onClick={handleRemoveAipipeToken} className="btn-danger">
                  Remove Token
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Instructions */}
        <div className="settings-section">
          <h2>📖 Getting Started</h2>
          <ol>
            <li>Configure your GitHub personal access token above</li>
            <li>Go to the <a href="/">Dashboard</a> and create a new project</li>
            <li>Your code will be deployed to GitHub Pages automatically</li>
            <li>Each project gets its own repository and live website</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
