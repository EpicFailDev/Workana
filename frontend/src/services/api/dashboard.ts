/**
 * Serviços de API para Estatísticas e Dashboard.
 */
import { apiRequest } from './client';

export interface DashboardStats {
  total_proposals_sent: number;
  proposals_today: number;
  proposals_this_week: number;
  proposals_this_month: number;
  response_rate: number;
  accepted_proposals: number;
  pending_proposals: number;
  last_activity: string | null;
}

export interface ActivityLogItem {
  id: number;
  user_id: string;
  action_type: string;
  description: string;
  details?: any;
  project_id?: string | null;
  status: 'success' | 'warning' | 'error' | 'info';
  created_at: string;
}

export interface ActivityLogsResponse {
  logs: ActivityLogItem[];
  total: number;
}

export interface DailyStatistic {
  date: string;
  projects_found: number;
  projects_viewed: number;
  proposals_sent: number;
  proposals_accepted: number;
  proposals_rejected: number;
  logins_count: number;
  searches_count: number;
  errors_count: number;
}

export interface StatisticsResponse {
  statistics: DailyStatistic[];
  days: number;
}

export interface StatisticsSummary {
  today?: {
    proposals_sent: number;
    projects_found: number;
    searches_count: number;
  };
  week?: {
    proposals_sent: number;
    projects_found: number;
    searches_count: number;
  };
  month?: {
    proposals_sent: number;
    projects_found: number;
  };
}

export const dashboardApi = {
  async getDashboardStats() {
    return apiRequest<DashboardStats>('/dashboard/stats');
  },

  async getActivityLogs(params?: { limit?: number; action_type?: string; status?: string }) {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.action_type) query.set('action_type', params.action_type);
    if (params?.status) query.set('status', params.status);
    return apiRequest<ActivityLogsResponse>(`/logs?${query.toString()}`);
  },

  async getStatistics(days = 30) {
    return apiRequest<StatisticsResponse>(`/statistics?days=${days}`);
  },

  async getStatisticsSummary() {
    return apiRequest<StatisticsSummary>('/statistics/summary');
  },
};
