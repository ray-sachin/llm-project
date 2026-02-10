import React, { useState, useEffect } from 'react';
import { Copy, ExternalLink, Trash2, RefreshCw, CheckCircle, AlertCircle, Clock, Edit3, X } from 'lucide-react';
import { api } from '../api';
import type { Project } from '../types';
import './History.css';

export const History: React.FC = () => {
  const [submissions, setSubmissions] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Edit modal state
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editBrief, setEditBrief] = useState('');
  const [editChecks, setEditChecks] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  useEffect(() => {
    // Load history on mount
    loadProjects();

    // Auto-refresh statuses every 5 seconds (faster for active processing)
    const interval = setInterval(() => {
      refreshProjects();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const projects = await api.getProjects();
      setSubmissions(projects);
      setError(null);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const refreshProjects = async () => {
    try {
      const projects = await api.getProjects();
      setSubmissions(projects);
    } catch (err) {
      console.error('Failed to refresh projects:', err);
    }
  };

  const handleRefreshOne = async (taskId: string) => {
    setRefreshing(taskId);
    try {
      const status = await api.getProjectStatus(taskId);
      if (status) {
        // Refresh the full projects list
        await refreshProjects();
      }
    } catch (err) {
      console.error('Failed to refresh:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh');
    } finally {
      setRefreshing(null);
    }
  };

  const handleCopyTaskId = (taskId: string) => {
    navigator.clipboard.writeText(taskId);
    setCopied(taskId);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleDelete = (_taskId: string) => {
    if (confirm('Are you sure you want to delete this submission from history?')) {
      // TODO: Implement delete endpoint
      loadProjects();
    }
  };

  const handleClearAll = () => {
    if (confirm('Clear all submission history? This cannot be undone.')) {
      // TODO: Implement clear all endpoint
      loadProjects();
    }
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setEditBrief(project.brief);
    // Convert checks object to array of strings
    const checksArray = project.checks ? Object.values(project.checks).map(v => String(v)) : [];
    setEditChecks(checksArray);
    setSubmitSuccess(false);
  };

  const handleCloseEditModal = () => {
    setEditingProject(null);
    setEditBrief('');
    setEditChecks([]);
    setSubmitSuccess(false);
  };

  const handleSubmitModification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProject) return;

    setSubmitting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('brief', editBrief);
      formData.append('checks', JSON.stringify(editChecks));
      // The backend will auto-increment the round based on the task_id

      await api.submitProject(editBrief, editChecks);
      
      setSubmitSuccess(true);
      setTimeout(() => {
        handleCloseEditModal();
        loadProjects();
      }, 2000);
    } catch (err) {
      console.error('Failed to submit modification:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit modifications');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddCheck = () => {
    setEditChecks([...editChecks, '']);
  };

  const handleUpdateCheck = (index: number, value: string) => {
    const newChecks = [...editChecks];
    newChecks[index] = value;
    setEditChecks(newChecks);
  };

  const handleRemoveCheck = (index: number) => {
    setEditChecks(editChecks.filter((_, i) => i !== index));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'status-completed';
      case 'failed':
        return 'status-failed';
      case 'processing':
      case 'generating_code':
        return 'status-processing';
      default:
        return 'status-pending';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} />;
      case 'failed':
        return <AlertCircle size={16} />;
      case 'processing':
      case 'generating_code':
        return <RefreshCw size={16} className="animate-spin" />;
      default:
        return <Clock size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="history-page">
        <div className="loading-state">
          <RefreshCw size={48} className="animate-spin" />
          <h2>Loading projects...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>Project History</h1>
        <p className="history-subtitle">
          View all your project submissions and their deployment status
        </p>
      </div>

      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {submissions.length === 0 ? (
        <div className="empty-state">
          <Clock size={48} />
          <h2>No projects yet</h2>
          <p>Create your first project to see it appear here</p>
        </div>
      ) : (
        <>
          <div className="history-controls">
            <button
              onClick={refreshProjects}
              className="btn btn-secondary"
              title="Refresh all projects"
            >
              <RefreshCw size={16} />
              Refresh All
            </button>
            {submissions.length > 0 && (
              <button
                onClick={handleClearAll}
                className="btn btn-danger"
                title="Clear all history"
              >
                Clear All
              </button>
            )}
          </div>

          <div className="submissions-grid">
            {submissions.map((submission) => (
              <div key={submission.id || submission.task_id} className="submission-card">
                <div className="card-header">
                  <div className="header-title">
                    <h3>{submission.brief.substring(0, 50)}</h3>
                    <span className={`status-badge ${getStatusColor(submission.status)}`}>
                      {getStatusIcon(submission.status)}
                      <span>{submission.status}</span>
                    </span>
                    {submission.round > 1 && (
                      <span className="round-badge">Round {submission.round}</span>
                    )}
                  </div>
                  <div className="header-actions">
                    {submission.status === 'completed' && (
                      <button
                        onClick={() => handleEditProject(submission)}
                        className="btn-icon btn-edit"
                        title="Modify Project"
                      >
                        <Edit3 size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(submission.task_id)}
                      className="btn-icon btn-delete"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="card-content">
                  <div className="card-section">
                    <label>Brief</label>
                    <p className="brief-text">{submission.brief}</p>
                  </div>

                  {submission.checks && Object.keys(submission.checks).length > 0 && (
                    <div className="card-section">
                      <label>Requirements</label>
                      <div className="checks-list">
                        {Object.entries(submission.checks).map(([key, value]) => (
                          <span key={key} className="check-badge">
                            {typeof value === 'string' ? value : key}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="card-section">
                    <label>Task ID</label>
                    <div className="task-id-container">
                      <code className="task-id">{submission.task_id}</code>
                      <button
                        onClick={() => handleCopyTaskId(submission.task_id)}
                        className="btn-icon"
                        title="Copy Task ID"
                      >
                        <Copy size={14} />
                        {copied === submission.task_id && <span className="copy-feedback">Copied!</span>}
                      </button>
                    </div>
                  </div>

                  <div className="card-section">
                    <label>Submitted</label>
                    <p className="timestamp">
                      {new Date(submission.created_at).toLocaleString()}
                    </p>
                  </div>

                  {submission.github_url && (
                    <div className="card-section">
                      <label>GitHub Repository</label>
                      <a
                        href={submission.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-link"
                      >
                        <ExternalLink size={16} />
                        View Repository
                      </a>
                    </div>
                  )}

                  {submission.pages_url && (
                    <div className="card-section">
                      <label>Live Website</label>
                      <a
                        href={submission.pages_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-primary-link"
                      >
                        <ExternalLink size={16} />
                        Open Live Site
                      </a>
                    </div>
                  )}
                </div>

                <div className="card-footer">
                  {submission.status === 'completed' && submission.pages_url ? (
                    <div className="footer-buttons">
                      <a
                        href={submission.pages_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-visit btn-small"
                      >
                        <ExternalLink size={14} />
                        Visit Website
                      </a>
                    </div>
                  ) : submission.status === 'completed' && submission.github_url ? (
                    <div className="footer-buttons">
                      <a
                        href={submission.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-visit btn-small"
                      >
                        <ExternalLink size={14} />
                        View Repo
                      </a>
                    </div>
                  ) : (
                    <div className="footer-buttons">
                      <button
                        onClick={() => handleRefreshOne(submission.task_id)}
                        disabled={refreshing === submission.task_id}
                        className="btn btn-secondary btn-small"
                      >
                        {refreshing === submission.task_id ? (
                          <>
                            <RefreshCw size={14} className="animate-spin" />
                            Checking...
                          </>
                        ) : (
                          <>
                            <RefreshCw size={14} />
                            Refresh
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Edit Modal */}
      {editingProject && (
        <div className="modal-overlay" onClick={handleCloseEditModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Modify Project - Round {(editingProject.round || 1) + 1}</h2>
              <button onClick={handleCloseEditModal} className="btn-close">
                <X size={20} />
              </button>
            </div>

            {submitSuccess ? (
              <div className="success-state">
                <CheckCircle size={48} className="success-icon" />
                <h3>Modifications Submitted!</h3>
                <p>Your updated project is being processed...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmitModification} className="modal-form">
                {error && (
                  <div className="error-banner">
                    <AlertCircle size={20} />
                    <span>{error}</span>
                  </div>
                )}

                <div className="form-group">
                  <label>Project Brief</label>
                  <textarea
                    value={editBrief}
                    onChange={(e) => setEditBrief(e.target.value)}
                    placeholder="Describe your project modifications..."
                    rows={4}
                    required
                  />
                  <small>Describe what changes or improvements you want to make</small>
                </div>

                <div className="form-group">
                  <label>Requirements (Optional)</label>
                  {editChecks.map((check, index) => (
                    <div key={index} className="check-input-group">
                      <input
                        type="text"
                        value={check}
                        onChange={(e) => handleUpdateCheck(index, e.target.value)}
                        placeholder="Enter a requirement"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveCheck(index)}
                        className="btn-remove-check"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={handleAddCheck}
                    className="btn-add-check"
                  >
                    + Add Requirement
                  </button>
                </div>

                <div className="modal-footer">
                  <button
                    type="button"
                    onClick={handleCloseEditModal}
                    className="btn btn-secondary"
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={submitting || !editBrief.trim()}
                  >
                    {submitting ? (
                      <>
                        <RefreshCw size={16} className="animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      'Submit Modifications'
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
