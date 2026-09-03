/**
 * Serviços de API para Lotes de Propostas (Batches).
 */
import { apiRequest } from './client';
import { CatalogFilters } from './projects';

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

export const batchesApi = {
    async createBatch(body: {
        project_ids?: string[];
        filters?: Record<string, any>;
        template_ref?: string | null;
        exclude_ids?: string[];
        summary?: Record<string, any>;
        daily_limit?: number;
    }) {
        return apiRequest<{
            success: boolean;
            batch_id: number;
            status: string;
            total: number;
            message: string;
        }>("/projects/batch", {
            method: "POST",
            body,
        });
    },

    async getBatches(status?: string, limit: number = 20) {
        const params = new URLSearchParams();
        if (status) params.set("status", status);
        params.set("limit", String(limit));
        return apiRequest<Array<{
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
    },

    async getBatchItems(batchId: number) {
        return apiRequest<Array<{
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
    },

    async startBatch(batchId: number) {
        return apiRequest<{
            success: boolean;
            batch_id: number;
            status: string;
            message: string;
        }>(`/projects/batches/${batchId}/start`, {
            method: "POST",
        });
    },

    async bulkGenerateProposals(projectIds: string[], templateRef?: string) {
        return apiRequest<BulkGenerateResponse>("/projects/bulk-generate-proposals", {
            method: "POST",
            body: {
                project_ids: projectIds,
                template_ref: templateRef,
            },
        });
    },

    async createProposalBatch(payload: ProposalBatchCreate) {
        return apiRequest<{
            success: boolean;
            batch_id: number;
            total: number;
            status: string;
            template_ref?: string;
        }>("/projects/batches", {
            method: "POST",
            body: payload,
        });
    },

    async listProposalBatches(limit: number = 20, offset: number = 0) {
        return apiRequest<ProposalBatchList>(`/projects/batches?limit=${limit}&offset=${offset}`);
    },

    async getProposalBatch(batchId: number) {
        return apiRequest<ProposalBatch>(`/projects/batches/${batchId}`);
    },

    async cancelProposalBatch(batchId: number) {
        return apiRequest<{ success: boolean; message: string }>(`/projects/batches/${batchId}/cancel`, {
            method: "POST",
        });
    },

    async retryProposalBatch(batchId: number) {
        return apiRequest<{ success: boolean; message: string }>(`/projects/batches/${batchId}/retry`, {
            method: "POST",
        });
    },

    async triggerBatchProcessingNow() {
        return apiRequest<{ success: boolean; processed: boolean }>("/projects/batches/process-now", {
            method: "POST",
        });
    },

    async updateBatchItem(itemId: number, data: {
        generated_message?: string;
        budget?: number | null;
        deadline_days?: number | null;
        status?: string;
    }) {
        return apiRequest<{ success: boolean; item: ProposalBatchItem }>(`/projects/batches/items/${itemId}`, {
            method: "PUT",
            body: data,
        });
    },

    async deleteBatchItem(itemId: number) {
        return apiRequest<{ success: boolean; message: string }>(`/projects/batches/items/${itemId}`, {
            method: "DELETE",
        });
    },

    async sendBatchItemNow(itemId: number) {
        return apiRequest<{ success: boolean; message: string; proposal_id?: string }>(`/projects/batches/items/${itemId}/send-now`, {
            method: "POST",
        });
    },
};
