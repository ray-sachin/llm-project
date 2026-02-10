import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import type { Project } from '../types';
import { CheckCircle, Clock, AlertCircle, ExternalLink, Loader } from 'lucide-react';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
    const interval = setInterval(loadProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadProjects = async () => {
    try {
      setError(null);
      const data = await api.getProjects();
      setProjects(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="status-icon completed" size={20} />;
      case 'processing':
      case 'generating_code':
        return <Loader className="status-icon processing animate-spin" size={20} />;
      case 'failed':
        return <AlertCircle className="status-icon failed" size={20} />;
      default:
        return <Clock className="status-icon pending" size={20} />;
    }
  };

  const getStatusBadge = (status: Project['status']) => {
    const statusConfig: Record<Project['status'], { label: string; className: string }> = {
      completed: { label: 'Completed', className: 'badge-completed' },
      processing: { label: 'Processing', className: 'badge-processing' },
      generating_code: { label: 'Generating', className: 'badge-processing' },
      failed: { label: 'Failed', className: 'badge-failed' },
      pending: { label: 'Pending', className: 'badge-pending' },
    };
    const config = statusConfig[status];
    return <span className={`badge ${config.className}`}>{config.label}</span>;
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Project Dashboard</h1>
          <p className="subtitle">Manage your LLM-generated web applications</p>
        </div>
        <Link to="/create" className="btn btn-primary">
          Create New Project
        </Link>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-container">
          <Loader className="animate-spin" size={40} />
          <p>Loading projects...</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✨</div>
          <h2>No projects yet</h2>
          <p>Create your first LLM-generated web application</p>
          <Link to="/create" className="btn btn-primary">
            Get Started
          </Link>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((project) => (
            <div key={project.id} className="project-card">
              <div className="project-header">
                <div className="project-title">
                  {getStatusIcon(project.status)}
                  <h3>{project.task_id}</h3>
                </div>
                {getStatusBadge(project.status)}
              </div>

              <p className="project-brief">{project.brief}</p>

              <div className="project-meta">
                <span>Round {project.round}</span>
                <span>{new Date(project.created_at).toLocaleDateString()}</span>
              </div>

              <div className="project-actions">
                {project.pages_url && (
                  <a href={project.pages_url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-secondary">
                    <ExternalLink size={16} />
                    View Live
                  </a>
                )}
                {project.github_url && (
                  <a href={project.github_url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-secondary">
                    <ExternalLink size={16} />
                    GitHub
                  </a>
                )}
              </div>

              {project.error && (
                <div className="error-message">
                  <AlertCircle size={16} />
                  {project.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
