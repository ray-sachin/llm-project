// frontend/src/pages/AuthCallback.tsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import axios from 'axios';
import '../styles/Auth.css';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // Supabase will automatically parse the hash fragment and establish the session
      const { data, error } = await supabase.auth.getSession();

      if (error) {
        console.error('Auth callback error:', error);
        setStatus('error');
        setMessage('Authentication failed. Please try again.');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (data.session) {
        const session = data.session;
        const user = session.user;

        // Store tokens
        localStorage.setItem('access_token', session.access_token);
        localStorage.setItem('refresh_token', session.refresh_token);
        localStorage.setItem('user_id', user.id);

        // Ensure user profile exists in the backend
        try {
          await axios.post(
            `${import.meta.env.VITE_API_URL}/api/auth/oauth-profile`,
            {
              user_id: user.id,
              email: user.email,
              username:
                user.user_metadata?.user_name ||
                user.user_metadata?.preferred_username ||
                user.user_metadata?.name ||
                user.email?.split('@')[0] || 'user',
              avatar_url: user.user_metadata?.avatar_url || null,
              provider: user.app_metadata?.provider || 'unknown',
              provider_token: session.provider_token || null,
            },
            {
              headers: { Authorization: `Bearer ${session.access_token}` },
            }
          );
        } catch (profileErr) {
          console.warn('Could not sync profile:', profileErr);
        }

        // If this was a GitHub OAuth login, auto-save the GitHub token
        // BUT only if the user doesn't already have one manually configured
        if (
          session.provider_token &&
          user.app_metadata?.provider === 'github'
        ) {
          const githubUsername =
            user.user_metadata?.user_name ||
            user.user_metadata?.preferred_username;

          if (githubUsername) {
            try {
              // Check if user already has a GitHub token configured
              const existingConfig = await axios.get(
                `${import.meta.env.VITE_API_URL}/api/auth/github-token`,
                { headers: { Authorization: `Bearer ${session.access_token}` } }
              ).catch(() => null);

              // Only save if no existing config (404 means not configured)
              if (!existingConfig || !existingConfig.data?.configured) {
                await axios.post(
                  `${import.meta.env.VITE_API_URL}/api/auth/github-token`,
                  {
                    token: session.provider_token,
                    github_username: githubUsername,
                  },
                  {
                    headers: { Authorization: `Bearer ${session.access_token}` },
                  }
                );
              }
            } catch (ghErr) {
              console.warn('Could not auto-save GitHub token:', ghErr);
            }
          }
        }

        setStatus('success');
        setMessage('Authentication successful! Redirecting...');
        setTimeout(() => navigate('/'), 1000);
      } else {
        // No session — might be email verification link without auto-login
        // Check if the URL has a type=signup or type=recovery
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.replace('#', ''));
        const type = params.get('type');

        if (type === 'signup' || type === 'email') {
          setStatus('success');
          setMessage('Email verified successfully! You can now log in.');
          setTimeout(() => navigate('/login'), 2500);
        } else {
          setStatus('error');
          setMessage('No session found. Please log in.');
          setTimeout(() => navigate('/login'), 2500);
        }
      }
    } catch (err) {
      console.error('Callback processing error:', err);
      setStatus('error');
      setMessage('Something went wrong. Redirecting to login...');
      setTimeout(() => navigate('/login'), 3000);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box" style={{ textAlign: 'center' }}>
        <h1>🚀 Madme</h1>

        {status === 'loading' && (
          <>
            <div
              style={{
                margin: '2rem auto',
                width: '2rem',
                height: '2rem',
                border: '3px solid var(--border-color)',
                borderTopColor: 'var(--accent-primary)',
                borderRadius: '50%',
                animation: 'spin 0.7s linear infinite',
              }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem' }}>
              {message}
            </p>
          </>
        )}

        {status === 'success' && (
          <div className="success-message" style={{ marginTop: '1.5rem' }}>
            {message}
          </div>
        )}

        {status === 'error' && (
          <div className="error-message" style={{ marginTop: '1.5rem' }}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
