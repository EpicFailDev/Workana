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

export const dashboardApi = {
  async getDashboardStats() {
    return apiRequest<DashboardStats>('/dashboard/stats');
  },
};
