export interface Project {
  id: string;
  user_id: string;
  task_id: string;
  brief: string;
  checks: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'generating_code';
  github_url?: string;
  pages_url?: string;
  round: number;
  created_at: string;
  updated_at: string;
  error?: string;
}

export interface CreateProjectRequest {
  brief: string;
  checks?: string[];
  attachments?: File[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
