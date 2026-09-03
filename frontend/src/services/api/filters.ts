/**
 * Serviços de API para Filtros Salvos.
 */
import { apiRequest } from './client';

export interface SavedFilter {
  id: number;
  name: string;
  filters: Record<string, unknown>;
  created_at: string;
}

export const filtersApi = {
  async getSavedFilters() {
    return apiRequest<SavedFilter[]>('/filters');
  },

  async createFilter(name: string, filters: Record<string, unknown>) {
    return apiRequest<SavedFilter>('/filters', {
      method: 'POST',
      body: { name, filters },
    });
  },

  async deleteFilter(filterId: number) {
    return apiRequest(`/filters/${filterId}`, { method: 'DELETE' });
  },
};
