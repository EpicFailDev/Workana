/**
 * Serviço de API para comunicação com o backend.
 */
import { supabase } from '../integrations/supabase/client';

// Garante que a URL base sempre termine com /api
const rawBaseUrl = import.meta.env.VITE_API_URL || "";
const API_BASE_URL = rawBaseUrl 
    ? (rawBaseUrl.endsWith("/api") ? rawBaseUrl : `${rawBaseUrl}/api`)
    : "/api";

interface RequestOptions {
    method?: "GET" | "POST" | "PUT" | "DELETE";
    body?: unknown;
    headers?: Record<string, string>;
}

export type BlockType = 
    | "abertura" 
    | "tom_de_voz" 
    | "entendimento_projeto" 
    | "solucao" 
    | "experiencia" 
    | "entregas" 
    | "diferenciais" 
    | "preco_prazo" 
    | "cta" 
    | "assinatura" 
    | "instrucao_personalizada";

export type BlockMode = "literal" | "instruction";

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

class ApiService {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { method = "GET", body, headers = {} } = options;

        // Obter token de acesso do Supabase
        const { data } = await supabase.auth.getSession();
        const token = data.session?.access_token;

        const config: RequestInit = {
            method,
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {}),
                ...headers,
            },
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, config);

        if (response.status === 401) {
            // Token inválido/expirado -> limpa sessão local e redireciona para login
            await supabase.auth.signOut();
            window.location.href = "/auth/login";
            throw new Error("Sessão expirada. Faça login novamente.");
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Erro desconhecido" }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    // ==================== Automação ====================

    async getAutomationStatus() {
        return this.request<{
            is_running: boolean;
            is_logged_in: boolean;
            current_action: string | null;
            proposals_sent_today: number;
            max_proposals_per_day: number;
            last_error: string | null;
        }>("/automation/status");
    }

    async getAutomationConfig() {
        return this.request<{
            headless: boolean;
            delay_between_actions_ms: number;
            max_proposals_per_day: number;
            auto_apply: boolean;
            preferred_template_id: number | null;
            gemini_api_key?: string;
            user_full_name?: string;
        }>("/automation/config");
    }

    async updateAutomationConfig(config: {
        headless: boolean;
        delay_between_actions_ms: number;
        max_proposals_per_day: number;
        auto_apply: boolean;
        gemini_api_key?: string;
        user_full_name?: string;
    }) {
        return this.request("/automation/config", {
            method: "PUT",
            body: config,
        });
    }

    async getCredentialsStatus() {
        return this.request<{
            configured: boolean;
            email: string | null;
        }>("/automation/credentials");
    }

    async updateCredentials(creds: { email: string; password: string }) {
        return this.request("/automation/credentials", {
            method: "POST",
            body: creds,
        });
    }

    // ==================== Projetos ====================

    async searchProjects(filters: {
        keywords?: string;
        category?: string;
        min_budget?: number;
        max_budget?: number;
        project_type?: string;
        sort?: string;
        max_results?: number;
        page?: number;
        pages_to_fetch?: number;
        publication?: string; // e.g. '1d', '3d'
        language?: string;    // e.g. 'pt', 'en'
        proposals?: string;   // e.g. 'less_than_5', '5_plus'
        payment_verified?: boolean;
    }) {
        return this.request<{
            projects: Array<{
                id: string;
                title: string;
                description: string;
                budget: string | null;
                skills: string[];
                proposals_count: number | null;
                posted_at: string | null;
                url: string;
            }>;
            total: number;
        }>("/projects/search", {
            method: "POST",
            body: filters,
        });
    }

    async getProjectDetails(projectId: string) {
        return this.request(`/projects/${projectId}`);
    }

    async generateProposal(projectId: string, templateId?: any) {
        const query = templateId ? `?template_id=${encodeURIComponent(templateId)}` : "";
        return this.request<{
            success: boolean;
            proposal?: string;
            suggested_price?: string;
            justification?: string;
            error?: string;
        }>(`/projects/${projectId}/generate-proposal${query}`, {
            method: "POST",
        });
    }

    async submitProposal(projectId: string, proposalData: {
        project_id: string;
        custom_message: string;
        budget: number;
        deadline_days: number;
        template_id?: any;
    }) {
        return this.request<{
            success: boolean;
            message: string;
            project_id: string;
            proposal_id?: string;
        }>(`/projects/${projectId}/submit-proposal`, {
            method: "POST",
            body: proposalData,
        });
    }

    async getProposalHistory() {
        return this.request<Array<{
            id: number;
            project_id: string;
            project_title: string;
            budget: number;
            deadline_days: number;
            status: "generated" | "sent" | "viewed" | "accepted" | "rejected";
            sent_at: string;
        }>>("/proposals/history");
    }

    async updateProposalStatus(proposalId: number, status: string) {
        return this.request<{ success: boolean; message: string }>(`/proposals/${proposalId}/status`, {
            method: "PUT",
            body: { status }
        });
    }

    // ==================== Filtros ====================

    async getSavedFilters() {
        return this.request<Array<{
            id: number;
            name: string;
            filters: Record<string, unknown>;
            created_at: string;
        }>>("/filters");
    }

    async createFilter(name: string, filters: Record<string, unknown>) {
        return this.request("/filters", {
            method: "POST",
            body: { name, filters },
        });
    }

    async deleteFilter(filterId: number) {
        return this.request(`/filters/${filterId}`, { method: "DELETE" });
    }

    // ==================== Templates ====================

    async getTemplates() {
        return this.request<ProposalTemplate[]>("/templates");
    }

    async createTemplate(template: ProposalTemplateCreate) {
        return this.request<ProposalTemplate>("/templates", {
            method: "POST",
            body: template,
        });
    }

    async updateTemplate(templateId: number, template: ProposalTemplateCreate) {
        return this.request<ProposalTemplate>(`/templates/${templateId}`, {
            method: "PUT",
            body: template,
        });
    }

    async deleteTemplate(templateId: number) {
        return this.request<{ success: boolean; message: string }>(`/templates/${templateId}`, { method: "DELETE" });
    }

    async duplicateTemplate(slug: string) {
        return this.request<ProposalTemplate>(`/templates/duplicate/${slug}`, {
            method: "POST"
        });
    }

    async testBlueprint(payload: {
        blueprint: TemplateBlock[];
        project?: Record<string, any> | null;
        run_ai?: boolean;
    }) {
        return this.request<{
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
        }>("/templates/test-blueprint", {
            method: "POST",
            body: payload,
        });
    }

    // ==================== Dashboard ====================

    async getDashboardStats() {
        return this.request<{
            total_proposals_sent: number;
            proposals_today: number;
            proposals_this_week: number;
            proposals_this_month: number;
            response_rate: number;
            accepted_proposals: number;
            pending_proposals: number;
            last_activity: string | null;
        }>("/dashboard/stats");
    }

    // ==================== Perfil Público ====================

    async getProfileMetrics() {
        return this.request<{
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
        }>("/profile/metrics");
    }

    async syncProfileMetrics(force: boolean = false) {
        return this.request<{
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
        }>(`/profile/sync?force=${force}`, { method: "POST" });
    }

    async getProfileConfig() {
        return this.request<{
            profile_url: string | null;
            auto_sync_enabled: boolean;
            sync_interval_hours: number;
            last_sync_at: string | null;
            is_configured: boolean;
        }>("/profile/config");
    }

    async updateProfileConfig(config: {
        profile_url: string;
        auto_sync_enabled?: boolean;
        sync_interval_hours?: number;
    }) {
        return this.request<{ success: boolean; message: string }>("/profile/config", {
            method: "PUT",
            body: config,
        });
    }

    async validateProfileUrl(url: string) {
        return this.request<{
            valid: boolean;
            display_name?: string;
            username?: string;
            error?: string;
        }>(`/profile/validate?url=${encodeURIComponent(url)}`, { method: "POST" });
    }
}

// Instância singleton do serviço
export const api = new ApiService(API_BASE_URL);

