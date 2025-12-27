"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "../../services/api";
import styles from "./page.module.css";

interface SavedFilter {
    id: number;
    name: string;
    filters: {
        keywords?: string;
        category?: string;
        min_budget?: number;
        max_budget?: number;
        project_type?: string;
    };
    created_at: string;
}


export default function FiltersPage() {
    const [filters, setFilters] = useState<SavedFilter[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadFilters();
    }, []);

    const loadFilters = async () => {
        try {
            const data = await api.getSavedFilters();
            // @ts-ignore - Adapter simples pois a API retorna any
            setFilters(data);
        } catch (error) {
            console.error("Erro ao carregar filtros:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Tem certeza que deseja excluir este filtro?")) return;

        try {
            await api.deleteFilter(id);
            setFilters(filters.filter(f => f.id !== id));
        } catch (error) {
            console.error("Erro ao excluir filtro:", error);
            alert("Erro ao excluir filtro.");
        }
    };

    const getFilterUrl = (filterData: any) => {
        const params = new URLSearchParams();
        if (filterData.keywords) params.append("keywords", filterData.keywords);
        if (filterData.category) params.append("category", filterData.category);
        if (filterData.min_budget) params.append("min_budget", String(filterData.min_budget));
        if (filterData.max_budget) params.append("max_budget", String(filterData.max_budget));
        if (filterData.project_type) params.append("project_type", filterData.project_type);
        if (filterData.sort && filterData.sort !== "relevance") params.append("sort", filterData.sort);

        return `/projects?${params.toString()}`;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("pt-BR");
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className="page-header">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="page-title">
                            <span className="text-gradient">Filtros Salvos</span>
                        </h1>
                        <p className="page-subtitle">
                            Reutilize seus filtros de busca favoritos
                        </p>
                    </div>
                    <Link href="/projects" className="btn btn-primary">
                        <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 5v14M5 12h14" />
                        </svg>
                        Novo Filtro
                    </Link>
                </div>
            </div>

            {/* Filters List */}
            {filters.length > 0 ? (
                <div className={styles.filtersList}>
                    {filters.map((filter) => (
                        <div key={filter.id} className={`card ${styles.filterCard}`}>
                            <div className={styles.filterHeader}>
                                <div>
                                    <h3 className={styles.filterName}>{filter.name}</h3>
                                    <span className={styles.filterDate}>Criado em {formatDate(filter.created_at)}</span>
                                </div>
                                <div className={styles.filterActions}>
                                    <Link
                                        href={getFilterUrl(filter.filters)}
                                        className="btn btn-primary btn-sm"
                                    >
                                        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="11" cy="11" r="8" />
                                            <path d="M21 21l-4.35-4.35" />
                                        </svg>
                                        Usar Filtro
                                    </Link>
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => handleDelete(filter.id)}
                                        style={{ color: 'var(--color-error)' }}
                                    >
                                        <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <div className={styles.filterDetails}>
                                {filter.filters.keywords && (
                                    <div className={styles.filterDetail}>
                                        <span className={styles.detailLabel}>Palavras-chave:</span>
                                        <span>{filter.filters.keywords}</span>
                                    </div>
                                )}
                                {filter.filters.category && (
                                    <div className={styles.filterDetail}>
                                        <span className={styles.detailLabel}>Categoria:</span>
                                        <span>{filter.filters.category}</span>
                                    </div>
                                )}
                                {(filter.filters.min_budget || filter.filters.max_budget) && (
                                    <div className={styles.filterDetail}>
                                        <span className={styles.detailLabel}>Orçamento:</span>
                                        <span>
                                            {filter.filters.min_budget && `R$ ${filter.filters.min_budget.toLocaleString()}`}
                                            {filter.filters.min_budget && filter.filters.max_budget && " - "}
                                            {filter.filters.max_budget && `R$ ${filter.filters.max_budget.toLocaleString()}`}
                                        </span>
                                    </div>
                                )}
                                {filter.filters.project_type && (
                                    <div className={styles.filterDetail}>
                                        <span className={styles.detailLabel}>Tipo:</span>
                                        <span>{filter.filters.project_type === "fixed" ? "Preço Fixo" : "Por Hora"}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card">
                    <div className="empty-state">
                        <svg className="empty-state-icon" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                        </svg>
                        <h3 className="empty-state-title">Nenhum filtro salvo</h3>
                        <p className="empty-state-description">
                            Salve seus filtros de busca na página de Projetos para reutilizá-los depois
                        </p>
                        <Link href="/projects" className="btn btn-primary mt-lg">
                            Ir para Busca de Projetos
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}
