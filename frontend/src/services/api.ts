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
    recommendation: "send" | "review" | "discard";
    dimensions: AnalysisDimensions;
    justification: string;
}

export interface AnalyzeRequest {
    project_ids?: string[];
    filters?: CatalogFilters;
    exclude_ids?: string[];
}

export interface BulkProposalCustomItem {
    workana_id: string;
    proposal_text: string;
    budget?: number | null;
    deadline_days?: number | null;
}

export interface ProposalBatchCreate {
    project_ids?: string[];
    filters?: CatalogFilters;
    exclude_ids?: string[];
    template_ref?: string;
    custom_proposals?: BulkProposalCustomItem[];
    daily_limit?: number;
}

export interface ProposalBatchItem {
    id: number;
    batch_id: number;
    workana_id: string;
    project_title?: string | null;
    project_url?: string | null;
    status: "queued" | "generating" | "ready" | "sending" | "sent" | "failed" | "skipped" | "cancelled";
    generated_message?: string | null;
    suggested_price?: string | null;
    budget?: number | null;
    deadline_days?: number | null;
    error?: string | null;
    attempts: number;
    created_at?: string | null;
    updated_at?: string | null;
    sent_at?: string | null;
}

export interface ProposalBatch {
    id: number;
    user_id: string;
    template_ref?: string | null;
    summary?: Record<string, unknown> | null;
    status: "queued" | "running" | "completed" | "cancelled" | "failed";
    total: number;
    sent_count: number;
    failed_count: number;
    skipped_count: number;
    daily_limit?: number | null;
    error?: string | null;
    created_at?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    items?: ProposalBatchItem[];
}

export interface ProposalBatchList {
    batches: ProposalBatch[];
    total: number;
}

export interface BulkGenerateItemResult {
    workana_id: string;
    title: string;
    url: string;
    success: boolean;
    proposal: string;
    suggested_price: string;
    suggested_budget?: number | null;
    suggested_deadline_days: number;
    error?: string | null;
}

export interface BulkGenerateResponse {
    success: boolean;
    results: BulkGenerateItemResult[];
    total: number;
    generated: number;
    failed: number;
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

    async getCatalogProjects(params: CatalogFilters & {
        page?: number;
        limit?: number;
        sort?: string;
    }) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== "") {
                query.set(key, String(value));
            }
        });
        return this.request<{
            projects: CatalogProject[];
            total: number;
            page: number;
            limit: number;
        }>(`/projects?${query.toString()}`);
    }

    async getBidsHistory(workanaId: string, limit = 30) {
        return this.request<BidsHistoryResponse>(
            `/projects/${encodeURIComponent(workanaId)}/bids-history?limit=${limit}`
        );
    }

    async downloadCatalogCsv(includeInactive = false) {
        const { data } = await supabase.auth.getSession();
        const token = data.session?.access_token;
        const query = new URLSearchParams({
            include_inactive: String(includeInactive),
        });
        const response = await fetch(
            `${this.baseUrl}/projects/export.csv?${query.toString()}`,
            {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            }
        );
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Erro no download" }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "catalog.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async bulkState(body: {
        action: "favorite" | "unfavorite" | "hide" | "restore";
        project_ids?: string[];
        filters?: CatalogFilters;
        exclude_ids?: string[];
    }) {
        return this.request<{ success: boolean; updated: number; total: number }>(
            "/projects/bulk-state",
            { method: "POST", body },
        );
    }

    async analyzeProjects(body: AnalyzeRequest) {
        return this.request<AnalysisResult[]>("/projects/analyze", {
            method: "POST",
            body,
        });
    }

    async setProjectState(
        workanaId: string,
        body: {
            action?: "favorite" | "unfavorite" | "hide" | "restore";
            notes?: string;
        },
    ) {
        return this.request<{ success: boolean; updated: number }>(
            `/projects/${encodeURIComponent(workanaId)}/state`,
            { method: "POST", body },
        );
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

    // ==================== Lotes (Batches) ====================

    async createBatch(body: {
        project_ids?: string[];
        filters?: Record<string, any>;
        template_ref?: string | null;
        exclude_ids?: string[];
        summary?: Record<string, any>;
        daily_limit?: number;
    }) {
        return this.request<{
            success: boolean;
            batch_id: number;
            status: string;
            total: number;
            message: string;
        }>("/projects/batch", {
            method: "POST",
            body,
        });
    }

    async getBatches(status?: string, limit: number = 20) {
        const params = new URLSearchParams();
        if (status) params.set("status", status);
        params.set("limit", String(limit));
        return this.request<Array<{
            id: number;
            status: string;
            total: number;
            sent_count: number;
            failed_count: number;
            skipped_count: number;
            summary: Record<string, any>;
            template_ref: string | null;
            created_at: string;
            started_at: string;
            finished_at: string;
            error: string;
        }>>(`/projects/batches?${params.toString()}`);
    }

    async getBatchItems(batchId: number) {
        return this.request<Array<{
            id: number;
            workana_id: string;
            project_title: string;
            project_url: string;
            status: string;
            generated_message: string;
            suggested_price: string;
            budget: number;
            deadline_days: number;
            error: string;
            attempts: number;
            created_at: string;
            sent_at: string;
        }>>(`/projects/batches/${batchId}/items`);
    }

    async startBatch(batchId: number) {
        return this.request<{
            success: boolean;
            batch_id: number;
            status: string;
            message: string;
        }>(`/projects/batches/${batchId}/start`, {
            method: "POST",
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

    // ==================== Lotes de Proposta (Bulk & Batches) ====================

    async bulkGenerateProposals(projectIds: string[], templateRef?: string) {
        return this.request<BulkGenerateResponse>("/projects/bulk-generate-proposals", {
            method: "POST",
            body: {
                project_ids: projectIds,
                template_ref: templateRef,
            },
        });
    }

    async createProposalBatch(payload: ProposalBatchCreate) {
        return this.request<{
            success: boolean;
            batch_id: number;
            total: number;
            status: string;
            template_ref?: string;
        }>("/projects/batches", {
            method: "POST",
            body: payload,
        });
    }

    async listProposalBatches(limit: number = 20, offset: number = 0) {
        return this.request<ProposalBatchList>(`/projects/batches?limit=${limit}&offset=${offset}`);
    }

    async getProposalBatch(batchId: number) {
        return this.request<ProposalBatch>(`/projects/batches/${batchId}`);
    }

    async cancelProposalBatch(batchId: number) {
        return this.request<{ success: boolean; message: string }>(`/projects/batches/${batchId}/cancel`, {
            method: "POST",
        });
    }

    async retryProposalBatch(batchId: number) {
        return this.request<{ success: boolean; message: string }>(`/projects/batches/${batchId}/retry`, {
            method: "POST",
        });
    }

    async triggerBatchProcessingNow() {
        return this.request<{ success: boolean; processed: boolean }>("/projects/batches/process-now", {
            method: "POST",
        });
    }
}

// Instância singleton do serviço
export const api = new ApiService(API_BASE_URL);

