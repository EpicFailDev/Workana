"use client";

import { useState } from "react";
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
    const [filters, setFilters] = useState<SearchFilters>({
        keywords: "",
        category: "",
        min_budget: "",
        max_budget: "",
        project_type: "any",
    });

    const [projects, setProjects] = useState<Project[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    const handleSearch = async () => {
        setIsSearching(true);
        setHasSearched(true);

        try {
            // Simular busca (em produção, chamar API real)
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Dados mock para demonstração
            setProjects([
                {
                    id: "123456",
                    title: "Desenvolvimento de Aplicativo Mobile React Native",
                    description: "Preciso de um desenvolvedor experiente para criar um aplicativo mobile usando React Native. O app deve ter integração com API REST, autenticação com Firebase, e suporte a notificações push...",
                    budget: "R$ 3.000 - R$ 5.000",
                    skills: ["React Native", "Firebase", "REST API", "TypeScript"],
                    proposals_count: 15,
                    posted_at: "Há 2 horas",
                    url: "https://workana.com/job/123456",
                },
                {
                    id: "123457",
                    title: "Sistema Web em Python/Django para E-commerce",
                    description: "Desenvolvimento de plataforma completa de e-commerce com painel administrativo, integração com meios de pagamento (PagSeguro, MercadoPago), gestão de estoque e relatórios...",
                    budget: "R$ 8.000 - R$ 15.000",
                    skills: ["Python", "Django", "PostgreSQL", "REST API"],
                    proposals_count: 23,
                    posted_at: "Há 5 horas",
                    url: "https://workana.com/job/123457",
                },
                {
                    id: "123458",
                    title: "Landing Page para Startup de Tecnologia",
                    description: "Criar uma landing page moderna e responsiva para nossa startup. Precisa ter animações suaves, formulário de contato, e otimização para SEO...",
                    budget: "R$ 500 - R$ 1.500",
                    skills: ["HTML", "CSS", "JavaScript", "Figma"],
                    proposals_count: 42,
                    posted_at: "Há 1 dia",
                    url: "https://workana.com/job/123458",
                },
            ]);
        } catch (error) {
            console.error("Erro na busca:", error);
        } finally {
            setIsSearching(false);
        }
    };

    const handleSendProposal = (projectId: string) => {
        // TODO: Abrir modal de envio de proposta
        console.log("Enviar proposta para:", projectId);
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
                </div>

                <div className={styles.filtersActions}>
                    <button className="btn btn-secondary">
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
        </div>
    );
}
