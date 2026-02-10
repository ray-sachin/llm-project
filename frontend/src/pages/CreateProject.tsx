import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { Send, Upload, AlertCircle, CheckCircle, Loader, Copy, Eye } from 'lucide-react';
import { historyStorage } from '../utils/historyStorage';
import './CreateProject.css';

export const CreateProject: React.FC = () => {
  const navigate = useNavigate();
  const [brief, setBrief] = useState('');
  const [checks, setChecks] = useState<string>('');
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!brief.trim()) {
      setError('Please enter a project brief');
      return;
    }

    setLoading(true);
    try {
      const checksArray = checks
        .split(',')
        .map((c) => c.trim())
        .filter((c) => c.length > 0);

      const response = await api.submitProject(brief, checksArray, files);
      
      if (response.task_id) {
        // Save to history
        historyStorage.addSubmission({
          task_id: response.task_id,
          brief,
          checks: checksArray,
          status: 'processing',
          github_url: undefined,
          pages_url: undefined,
          error: undefined,
        });
        
        setTaskId(response.task_id);
        setSuccess(true);
        setBrief('');
        setChecks('');
        setFiles([]);
      } else {
        setError(response.error || 'Failed to submit project');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyTaskId = () => {
    if (taskId) {
      navigator.clipboard.writeText(taskId);
    }
  };

  const goToHistory = () => {
    navigate('/history');
  };

  return (
    <div className="create-project">
      <div className="form-container">
        <div className="form-header">
          <h1>Create New Project</h1>
          <p className="form-subtitle">
            Describe your web application idea and let AI generate it for you
          </p>
        </div>

        {error && (
          <div className="form-alert alert-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="form-alert alert-success">
            <CheckCircle size={20} />
            <div className="success-content">
              <p className="alert-title">Project submitted successfully! 🎉</p>
              <p className="alert-subtitle">
                Your project is now being processed by AI
              </p>
              
              {taskId && (
                <div className="task-id-display">
                  <p className="task-label">Task ID (save this for reference)</p>
                  <div className="task-id-box">
                    <code className="task-id-value">{taskId}</code>
                    <button
                      onClick={handleCopyTaskId}
                      className="btn-copy"
                      type="button"
                      title="Copy Task ID"
                    >
                      <Copy size={16} />
                    </button>
                  </div>
                </div>
              )}
              
              <div className="success-actions">
                <button
                  onClick={goToHistory}
                  className="btn btn-primary"
                  type="button"
                >
                  <Eye size={16} />
                  View in History
                </button>
                <button
                  onClick={() => setSuccess(false)}
                  className="btn btn-secondary"
                  type="button"
                >
                  Create Another
                </button>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label htmlFor="brief" className="form-label">
              Project Brief <span className="required">*</span>
            </label>
            <p className="form-help">
              Describe what kind of web application you want to create
            </p>
            <textarea
              id="brief"
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="e.g., Create a personal portfolio website with a projects section, about me page, and contact form..."
              className="form-textarea"
              rows={6}
              disabled={loading}
            />
            <div className="char-count">
              {brief.length} characters
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="checks" className="form-label">
              Requirements / Checks <span className="optional">(Optional)</span>
            </label>
            <p className="form-help">
              Enter comma-separated requirements (e.g., responsive design, dark mode, animations)
            </p>
            <input
              id="checks"
              type="text"
              value={checks}
              onChange={(e) => setChecks(e.target.value)}
              placeholder="e.g., Mobile responsive, Dark mode support, Smooth animations"
              className="form-input"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              Attachments <span className="optional">(Optional)</span>
            </label>
            <p className="form-help">
              Upload reference images, designs, or additional files (images, documents)
            </p>

            <div className="file-upload">
              <input
                type="file"
                id="file-input"
                multiple
                onChange={handleFileChange}
                className="file-input-hidden"
                disabled={loading}
                accept="image/*,.pdf,.doc,.docx,.txt"
              />
              <label htmlFor="file-input" className="file-upload-label">
                <Upload size={24} />
                <div>
                  <p className="file-upload-title">Click to upload or drag files here</p>
                  <p className="file-upload-subtitle">Supported: Images, PDF, Documents</p>
                </div>
              </label>
            </div>

            {files.length > 0 && (
              <div className="file-list">
                <p className="file-list-title">Selected files:</p>
                <ul className="file-items">
                  {files.map((file, index) => (
                    <li key={index} className="file-item">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">({(file.size / 1024).toFixed(2)} KB)</span>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="btn-remove"
                        disabled={loading}
                      >
                        ✕
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-submit"
            disabled={loading || !brief.trim()}
          >
            {loading ? (
              <>
                <Loader size={18} className="animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send size={18} />
                Submit Project
              </>
            )}
          </button>
        </form>

        <div className="form-info">
          <div className="info-box">
            <h3>How it works</h3>
            <ol>
              <li>Describe your project in the brief above</li>
              <li>Our AI generates the HTML, CSS, and JavaScript</li>
              <li>Code is automatically deployed to GitHub Pages</li>
              <li>Your live website is ready in minutes</li>
            </ol>
          </div>

          <div className="info-box">
            <h3>Best Practices</h3>
            <ul>
              <li>Be specific about your design preferences</li>
              <li>Include the main features you want</li>
              <li>Mention target audience or use case</li>
              <li>Attach reference images for design inspiration</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
