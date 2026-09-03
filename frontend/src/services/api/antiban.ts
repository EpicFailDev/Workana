/**
 * Serviços de API para o Sistema Anti-Ban e Proteção de Automação.
 */
import { apiRequest } from './client';

export interface AntibanStatus {
  searches_this_hour: number;
  max_per_hour: number;
  in_cooldown: boolean;
  cooldown_remaining_seconds: number;
  last_search_time?: string | null;
  safe_mode_enabled: boolean;
}

export interface AntibanConfig {
  max_searches_per_hour: number;
  min_delay_between_searches_sec: number;
  max_delay_between_searches_sec: number;
  cooldown_period_minutes: number;
  safe_mode: boolean;
  user_agent_rotation: boolean;
}

export interface CanSearchResponse {
  can_search: boolean;
  message: string;
  searches_this_hour: number;
  max_per_hour: number;
}

export const antibanApi = {
  async getAntibanStatus() {
    return apiRequest<AntibanStatus>('/antiban/status');
  },

  async getAntibanConfig() {
    return apiRequest<AntibanConfig>('/antiban/config');
  },

  async updateAntibanConfig(config: Partial<AntibanConfig>) {
    return apiRequest<{
      success: boolean;
      message: string;
      config: AntibanConfig;
    }>('/antiban/config', {
      method: 'PUT',
      body: config,
    });
  },

  async canSearch() {
    return apiRequest<CanSearchResponse>('/antiban/can-search');
  },
};
