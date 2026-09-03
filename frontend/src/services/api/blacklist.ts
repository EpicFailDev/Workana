/**
 * Serviços de API para a Lista Negra de Clientes (Blacklist).
 */
import { apiRequest } from './client';

export interface BlacklistedClient {
  id: number;
  client_name: string;
  reason?: string | null;
  created_at: string;
}

export interface BlacklistResponse {
  clients: BlacklistedClient[];
  total: number;
}

export const blacklistApi = {
  async getBlacklistedClients() {
    return apiRequest<BlacklistResponse>('/blacklist');
  },

  async addToBlacklist(data: { client_name: string; reason?: string }) {
    return apiRequest<{ success: boolean; message: string }>('/blacklist', {
      method: 'POST',
      body: data,
    });
  },

  async removeFromBlacklist(clientId: number) {
    return apiRequest<{ success: boolean; message: string }>(`/blacklist/${clientId}`, {
      method: 'DELETE',
    });
  },

  async checkBlacklist(clientName: string) {
    return apiRequest<{ client_name: string; is_blacklisted: boolean }>(
      `/blacklist/check/${encodeURIComponent(clientName)}`
    );
  },
};
