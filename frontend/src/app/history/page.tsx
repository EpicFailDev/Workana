
"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";

interface ProposalHistory {
    id: number;
    project_id: string;
    project_title: string;
    budget: number;
    deadline_days: number;
    status: "sent" | "viewed" | "accepted" | "rejected";
    sent_at: string;
}

const statusLabels: Record<string, { label: string; class: string }> = {
    sent: { label: "Enviada", class: "badge-neutral" },
    viewed: { label: "Visualizada", class: "badge-info" },
    accepted: { label: "Aceita", class: "badge-success" },
    rejected: { label: "Rejeitada", class: "badge-error" },
};

export default function HistoryPage() {
    const [history, setHistory] = useState<ProposalHistory[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState<string>("all");

    const API_BASE = "http://localhost:8000/api";

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const response = await fetch(`${API_BASE}/proposals/history?limit=100`);
            if (response.ok) {
                const data = await response.json();
                setHistory(data);
            }
        } catch (error) {
            console.error("Erro ao carregar histórico:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredHistory = filter === "all"
        ? history
        : history.filter(h => h.status === filter);

    const formatDate = (dateString: string) => {
        if (!dateString) return "-";
        const date = new Date(dateString);
        return date.toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
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
            <div className={styles.loadingContainer}>
                <div className="spinner spinner-lg"></div>
                <p className="mt-md text-muted">Carregando histórico...</p>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className="page-header">
                <h1 className="page-title">
                    <span className="text-gradient">Histórico de Propostas</span>
                </h1>
                <p className="page-subtitle">
                    Acompanhe todas as propostas que você enviou
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4">
                <div className="stat-card" style={{ '--stat-color': 'var(--gradient-primary)' } as React.CSSProperties}>
                    <div className="stat-value text-gradient">{history.length}</div>
                    <div className="stat-label">Total Enviadas</div>
                </div>

                <div className="stat-card" style={{ '--stat-color': 'var(--gradient-success)' } as React.CSSProperties}>
                    <div className="stat-value" style={{ color: 'var(--color-success)' }}>
                        {history.filter(h => h.status === "accepted").length}
                    </div>
                    <div className="stat-label">Aceitas</div>
                </div>

                <div className="stat-card" style={{ '--stat-color': 'var(--gradient-secondary)' } as React.CSSProperties}>
                    <div className="stat-value" style={{ color: 'var(--color-secondary)' }}>
                        {history.filter(h => h.status === "viewed").length}
                    </div>
                    <div className="stat-label">Visualizadas</div>
                </div>

                <div className="stat-card" style={{ '--stat-color': 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)' } as React.CSSProperties}>
                    <div className="stat-value" style={{ color: 'var(--color-text-secondary)' }}>
                        {history.filter(h => h.status === "sent").length}
                    </div>
                    <div className="stat-label">Aguardando</div>
                </div>
            </div>

            {/* Filters */}
            <div className={`card ${styles.filtersCard}`}>
                <div className={styles.filterTabs}>
                    <button
                        className={`${styles.filterTab} ${filter === "all" ? styles.active : ""}`}
                        onClick={() => setFilter("all")}
                    >
                        Todas
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === "sent" ? styles.active : ""}`}
                        onClick={() => setFilter("sent")}
                    >
                        Enviadas
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === "viewed" ? styles.active : ""}`}
                        onClick={() => setFilter("viewed")}
                    >
                        Visualizadas
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === "accepted" ? styles.active : ""}`}
                        onClick={() => setFilter("accepted")}
                    >
                        Aceitas
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === "rejected" ? styles.active : ""}`}
                        onClick={() => setFilter("rejected")}
                    >
                        Rejeitadas
                    </button>
                </div>
            </div>

            {/* History Table */}
            {filteredHistory.length > 0 ? (
                <div className="table-container">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Projeto</th>
                                <th>Valor</th>
                                <th>Prazo</th>
                                <th>Status</th>
                                <th>Data</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredHistory.map((item) => (
                                <tr key={item.id}>
                                    <td>
                                        <div className={styles.projectCell}>
                                            <span className={styles.projectTitle}>{item.project_title}</span>
                                            <span className={styles.projectId}>ID: {item.project_id}</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className={styles.budget}>{formatCurrency(item.budget)}</span>
                                    </td>
                                    <td>{item.deadline_days} dias</td>
                                    <td>
                                        <span className={`badge ${statusLabels[item.status]?.class || 'badge-neutral'}`}>
                                            {statusLabels[item.status]?.label || item.status}
                                        </span>
                                    </td>
                                    <td className={styles.dateCell}>{formatDate(item.sent_at)}</td>
                                    <td>
                                        <div className={styles.actions}>
                                            <button className="btn btn-ghost btn-sm">
                                                <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                    <circle cx="12" cy="12" r="3" />
                                                </svg>
                                                Ver
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="card">
                    <div className="empty-state">
                        <svg className="empty-state-icon" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                            <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <h3 className="empty-state-title">Nenhuma proposta encontrada</h3>
                        <p className="empty-state-description">
                            {filter === "all"
                                ? "Você ainda não enviou nenhuma proposta."
                                : `Não há propostas com o status "${statusLabels[filter]?.label || filter}".`}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
