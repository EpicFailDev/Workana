"use client";

import { useState } from "react";
import Link from "next/link";
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

const mockFilters: SavedFilter[] = [
    {
        id: 1,
        name: "Desenvolvimento React",
        filters: {
            keywords: "React, Next.js, TypeScript",
            category: "it-programming",
            min_budget: 2000,
            project_type: "fixed",
        },
        created_at: "2024-12-20T10:00:00Z",
    },
    {
        id: 2,
        name: "Python Backend",
        filters: {
            keywords: "Python, Django, FastAPI",
            category: "it-programming",
            min_budget: 3000,
            max_budget: 15000,
        },
        created_at: "2024-12-18T14:30:00Z",
    },
    {
        id: 3,
        name: "Mobile Apps",
        filters: {
            keywords: "React Native, Flutter",
            min_budget: 5000,
        },
        created_at: "2024-12-15T09:00:00Z",
    },
];

export default function FiltersPage() {
    const [filters, setFilters] = useState<SavedFilter[]>(mockFilters);

    const handleDelete = (id: number) => {
        setFilters(filters.filter(f => f.id !== id));
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
                                        href={`/projects?filter=${filter.id}`}
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
