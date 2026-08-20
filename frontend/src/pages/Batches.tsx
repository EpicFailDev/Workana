import { useState, useEffect, useCallback } from "react";
import styles from "./Batches.module.css";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import Loader from "../components/Loader";
import CyberHeader from "../components/CyberHeader";

interface BatchItem {
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
}

interface Batch {
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
}

const STATUS_LABELS: Record<string, string> = {
    queued: "Em fila",
    running: "Processando",
    completed: "Concluído",
    cancelled: "Cancelado",
    failed: "Falhou",
};

const STATUS_COLORS: Record<string, string> = {
    queued: "var(--color-text-muted)",
    running: "var(--color-info)",
    completed: "var(--color-success)",
    cancelled: "var(--color-text-muted)",
    failed: "var(--color-error)",
};

export default function Batches() {
    const { toast } = useToast();
    const [batches, setBatches] = useState<Batch[]>([]);
    const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null);
    const [batchItems, setBatchItems] = useState<BatchItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingItems, setIsLoadingItems] = useState(false);
    const [statusFilter, setStatusFilter] = useState<string | null>(null);

    const fetchBatches = useCallback(async () => {
        try {
            const data = await api.getBatches(statusFilter || undefined, 50);
            setBatches(data);
        } catch (error) {
            console.error("Erro ao carregar lotes:", error);
            toast.error("Erro ao carregar lotes de propostas.");
        }
    }, [statusFilter, toast]);

    useEffect(() => {
        const load = async () => {
            setIsLoading(true);
            try {
                await fetchBatches();
            } finally {
                setIsLoading(false);
            }
        };
        load();
    }, [fetchBatches]);

    const handleSelectBatch = async (batch: Batch) => {
        setSelectedBatch(batch);
        setIsLoadingItems(true);
        try {
            const items = await api.getBatchItems(batch.id);
            setBatchItems(items);
        } catch (error) {
            console.error("Erro ao carregar itens:", error);
            toast.error("Erro ao carregar itens do lote.");
        } finally {
            setIsLoadingItems(false);
        }
    };

    const handleStartBatch = async (batchId: number) => {
        try {
            const result = await api.startBatch(batchId);
            if (result.success) {
                toast.success(`Lote ${batchId} iniciado: ${result.status}`);
                // Recarregar o lote selecionado se for o atual
                if (selectedBatch?.id === batchId) {
                    setSelectedBatch(prev => prev ? { ...prev, status: result.status } : null);
                }
                fetchBatches();
            }
        } catch (error: any) {
            toast.error(error.message || "Erro ao iniciar lote.");
        }
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return "—";
        const date = new Date(dateStr);
        return date.toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const formatCurrency = (value: number) => {
        return value.toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
        });
    };

    if (isLoading) {
        return (
            <div className={styles.container}>
                <CyberHeader
                    title="LOTES DE PROPOSTAS"
                    subtitle="AUTOMAÇÃO // BATCHES"
                    description="Gerencie envios em massa de propostas no Workana"
                />
                <Loader type="overlay" message="Carregando lotes..." />
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <CyberHeader
                title="LOTES DE PROPOSTAS"
                subtitle="AUTOMAÇÃO // BATCHES"
                description="Gerencie envios em massa de propostas no Workana"
            />

            {/* Filtros */}
            <div className={styles.toolbar}>
                <div className={styles.filterGroup}>
                    <label>Filtrar por status:</label>
                    <select
                        className={styles.select}
                        value={statusFilter || ""}
                        onChange={(e) => setStatusFilter(e.target.value || null)}
                    >
                        <option value="">Todos</option>
                        <option value="queued">Em fila</option>
                        <option value="running">Processando</option>
                        <option value="completed">Concluído</option>
                        <option value="failed">Falhou</option>
                        <option value="cancelled">Cancelado</option>
                    </select>
                </div>

                <button
                    className={styles.refreshButton}
                    onClick={fetchBatches}
                >
                    🔄 Atualizar
                </button>
            </div>

            {/* Lista de lotes */}
            {batches.length === 0 ? (
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>📦</div>
                    <h3>Nenhum lote encontrado</h3>
                    <p>Crie um lote a partir dos projetos da página de projetos.</p>
                </div>
            ) : (
                <div className={styles.batchList}>
                    {batches.map(batch => (
                        <div
                            key={batch.id}
                            className={`${styles.batchCard} ${selectedBatch?.id === batch.id ? styles.selected : ""}`}
                            onClick={() => handleSelectBatch(batch)}
                        >
                            <div className={styles.batchHeader}>
                                <div className={styles.batchId}>
                                    <span className={styles.batchIcon}>📦</span>
                                    <span className={styles.batchLabel}>Lote #{batch.id}</span>
                                </div>
                                <span
                                    className={styles.batchStatus}
                                    style={{ color: STATUS_COLORS[batch.status] }}
                                >
                                    {STATUS_LABELS[batch.status] || batch.status}
                                </span>
                            </div>

                            <div className={styles.batchBody}>
                                <div className={styles.batchStats}>
                                    <div className={styles.statItem}>
                                        <span className={styles.statValue}>{batch.total}</span>
                                        <span className={styles.statLabel}>Total</span>
                                    </div>
                                    <div className={styles.statItem}>
                                        <span className={styles.statValue}>{batch.sent_count}</span>
                                        <span className={styles.statLabel}>Enviados</span>
                                    </div>
                                    <div className={styles.statItem}>
                                        <span className={styles.statValue}>{batch.failed_count}</span>
                                        <span className={styles.statLabel}>Falhos</span>
                                    </div>
                                    <div className={styles.statItem}>
                                        <span className={styles.statValue}>{batch.skipped_count}</span>
                                        <span className={styles.statLabel}>Ignorados</span>
                                    </div>
                                </div>

                                <div className={styles.batchMeta}>
                                    <span>Criado: {formatDate(batch.created_at)}</span>
                                    {batch.started_at && (
                                        <span>Iniciado: {formatDate(batch.started_at)}</span>
                                    )}
                                    {batch.finished_at && (
                                        <span>Finalizado: {formatDate(batch.finished_at)}</span>
                                    )}
                                </div>

                                {batch.error && (
                                    <div className={styles.batchError}>
                                        Erro: {batch.error}
                                    </div>
                                )}

                                {batch.template_ref && (
                                    <div className={styles.batchTemplate}>
                                        Template: <code>{batch.template_ref}</code>
                                    </div>
                                )}
                            </div>

                            {batch.status === "queued" && (
                                <div className={styles.batchActions}>
                                    <button
                                        className={styles.startButton}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleStartBatch(batch.id);
                                        }}
                                    >
                                        ▶ Iniciar Processamento
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Detalhes do lote selecionado */}
            {selectedBatch && (
                <div className={styles.detailPanel}>
                    <div className={styles.detailHeader}>
                        <h3>Detalhes do Lote #{selectedBatch.id}</h3>
                        <button
                            className={styles.closeButton}
                            onClick={() => setSelectedBatch(null)}
                        >
                            ✕
                        </button>
                    </div>

                    <div className={styles.detailStatus}>
                        Status: <strong>{STATUS_LABELS[selectedBatch.status] || selectedBatch.status}</strong>
                    </div>

                    <div className={styles.detailStats}>
                        <div className={styles.detailStat}>
                            <span className={styles.detailStatValue}>{selectedBatch.total}</span>
                            <span className={styles.detailStatLabel}>Total de projetos</span>
                        </div>
                        <div className={styles.detailStat}>
                            <span className={styles.detailStatValue}>{selectedBatch.sent_count}</span>
                            <span className={styles.detailStatLabel}>Enviados com sucesso</span>
                        </div>
                        <div className={styles.detailStat}>
                            <span className={styles.detailStatValue}>{selectedBatch.failed_count}</span>
                            <span className={styles.detailStatLabel}>Falhos</span>
                        </div>
                        <div className={styles.detailStat}>
                            <span className={styles.detailStatValue}>{selectedBatch.skipped_count}</span>
                            <span className={styles.detailStatLabel}>Ignorados</span>
                        </div>
                    </div>

                    {selectedBatch.started_at && (
                        <div className={styles.detailMeta}>
                            <div><strong>Iniciado em:</strong> {formatDate(selectedBatch.started_at)}</div>
                        </div>
                    )}
                    {selectedBatch.finished_at && (
                        <div className={styles.detailMeta}>
                            <div><strong>Finalizado em:</strong> {formatDate(selectedBatch.finished_at)}</div>
                        </div>
                    )}

                    {selectedBatch.error && (
                        <div className={styles.detailError}>
                            <strong>Erro:</strong> {selectedBatch.error}
                        </div>
                    )}

                    {batchItems.length > 0 && (
                        <div className={styles.detailItems}>
                            <h4>Itens ({batchItems.length})</h4>
                            <div className={styles.itemsList}>
                                {batchItems.map(item => (
                                    <div key={item.id} className={styles.itemRow}>
                                        <div className={styles.itemInfo}>
                                            <span className={styles.itemWorkanaId}>{item.workana_id}</span>
                                            <span className={styles.itemTitle}>{item.project_title}</span>
                                        </div>
                                        <div className={styles.itemStatus}>
                                            <span className={`${styles.itemStatusBadge} ${styles[item.status]}`}>
                                                {item.status}
                                            </span>
                                            {item.status === "sent" && (
                                                <span className={styles.itemPrice}>
                                                    {formatCurrency(item.budget)} • {item.deadline_days}d
                                                </span>
                                            )}
                                            {item.status === "failed" && item.error && (
                                                <span className={styles.itemError}>{item.error}</span>
                                            )}
                                        </div>
                                        <div className={styles.itemMeta}>
                                            <span>{item.attempts}x tentativas</span>
                                            <span>{formatDate(item.created_at)}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {!isLoadingItems && batchItems.length === 0 && (
                        <div className={styles.noItems}>
                            Sem itens neste lote.
                        </div>
                    )}

                    {selectedBatch.status === "queued" && (
                        <button
                            className={styles.startButtonLarge}
                            onClick={() => handleStartBatch(selectedBatch.id)}
                        >
                            ▶ Iniciar Processamento
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
