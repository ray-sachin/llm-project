import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type { Project } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include Bearer token
apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token');
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Add response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_id');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Submit a new project request
  submitProject: async (brief: string, checks?: string[], attachments?: File[]): Promise<any> => {
    const formData = new FormData();
    formData.append('brief', brief);
    
    if (checks && checks.length > 0) {
      formData.append('checks', JSON.stringify(checks));
    }
    
    if (attachments && attachments.length > 0) {
      attachments.forEach((file) => {
        formData.append('attachments', file);
      });
    }

    const response = await apiClient.post('/deploy', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get('/projects');
    return response.data;
  },

  // Get a specific project
  getProject: async (id: string): Promise<Project> => {
    const response = await apiClient.get(`/projects/${id}`);
    return response.data;
  },

  // Get project status
  getProjectStatus: async (taskId: string): Promise<any> => {
    const response = await apiClient.get(`/status/${taskId}`);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<boolean> => {
    try {
      await apiClient.get('/health');
      return true;
    } catch {
      return false;
    }
  },
};

export default apiClient;
