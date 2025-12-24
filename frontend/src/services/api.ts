/**
 * Serviço de API para comunicação com o backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface RequestOptions {
    method?: "GET" | "POST" | "PUT" | "DELETE";
    body?: unknown;
    headers?: Record<string, string>;
}

class ApiService {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { method = "GET", body, headers = {} } = options;

        const config: RequestInit = {
            method,
            headers: {
                "Content-Type": "application/json",
                ...headers,
            },
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Erro desconhecido" }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    // ==================== Credenciais ====================

    async saveCredentials(email: string, password: string) {
        return this.request("/credentials", {
            method: "POST",
            body: { email, password },
        });
    }

    async getCredentialsStatus() {
        return this.request<{ configured: boolean; email: string | null }>("/credentials/status");
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

    async login() {
        return this.request("/automation/login", { method: "POST" });
    }

    async logout() {
        return this.request("/automation/logout", { method: "POST" });
    }

    async updateAutomationConfig(config: {
        headless: boolean;
        delay_between_actions_ms: number;
        max_proposals_per_day: number;
        auto_apply: boolean;
    }) {
        return this.request("/automation/config", {
            method: "PUT",
            body: config,
        });
    }

    // ==================== Projetos ====================

    async searchProjects(filters: {
        keywords?: string;
        category?: string;
        min_budget?: number;
        max_budget?: number;
        project_type?: string;
        max_results?: number;
        page?: number;
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
        return this.request<Array<{
            id: number;
            name: string;
            content: string;
            default_budget: number | null;
            default_deadline_days: number | null;
            is_default: boolean;
        }>>("/templates");
    }

    async createTemplate(template: {
        name: string;
        content: string;
        default_budget?: number;
        default_deadline_days?: number;
        is_default?: boolean;
    }) {
        return this.request("/templates", {
            method: "POST",
            body: template,
        });
    }

    async updateTemplate(templateId: number, template: {
        name: string;
        content: string;
        default_budget?: number;
        default_deadline_days?: number;
        is_default?: boolean;
    }) {
        return this.request(`/templates/${templateId}`, {
            method: "PUT",
            body: template,
        });
    }

    async deleteTemplate(templateId: number) {
        return this.request(`/templates/${templateId}`, { method: "DELETE" });
    }

    // ==================== Propostas ====================

    async sendProposal(proposal: {
        project_id: string;
        template_id?: number;
        custom_message?: string;
        budget: number;
        deadline_days: number;
    }) {
        return this.request<{
            success: boolean;
            message: string;
            project_id: string;
            proposal_id?: string;
        }>("/proposals/send", {
            method: "POST",
            body: proposal,
        });
    }

    async getProposalHistory(limit: number = 50) {
        return this.request<Array<{
            id: number;
            project_id: string;
            project_title: string;
            budget: number;
            deadline_days: number;
            status: string;
            sent_at: string;
        }>>(`/proposals/history?limit=${limit}`);
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
}

// Instância singleton do serviço
export const api = new ApiService(API_BASE_URL);
