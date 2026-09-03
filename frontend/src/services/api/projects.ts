/**
 * Serviços de API para Projetos e Catálogo.
 */
import { apiRequest, API_BASE_URL } from './client';
import { supabase } from '../../integrations/supabase/client';

export interface CatalogProject {
  workana_id: string;
  title: string;
  description?: string | null;
  url: string;
  category?: string | null;
  subcategory?: string | null;
  budget_min?: number | null;
  budget_max?: number | null;
  budget_type?: string | null;
  deadline?: string | null;
  skills?: string[] | null;
  details?: Record<string, unknown>;
  client_name?: string | null;
  client_country?: string | null;
  client_rating?: number | null;
  client_projects_posted?: number | null;
  client_projects_paid?: number | null;
  client_member_since?: string | null;
  client_plan?: string | null;
  proposals_count?: number | null;
  payment_verified?: boolean | null;
  estimated_published_at?: string | null;
  proposals_delta?: number | null;
  contract_type?: string | null;
  posted_at?: string | null;
  published_at?: string | null;
  last_client_activity?: string | null;
  is_urgent?: boolean;
  is_featured?: boolean;
  is_favorite: boolean;
  is_hidden: boolean;
  notes?: string | null;
  analysis?: Record<string, unknown> | null;
  analyzed_at?: string | null;
  status?: string;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface CatalogFilters {
  q?: string;
  category?: string;
  min_budget?: number;
  max_budget?: number;
  payment_verified?: boolean;
  favorites_only?: boolean;
  hidden_only?: boolean;
}

export interface BidsHistoryPoint {
  proposals_count: number;
  captured_at: string;
}

export interface BidsHistoryResponse {
  workana_id: string;
  title?: string | null;
  current_count?: number | null;
  points: BidsHistoryPoint[];
}

export interface AnalysisDimensions {
  profile_fit: number;
  budget: number;
  competition: number;
  client_reliability: number;
  recency: number;
  risk: number;
}

export interface AnalysisResult {
  workana_id: string;
  score: number;
  recommendation: 'send' | 'review' | 'discard';
  dimensions: AnalysisDimensions;
  justification: string;
}

export interface AnalyzeRequest {
  project_ids?: string[];
  filters?: CatalogFilters;
  exclude_ids?: string[];
}

export interface InvestmentStage {
  title: string;
  description: string;
  percentage: number;
  amount: number;
  amount_formatted: string;
}

export interface InvestmentBreakdown {
  total_value: number;
  total_formatted: string;
  price_level: string;
  price_level_label: string;
  price_level_description: string;
  stages: InvestmentStage[];
  breakdown_text: string;
}

export interface ProposalVersion {
  id: number;
  project_id: string;
  project_title?: string;
  project_url?: string;
  proposal?: string;
  budget?: number;
  deadline_days?: number;
  status?: string;
  sent_at?: string;
  template_id?: any;
  template_slug?: string;
  template_type?: string;
  source?: string;
}

export const projectsApi = {
  async getCatalogProjects(
    params: CatalogFilters & {
      page?: number;
      limit?: number;
      sort?: string;
    }
  ) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.set(key, String(value));
      }
    });
    return apiRequest<{
      projects: CatalogProject[];
      total: number;
      page: number;
      limit: number;
    }>(`/projects?${query.toString()}`);
  },

  async getBidsHistory(workanaId: string, limit = 30) {
    return apiRequest<BidsHistoryResponse>(
      `/projects/${encodeURIComponent(workanaId)}/bids-history?limit=${limit}`
    );
  },

  async downloadCatalogCsv(includeInactive = false) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    const query = new URLSearchParams({
      include_inactive: String(includeInactive),
    });
    const response = await fetch(`${API_BASE_URL}/projects/export.csv?${query.toString()}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Erro no download' }));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'catalog.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  async bulkState(body: {
    action: 'favorite' | 'unfavorite' | 'hide' | 'restore';
    project_ids?: string[];
    filters?: CatalogFilters;
    exclude_ids?: string[];
  }) {
    return apiRequest<{ success: boolean; updated: number; total: number }>(
      '/projects/bulk-state',
      { method: 'POST', body }
    );
  },

  async analyzeProjects(body: AnalyzeRequest) {
    return apiRequest<AnalysisResult[]>('/projects/analyze', {
      method: 'POST',
      body,
    });
  },

  async setProjectState(
    workanaId: string,
    body: {
      action?: 'favorite' | 'unfavorite' | 'hide' | 'restore';
      notes?: string;
    }
  ) {
    return apiRequest<{ success: boolean; updated: number }>(
      `/projects/${encodeURIComponent(workanaId)}/state`,
      { method: 'POST', body }
    );
  },

  async getProjectDetails(projectId: string) {
    return apiRequest(`/projects/${projectId}`);
  },

  async getProjectProposal(projectId: string) {
    return apiRequest<{
      has_proposal: boolean;
      id?: number;
      project_id?: string;
      project_title?: string;
      project_url?: string;
      proposal?: string;
      budget?: number;
      deadline_days?: number;
      status?: string;
      sent_at?: string;
      template_id?: any;
      template_slug?: string;
      source?: string;
      versions?: ProposalVersion[];
      total_versions?: number;
    }>(`/projects/${encodeURIComponent(projectId)}/proposal`);
  },

  async getProjectVersions(projectId: string) {
    return apiRequest<{
      project_id: string;
      versions: ProposalVersion[];
      total: number;
    }>(`/projects/${encodeURIComponent(projectId)}/versions`);
  },

  async deleteProjectProposalVersion(projectId: string, proposalId: number) {
    return apiRequest<{
      success: boolean;
      message: string;
      versions: ProposalVersion[];
    }>(`/projects/${encodeURIComponent(projectId)}/proposals/${proposalId}`, {
      method: 'DELETE',
    });
  },

  async saveProjectProposal(
    projectId: string,
    data: {
      proposal_id?: number | null;
      proposal_text: string;
      budget?: number | null;
      deadline_days?: number | null;
      template_id?: any;
      force_new_version?: boolean;
      add_to_batch?: boolean;
    }
  ) {
    return apiRequest<{
      success: boolean;
      message: string;
      proposal_id?: number;
      batch_info?: any;
      versions?: ProposalVersion[];
    }>(`/projects/${encodeURIComponent(projectId)}/save-proposal`, {
      method: 'POST',
      body: data,
    });
  },

  async generateProposal(
    projectId: string,
    templateId?: any,
    forceRegenerate = false,
    priceLevel: 'budget' | 'standard' | 'premium' = 'standard',
    saveAsNewVersion = true
  ) {
    const query = templateId ? `?template_id=${encodeURIComponent(templateId)}` : '';
    return apiRequest<{
      success: boolean;
      proposal?: string;
      suggested_price?: string;
      suggested_deadline_days?: number;
      justification?: string;
      error?: string;
      template_id_used?: any;
      investment_breakdown?: InvestmentBreakdown;
      proposal_id?: number;
      versions?: ProposalVersion[];
    }>(`/projects/${encodeURIComponent(projectId)}/generate-proposal${query}`, {
      method: 'POST',
      body: {
        template_id: templateId || undefined,
        force_regenerate: forceRegenerate,
        price_level: priceLevel,
        save_as_new_version: saveAsNewVersion,
      },
    });
  },

  async submitProposal(
    projectId: string,
    proposalData: {
      project_id: string;
      custom_message: string;
      budget: number;
      deadline_days: number;
      template_id?: any;
    }
  ) {
    return apiRequest<{
      success: boolean;
      message: string;
      project_id: string;
      proposal_id?: string;
    }>(`/projects/${encodeURIComponent(projectId)}/submit-proposal`, {
      method: 'POST',
      body: proposalData,
    });
  },

  async getAllProposals(params?: { status?: string; q?: string; limit?: number; offset?: number }) {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.q) query.set('q', params.q);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return apiRequest<{
      proposals: Array<{
        id: number;
        project_id: string;
        project_title: string;
        project_url?: string;
        message?: string;
        budget: number;
        deadline_days: number;
        status: string;
        sent_at?: string;
        template_id?: any;
        template_slug?: string;
        template_type?: string;
      }>;
      total: number;
      limit: number;
      offset: number;
    }>(`/projects/all-proposals?${query.toString()}`);
  },

  async getProposalHistory() {
    return apiRequest<
      Array<{
        id: number;
        project_id: string;
        project_title: string;
        budget: number;
        deadline_days: number;
        status: 'generated' | 'sent' | 'viewed' | 'accepted' | 'rejected';
        sent_at: string;
      }>
    >('/proposals/history');
  },

  async updateProposalStatus(proposalId: number, status: string) {
    return apiRequest<{ success: boolean; message: string }>(`/proposals/${proposalId}/status`, {
      method: 'PUT',
      body: { status },
    });
  },

  async deleteProposal(proposalId: number) {
    return apiRequest<{ success: boolean; message: string }>(`/proposals/${proposalId}`, {
      method: 'DELETE',
    });
  },
};
