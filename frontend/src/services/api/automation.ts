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
  status:
    | 'healthy'
    | 'warning'
    | 'expired'
    | 'disconnected'
    | 'empty'
    | 'blocked_waf'
    | 'saved_offline'
    | 'potentially_expired';
  valid: boolean;
  health_score?: number;
  message: string;
  cookies_count: number;
  has_cloudflare_clearance: boolean;
  account_email?: string | null;
  latency_ms?: number | null;
  decay_hours_remaining?: number;
  http_status?: number;
  last_tested_at?: string;
}

export interface DiagnosticItem {
  id: string;
  name: string;
  status: 'ok' | 'warning' | 'error' | 'pending' | 'blocked';
  detail: string;
}

export interface SessionDiagnosticsResponse {
  overall: 'optimal' | 'degraded' | 'disconnected';
  diagnostics: DiagnosticItem[];
}

export interface LocalSessionDetectionResponse {
  detected: boolean;
  path: string | null;
  cookies_count: number;
  has_session_cookie: boolean;
  has_cloudflare_clearance: boolean;
  modified_at: string | null;
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

  async getSessionDiagnostics() {
    return apiRequest<SessionDiagnosticsResponse>('/automation/session/diagnostics');
  },

  async autoLogin(creds?: { email?: string; password?: string }) {
    return apiRequest<{
      success: boolean;
      message: string;
      cookies_count?: number;
      email?: string;
    }>('/automation/workana/auto-login', {
      method: 'POST',
      body: creds || {},
    });
  },

  async detectLocalSession() {
    return apiRequest<LocalSessionDetectionResponse>('/automation/workana/detect-local-session');
  },

  async syncLocalSession(path?: string) {
    return apiRequest<{
      success: boolean;
      message: string;
      cookies_count?: number;
    }>('/automation/workana/sync-local-session', {
      method: 'POST',
      body: { path },
    });
  },

  async cdpConnect(port: number = 9222) {
    return apiRequest<{
      success: boolean;
      message: string;
      cookies_count?: number;
      detail?: string;
    }>('/automation/workana/cdp-connect', {
      method: 'POST',
      body: { port },
    });
  },

  async getRealtimeStatus() {
    return apiRequest<RealtimeStatusResponse>('/automation/realtime-status');
  },

  async startRealtime() {
    return apiRequest<RealtimeStatusResponse>('/automation/realtime/start', {
      method: 'POST',
    });
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
