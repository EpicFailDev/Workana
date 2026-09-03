/**
 * Serviços de API para Templates e Blueprints.
 */
import { apiRequest } from './client';

export type BlockType =
  | 'abertura'
  | 'tom_de_voz'
  | 'entendimento_projeto'
  | 'solucao'
  | 'experiencia'
  | 'entregas'
  | 'diferenciais'
  | 'preco_prazo'
  | 'cta'
  | 'assinatura'
  | 'instrucao_personalizada';

export type BlockMode = 'literal' | 'instruction';

export interface TemplateBlock {
  id: string;
  type: BlockType;
  mode: BlockMode;
  enabled: boolean;
  content?: string | null;
  config?: Record<string, any> | null;
}

export interface ProposalTemplate {
  id: number | null;
  name: string;
  content: string;
  blueprint: TemplateBlock[];
  schema_version: number;
  default_budget: number | null;
  default_deadline_days: number | null;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
  template_ref?: string;
  is_system?: boolean;
  can_edit?: boolean;
  can_delete?: boolean;
  version?: number;
}

export interface ProposalTemplateCreate {
  name: string;
  content?: string | null;
  blueprint: TemplateBlock[];
  schema_version?: number;
  default_budget?: number | null;
  default_deadline_days?: number | null;
  is_default?: boolean;
}

export const templatesApi = {
  async getTemplates() {
    return apiRequest<ProposalTemplate[]>('/templates');
  },

  async createTemplate(template: ProposalTemplateCreate) {
    return apiRequest<ProposalTemplate>('/templates', {
      method: 'POST',
      body: template,
    });
  },

  async updateTemplate(templateId: number, template: ProposalTemplateCreate) {
    return apiRequest<ProposalTemplate>(`/templates/${templateId}`, {
      method: 'PUT',
      body: template,
    });
  },

  async deleteTemplate(templateId: number) {
    return apiRequest<{ success: boolean; message: string }>(`/templates/${templateId}`, {
      method: 'DELETE',
    });
  },

  async duplicateTemplate(slug: string) {
    return apiRequest<ProposalTemplate>(`/templates/duplicate/${slug}`, {
      method: 'POST',
    });
  },

  async testBlueprint(payload: {
    blueprint: TemplateBlock[];
    project?: Record<string, any> | null;
    run_ai?: boolean;
  }) {
    return apiRequest<{
      success: boolean;
      compiled_prompt: string;
      ai_result?: {
        success: boolean;
        proposal?: string;
        suggested_price?: string;
        justification?: string;
        error?: string;
      } | null;
      error?: string;
    }>('/templates/test-blueprint', {
      method: 'POST',
      body: payload,
    });
  },
};
