"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "../../services/api";
import styles from "./page.module.css";

interface Project {
    id: string;
    title: string;
    description: string;
    budget: string | null;
    skills: string[];
    proposals_count: number | null;
    posted_at: string | null;
    url: string;
}

interface SearchFilters {
    keywords: string;
    category: string;
    min_budget: string;
    max_budget: string;
    project_type: string;
    sort: string;
}

const categories = [
    { value: "", label: "Todas as categorias" },
    { value: "it-programming", label: "TI & Programação" },
    { value: "design-multimedia", label: "Design & Multimídia" },
    { value: "writing-translation", label: "Escrita & Tradução" },
    { value: "marketing-sales", label: "Marketing & Vendas" },
    { value: "admin-support", label: "Administrativo & Suporte" },
    { value: "finance-legal", label: "Finanças & Jurídico" },
    { value: "engineering", label: "Engenharia & Arquitetura" },
];

export default function ProjectsPage() {
    const searchParams = useSearchParams();

    const [filters, setFilters] = useState<SearchFilters>({
        keywords: searchParams.get("keywords") || "",
        category: searchParams.get("category") || "",
        min_budget: searchParams.get("min_budget") || "",
        max_budget: searchParams.get("max_budget") || "",
        project_type: searchParams.get("project_type") || "any",
        sort: searchParams.get("sort") || "relevance",
    });

    const [projects, setProjects] = useState<Project[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);

    // Estado para salvar filtro
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [newFilterName, setNewFilterName] = useState("");
    const [isSavingFilter, setIsSavingFilter] = useState(false);

    // Efeito para buscar automaticamente se houver filtros na URL
    useEffect(() => {
        const hasParams = Array.from(searchParams.keys()).length > 0;
        if (hasParams && !hasSearched) {
            executeSearch(1, false);
        }
    }, [searchParams]);

    const executeSearch = async (pageNum: number, append: boolean = false) => {
        const loadingState = append ? setIsLoadingMore : setIsSearching;
        loadingState(true);

        try {
            const result = await api.searchProjects({
                keywords: filters.keywords,
                category: filters.category,
                min_budget: filters.min_budget ? Number(filters.min_budget) : undefined,
                max_budget: filters.max_budget ? Number(filters.max_budget) : undefined,
                project_type: filters.project_type !== "any" ? filters.project_type : undefined,
                sort: filters.sort,
                page: pageNum,
            });

            if (append) {
                setProjects(prev => [...prev, ...result.projects]);
            } else {
                setProjects(result.projects);
            }

            setHasMore(result.projects.length > 0);

        } catch (error) {
            console.error("Erro na busca:", error);
            // alert("Erro ao buscar projetos. Verifique se a automação está conectada.");
        } finally {
            loadingState(false);
        }
    };

    const handleSearch = () => {
        setHasSearched(true);
        setPage(1);
        setHasMore(true);
        executeSearch(1, false);
    };

    const handleLoadMore = () => {
        const nextPage = page + 1;
        setPage(nextPage);
        executeSearch(nextPage, true);
    };

    const handleSendProposal = (projectId: string) => {
        // TODO: Abrir modal de envio de proposta
        console.log("Enviar proposta para:", projectId);
    };

    const handleSaveFilter = async () => {
        if (!newFilterName.trim()) return;

        setIsSavingFilter(true);
        try {
            // Remove campos vazios
            const cleanFilters: Record<string, any> = {};
            if (filters.keywords) cleanFilters.keywords = filters.keywords;
            if (filters.category) cleanFilters.category = filters.category;
            if (filters.min_budget) cleanFilters.min_budget = Number(filters.min_budget);
            if (filters.max_budget) cleanFilters.max_budget = Number(filters.max_budget);
            if (filters.project_type && filters.project_type !== "any") cleanFilters.project_type = filters.project_type;
            if (filters.sort && filters.sort !== "relevance") cleanFilters.sort = filters.sort;

            await api.createFilter(newFilterName, cleanFilters);
            alert("Filtro salvo com sucesso!");
            setShowSaveModal(false);
            setNewFilterName("");
        } catch (error) {
            console.error("Erro ao salvar filtro:", error);
            alert("Erro ao salvar filtro.");
        } finally {
            setIsSavingFilter(false);
        }
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className="page-header">
                <h1 className="page-title">
                    <span className="text-gradient">Buscar Projetos</span>
                </h1>
                <p className="page-subtitle">
                    Encontre projetos que combinam com suas habilidades
                </p>
            </div>

            {/* Filtros */}
            <div className={`card ${styles.filtersCard}`}>
                <div className={styles.filtersGrid}>
                    <div className="form-group">
                        <label className="form-label">Palavras-chave</label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Ex: React, Python, WordPress..."
                            value={filters.keywords}
                            onChange={(e) => setFilters({ ...filters, keywords: e.target.value })}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Categoria</label>
                        <select
                            className="form-select"
                            value={filters.category}
                            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                        >
                            {categories.map((cat) => (
                                <option key={cat.value} value={cat.value}>
                                    {cat.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Orçamento Mínimo</label>
                        <input
                            type="number"
                            className="form-input"
                            placeholder="R$ 0"
                            value={filters.min_budget}
                            onChange={(e) => setFilters({ ...filters, min_budget: e.target.value })}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Orçamento Máximo</label>
                        <input
                            type="number"
                            className="form-input"
                            placeholder="R$ 50.000"
                            value={filters.max_budget}
                            onChange={(e) => setFilters({ ...filters, max_budget: e.target.value })}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Tipo de Projeto</label>
                        <select
                            className="form-select"
                            value={filters.project_type}
                            onChange={(e) => setFilters({ ...filters, project_type: e.target.value })}
                        >
                            <option value="any">Todos</option>
                            <option value="fixed">Preço Fixo</option>
                            <option value="hourly">Por Hora</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Ordenação</label>
                        <select
                            className="form-select"
                            value={filters.sort}
                            onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
                        >
                            <option value="relevance">Relevância</option>
                            <option value="created_at_desc">Mais Recentes</option>
                            <option value="created_at_asc">Mais Antigos</option>
                            <option value="budget_desc">Maior Valor</option>
                            <option value="budget_asc">Menor Valor</option>
                            <option value="bids_desc">Mais Propostas</option>
                            <option value="bids_asc">Menos Propostas</option>
                        </select>
                    </div>
                </div>

                <div className={styles.filtersActions}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => setShowSaveModal(true)}
                    >
                        <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                        </svg>
                        Salvar Filtro
                    </button>
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={handleSearch}
                        disabled={isSearching}
                    >
                        {isSearching ? (
                            <>
                                <span className="spinner"></span>
                                Buscando...
                            </>
                        ) : (
                            <>
                                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="11" cy="11" r="8" />
                                    <path d="M21 21l-4.35-4.35" />
                                </svg>
                                Buscar Projetos
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Resultados */}
            {isSearching ? (
                <div className={styles.loadingState}>
                    <div className="spinner spinner-lg"></div>
                    <p className="mt-md text-muted">Buscando projetos no Workana...</p>
                </div>
            ) : hasSearched && projects.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <svg className="empty-state-icon" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                            <path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                        </svg>
                        <h3 className="empty-state-title">Nenhum projeto encontrado</h3>
                        <p className="empty-state-description">
                            Tente ajustar seus filtros ou buscar por outras palavras-chave
                        </p>
                    </div>
                </div>
            ) : projects.length > 0 ? (
                <div className={styles.projectsContainer}>
                    <div className={styles.resultsHeader}>
                        <span>{projects.length} projetos encontrados</span>
                    </div>

                    <div className={styles.projectsList}>
                        {projects.map((project) => (
                            <div key={project.id} className={styles.projectCard}>
                                <div className={styles.projectHeader}>
                                    <h3 className={styles.projectTitle}>{project.title}</h3>
                                    <span className={styles.projectBudget}>{project.budget}</span>
                                </div>

                                <p className={styles.projectDescription}>{project.description}</p>

                                <div className={styles.projectSkills}>
                                    {project.skills.map((skill) => (
                                        <span key={skill} className="skill-tag">{skill}</span>
                                    ))}
                                </div>

                                <div className={styles.projectFooter}>
                                    <div className={styles.projectMeta}>
                                        <span>
                                            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                                                <circle cx="9" cy="7" r="4" />
                                            </svg>
                                            {project.proposals_count} propostas
                                        </span>
                                        <span>
                                            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                                                <circle cx="12" cy="12" r="10" />
                                                <polyline points="12 6 12 12 16 14" />
                                            </svg>
                                            {project.posted_at}
                                        </span>
                                    </div>

                                    <div className={styles.projectActions}>
                                        <a
                                            href={project.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn btn-ghost btn-sm"
                                        >
                                            Ver no Workana
                                        </a>
                                        <button
                                            className="btn btn-primary btn-sm"
                                            onClick={() => handleSendProposal(project.id)}
                                        >
                                            Enviar Proposta
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Botão Carregar Mais */}
                    {hasMore && (
                        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                            <button
                                className="btn btn-secondary btn-lg"
                                onClick={handleLoadMore}
                                disabled={isLoadingMore}
                            >
                                {isLoadingMore ? (
                                    <>
                                        <span className="spinner"></span>
                                        Carregando...
                                    </>
                                ) : (
                                    "Carregar Mais Projetos"
                                )}
                            </button>
                        </div>
                    )}
                </div>
            ) : (
                <div className="card">
                    <div className="empty-state">
                        <svg className="empty-state-icon" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                            <circle cx="11" cy="11" r="8" />
                            <path d="M21 21l-4.35-4.35" />
                        </svg>
                        <h3 className="empty-state-title">Comece sua busca</h3>
                        <p className="empty-state-description">
                            Configure os filtros acima e clique em &quot;Buscar Projetos&quot; para encontrar oportunidades
                        </p>
                    </div>
                </div>
            )}
            {/* Modal de Salvar Filtro */}
            {showSaveModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3 className="modal-title">Salvar Filtro</h3>
                            <button className="btn-close" onClick={() => setShowSaveModal(false)}>
                                <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="modal-body">
                            <p className="text-muted mb-md">Dê um nome para identificar este filtro depois (ex: Python Remoto)</p>
                            <div className="form-group">
                                <label className="form-label">Nome do Filtro</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={newFilterName}
                                    onChange={(e) => setNewFilterName(e.target.value)}
                                    placeholder="Ex: Projetos React"
                                    autoFocus
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button
                                className="btn btn-ghost"
                                onClick={() => setShowSaveModal(false)}
                                disabled={isSavingFilter}
                            >
                                Cancelar
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleSaveFilter}
                                disabled={!newFilterName.trim() || isSavingFilter}
                            >
                                {isSavingFilter ? "Salvando..." : "Salvar"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
