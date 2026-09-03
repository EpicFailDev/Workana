/**
 * Serviços de API para Perfil Público do Workana.
 */
import { apiRequest } from './client';

export interface ProfileMetrics {
  success: boolean;
  profile_url: string | null;
  username: string | null;
  display_name: string | null;
  projects_completed: number;
  projects_in_progress: number;
  hours_worked: number;
  average_rating: number | null;
  total_reviews: number;
  member_since: string | null;
  country: string | null;
  hourly_rate: string | null;
  skills: string[];
  last_login: string | null;
  profile_photo_url: string | null;
  last_sync: string | null;
  is_configured: boolean;
  error: string | null;
}

export interface ProfileConfig {
  profile_url: string | null;
  auto_sync_enabled: boolean;
  sync_interval_hours: number;
  last_sync_at: string | null;
  is_configured: boolean;
}

export interface ProfileValidationResult {
  valid: boolean;
  display_name?: string;
  username?: string;
  error?: string;
}

export const profileApi = {
  async getProfileMetrics() {
    return apiRequest<ProfileMetrics>('/profile/metrics');
  },

  async syncProfileMetrics(force: boolean = false) {
    return apiRequest<ProfileMetrics>(`/profile/sync?force=${force}`, { method: 'POST' });
  },

  async getProfileConfig() {
    return apiRequest<ProfileConfig>('/profile/config');
  },

  async updateProfileConfig(config: {
    profile_url: string;
    auto_sync_enabled?: boolean;
    sync_interval_hours?: number;
  }) {
    return apiRequest<{ success: boolean; message: string }>('/profile/config', {
      method: 'PUT',
      body: config,
    });
  },

  async validateProfileUrl(url: string) {
    return apiRequest<ProfileValidationResult>(`/profile/validate?url=${encodeURIComponent(url)}`, {
      method: 'POST',
    });
  },
};
