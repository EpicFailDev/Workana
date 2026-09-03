/**
 * Serviços de API para Automação e Credenciais.
 */
import { apiRequest } from './client';

export interface AutomationStatus {
  is_running: boolean;
  is_logged_in: boolean;
  current_action: string | null;
  proposals_sent_today: number;
  max_proposals_per_day: number;
  last_error: string | null;
}

export interface AutomationConfig {
  headless: boolean;
  delay_between_actions_ms: number;
  max_proposals_per_day: number;
  auto_apply: boolean;
  preferred_template_id: number | null;
  gemini_api_key?: string;
  user_full_name?: string;
  telegram_enabled?: boolean;
  telegram_bot_token?: string;
  telegram_chat_id?: string;
  webhook_enabled?: boolean;
  webhook_url?: string;
  email_enabled?: boolean;
  email_to?: string;
}

export interface CredentialsStatus {
  configured: boolean;
  email: string | null;
  login_method?: 'password' | 'google' | null;
  session_ready?: boolean;
  session_updated_at?: string | null;
}

export interface SessionHealthResponse {
  status: 'healthy' | 'warning' | 'expired' | 'disconnected' | 'empty';
  valid: boolean;
  message: string;
  cookies_count: number;
  has_cloudflare_clearance: boolean;
  account_email?: string | null;
  last_tested_at?: string;
}

export interface RealtimeStatusResponse {
  is_active: boolean;
  channels: string[];
  gateway: string;
}

export const automationApi = {
  async getAutomationStatus() {
    return apiRequest<AutomationStatus>('/automation/status');
  },

  async getAutomationConfig() {
    return apiRequest<AutomationConfig>('/automation/config');
  },

  async updateAutomationConfig(config: Partial<AutomationConfig>) {
    return apiRequest('/automation/config', {
      method: 'PUT',
      body: config,
    });
  },

  async getCredentialsStatus() {
    return apiRequest<CredentialsStatus>('/automation/credentials');
  },

  async updateCredentials(creds: { email: string; password: string }) {
    return apiRequest('/automation/credentials', {
      method: 'POST',
      body: creds,
    });
  },

  async googleLogin() {
    return apiRequest<{ success: boolean; message?: string; email?: string | null }>(
      '/automation/workana/google-login',
      { method: 'POST' }
    );
  },

  async importSession(session_json: string, account_email?: string) {
    return apiRequest<{ success: boolean; message?: string }>(
      '/automation/workana/session-import',
      { method: 'POST', body: { session_json, account_email: account_email || null } }
    );
  },

  async disconnectWorkana() {
    return apiRequest<{ success: boolean; message?: string }>('/automation/workana/disconnect', {
      method: 'POST',
    });
  },

  async getSessionHealth() {
    return apiRequest<SessionHealthResponse>('/automation/session/health');
  },

  async getRealtimeStatus() {
    return apiRequest<RealtimeStatusResponse>('/automation/realtime-status');
  },

  async refreshCatalog(filters?: Record<string, any>) {
    return apiRequest<{
      success: boolean;
      message: string;
      upserted?: number;
      marked_gone?: number;
      errors?: number;
    }>('/automation/catalog/refresh', {
      method: 'POST',
      body: filters,
    });
  },

  async restoreGoneCatalog(category?: string) {
    const query = category ? `?category=${encodeURIComponent(category)}` : '';
    return apiRequest<{
      success: boolean;
      restored: number;
      message: string;
    }>(`/automation/catalog/restore-gone${query}`, {
      method: 'POST',
    });
  },
};
