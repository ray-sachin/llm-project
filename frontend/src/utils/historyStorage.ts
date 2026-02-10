export interface SubmissionHistory {
  task_id: string;
  brief: string;
  checks: string[];
  status: 'pending' | 'processing' | 'generating_code' | 'completed' | 'failed';
  created_at: string;
  github_url?: string;
  pages_url?: string;
  error?: string;
}

const HISTORY_KEY = 'llm_deployment_history';

export const historyStorage = {
  // Add a new submission to history
  addSubmission: (submission: Omit<SubmissionHistory, 'created_at'>) => {
    const history = historyStorage.getHistory();
    const newSubmission: SubmissionHistory = {
      ...submission,
      created_at: new Date().toISOString(),
    };
    history.unshift(newSubmission); // Add to beginning (newest first)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    return newSubmission;
  },

  // Get all submissions
  getHistory: (): SubmissionHistory[] => {
    try {
      const data = localStorage.getItem(HISTORY_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  // Get a specific submission by task_id
  getSubmission: (task_id: string): SubmissionHistory | undefined => {
    const history = historyStorage.getHistory();
    return history.find((s) => s.task_id === task_id);
  },

  // Update a submission (for status updates)
  updateSubmission: (task_id: string, updates: Partial<SubmissionHistory>) => {
    const history = historyStorage.getHistory();
    const index = history.findIndex((s) => s.task_id === task_id);
    if (index !== -1) {
      history[index] = { ...history[index], ...updates };
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      return history[index];
    }
    return undefined;
  },

  // Delete a submission
  deleteSubmission: (task_id: string) => {
    const history = historyStorage.getHistory();
    const filtered = history.filter((s) => s.task_id !== task_id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(filtered));
  },

  // Clear all history
  clearHistory: () => {
    localStorage.removeItem(HISTORY_KEY);
  },
};
