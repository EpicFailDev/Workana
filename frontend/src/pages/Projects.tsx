import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import styles from "./Projects.module.css";
import Loader from "../components/Loader";
import { useToast } from "../context/ToastContext";
import Skeleton from "../components/Skeleton";
import ProjectSkeleton, { ProjectSkeletonList } from "../components/ProjectSkeleton";
import CyberHeader from "../components/CyberHeader";

interface Project {
    id: string;
    title: string;
    description: string;
    budget: string | null;
    budget_min?: number | null;
    budget_max?: number | null;
    project_type?: string | null;
    category?: string | null;
    subcategory?: string | null;
    deadline?: string | null;
    details?: Record<string, string>;
    skills: string[];
    client_name?: string | null;
    client_country?: string | null;
    client_rating?: number | null;
    client_plan?: string | null;
    client_projects_posted?: number | null;
    client_projects_paid?: number | null;
    client_member_since?: string | null;
    proposals_count: number | null;
    posted_at: string | null;
    published_at?: string | null;
    payment_verified?: boolean | null;
    last_client_activity?: string | null;
    is_urgent?: boolean;
    is_featured?: boolean;
    url: string;
    match_score?: number | null;
}

interface SearchFilters {
    keywords: string;
    category: string;
    min_budget: string;
    max_budget: string;
    project_type: string;
    sort: string;
    publication: string;
    language: string;
    proposals: string;
    payment_verified: boolean;
    pages_to_fetch: number;
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

export default function Projects() {
    const { toast } = useToast();
    const [searchParams] = useSearchParams();

    // --- Persistence Logic Start ---
    // v2 invalida estados vazios gravados quando erros do backend eram tratados como resultado válido.
    const STORAGE_KEY = "workana_projects_cache_v2";

    const loadStateFromStorage = () => {
        try {
            const stored = sessionStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : null;
        } catch (e) {
            console.error("Failed to load state", e);
            return null;
        }
    };

    const savedState = loadStateFromStorage();
    const hasUrlParams = Array.from(searchParams.keys()).length > 0;

    // Se temos params na URL, eles tem prioridade sobre o cache.
    // Se não temos params, tentamos usar o cache, senão default.

    const initialFilters = (hasUrlParams || !savedState) ? {
        keywords: searchParams.get("keywords") || "",
        category: searchParams.get("category") || "",
        min_budget: searchParams.get("min_budget") || "",
        max_budget: searchParams.get("max_budget") || "",
        project_type: searchParams.get("project_type") || "any",
        sort: searchParams.get("sort") || "relevance",
        publication: searchParams.get("publication") || "any",
        language: searchParams.get("language") || "any",
        proposals: searchParams.get("proposals") || "any",
        payment_verified: searchParams.get("payment_verified") === "true",
        pages_to_fetch: Number(searchParams.get("pages_to_fetch")) || 10,
    } : savedState.filters;

    const [filters, setFilters] = useState<SearchFilters>(initialFilters);

    // Initial project state only from cache if no new URL params forced a refresh logic implicitly
    // Mas na verdade, se tem URL params, o useEffect vai disparar o search de qualquer jeito.
    const [projects, setProjects] = useState<Project[]>((!hasUrlParams && savedState) ? savedState.projects : []);
    
    // Recovery of other states
    const [isSearching, setIsSearching] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasSearched, setHasSearched] = useState((!hasUrlParams && savedState) ? savedState.hasSearched : false);
    const [page, setPage] = useState((!hasUrlParams && savedState) ? savedState.page : 1);
    const [hasMore, setHasMore] = useState((!hasUrlParams && savedState) ? savedState.hasMore : true);

    // Save state effect
    useEffect(() => {
        // Só salva se já tiver feito uma busca ou tiver filtros não vazios relevantes, 
        // pra não sujar o cache com estado inicial vazio sem querer.
        if (hasSearched || projects.length > 0) {
            const stateToSave = {
                filters,
                projects,
                hasSearched,
                page,
                hasMore
            };
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
        }
    }, [filters, projects, hasSearched, page, hasMore]);
    // --- Persistence Logic End ---

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

    // const PAGES_PER_BATCH = 10; // Removido em favor do filtro dinâmico

    // Função auxiliar para extrair valor numérico do orçamento
    const parseBudget = (budgetStr: string | null): number => {
        if (!budgetStr) return 0;
        // Remove tudo que não é dígito, ponto ou vírgula
        let cleanStr = budgetStr.replace(/[^0-9.,]/g, '');
        
        // Assumindo formato PT-BR (1.000,00) se tiver vírgula no final
        // Se tiver apenas ponto e for xxx.xxx, removemos o ponto (milhar)
        // Se for xxx.xx e parecer centavos (USD), mantemos.
        // Simplificação: Workana PT geralmente usa 1.000 ou 500.
        
        // Remover pontos de milhar (ex: 1.000 -> 1000)
        cleanStr = cleanStr.replace(/\./g, '');
        // Trocar vírgula por ponto (ex: 50,00 -> 50.00)
        cleanStr = cleanStr.replace(',', '.');
        
        // Pegar o primeiro número encontrado (mínimo do range)
        const match = cleanStr.match(/(\d+(\.\d+)?)/);
        return match ? parseFloat(match[0]) : 0;
    };

    // Função auxiliar para comparar datas relativas
    const parseRelativeDate = (dateStr: string | null): number => {
        if (!dateStr) return Infinity;
        const str = dateStr.toLowerCase().trim();
        
        // Termos imediatos
        if (str.includes("agora") || str.includes("segundo") || str.includes("second") || str.includes("new")) return 0;
        if (str.includes("ontem")) return 1440; // 24h * 60

        // Parse de números
        const numberMatch = str.match(/\d+/);
        const number = numberMatch ? parseInt(numberMatch[0]) : 1; 
        // Se não achar número mas tiver "uma hora", assume 1.

        let minutes = 0;
        
        if (str.includes("minuto") || str.includes("minute")) minutes = number;
        else if (str.includes("hora") || str.includes("hour")) minutes = number * 60;
        else if (str.includes("dia") || str.includes("day")) minutes = number * 1440;
        else if (str.includes("semana") || str.includes("week")) minutes = number * 10080;
        else if (str.includes("mês") || str.includes("mes") || str.includes("month")) minutes = number * 43200;
        else {
            // Tentar parsear data absoluta (ex: 28 de Dezembro)
            // Se falhar, joga pro final
            return 999999; 
        }

        return minutes;
    };

    const sortProjectsLocal = (currentProjects: Project[], sortOption: string) => {
        const sorted = [...currentProjects];
        
        switch (sortOption) {
            case "budget_desc":
                sorted.sort((a, b) => parseBudget(b.budget) - parseBudget(a.budget));
                break;
            case "budget_asc":
                sorted.sort((a, b) => {
                    const valA = parseBudget(a.budget);
                    const valB = parseBudget(b.budget);
                    // Se um for 0 (sem budget), joga pro final ou inicio?
                    // Geralmente quem quer menor valor quer ver os baratos, não os "sem valor defined".
                    if (valA === 0) return 1;
                    if (valB === 0) return -1;
                    return valA - valB;
                });
                break;
            case "created_at_desc": // Mais recentes (menor tempo relativo)
                sorted.sort((a, b) => parseRelativeDate(a.posted_at) - parseRelativeDate(b.posted_at));
                break;
            case "created_at_asc": // Mais antigos (maior tempo relativo)
                sorted.sort((a, b) => parseRelativeDate(b.posted_at) - parseRelativeDate(a.posted_at));
                break;
            case "bids_desc":
                sorted.sort((a, b) => (Number(b.proposals_count) || 0) - (Number(a.proposals_count) || 0));
                break;
            case "bids_asc":
                sorted.sort((a, b) => (Number(a.proposals_count) || 0) - (Number(b.proposals_count) || 0));
                break;
            case "relevance":
            default:
                // Se temos match_score vindo do backend, usamos ele (maior é melhor)
                // Se não, usamos o fallback local (menor é melhor)
                if (sorted.length > 0 && sorted[0].match_score !== undefined && sorted[0].match_score !== null) {
                    sorted.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
                    break;
                }
                // Relevância customizada: Combina Recência + Baixa Concorrência
                // Score = Minutos + (Propostas * 30)
                // Quanto menor o score, melhor (mais recente e menos propostas)
                sorted.sort((a, b) => {
                    const timeA = parseRelativeDate(a.posted_at);
                    const timeB = parseRelativeDate(b.posted_at);
                    const propsA = a.proposals_count || 0;
                    const propsB = b.proposals_count || 0;
                    
                    // Peso: 1 proposta equivale a 30 minutos de "velhice"
                    const scoreA = timeA + (propsA * 30);
                    const scoreB = timeB + (propsB * 30);
                    
                    return scoreA - scoreB;
                });
                break;
        }
        return sorted;
    };

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
                publication: filters.publication !== "any" ? filters.publication : undefined,
                language: filters.language !== "any" ? filters.language : undefined,
                proposals: filters.proposals !== "any" ? filters.proposals : undefined,
                payment_verified: filters.payment_verified ? true : undefined,
                page: pageNum,
                pages_to_fetch: filters.pages_to_fetch, 
            });

            if (append) {
                setProjects(prev => {
                    const combined = [...prev, ...result.projects];
                    // Remover duplicatas baseadas no ID
                    const unique = combined.filter((p, index, self) => 
                        index === self.findIndex((t) => t.id === p.id)
                    );
                    return sortProjectsLocal(unique, filters.sort);
                });
            } else {
                setProjects(sortProjectsLocal(result.projects, filters.sort));
            }

            // Se retornou menos projetos que o esperado, provavelmente não tem mais
            // (Assumindo média de 10 por página)
            setHasMore(result.projects.length >= (filters.pages_to_fetch * 5)); 

        } catch (error: any) {
            console.error("Erro na busca:", error);
            const message = error?.message || "Não foi possível buscar projetos agora.";
            toast.error(message);

            // Uma falha de rede/serviço não equivale a uma busca válida sem resultados.
            if (!append) {
                setHasSearched(false);
            }
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
        // Incrementa conforme a quantidade selecionada pelo usuário
        const nextPage = page + filters.pages_to_fetch;
        setPage(nextPage);
        executeSearch(nextPage, true);
    };

    // Estado para Mega Proposta IA
    const [showAiModal, setShowAiModal] = useState(false);
    const [aiProposal, setAiProposal] = useState<{
        proposal?: string;
        suggested_price?: string;
        justification?: string;
    } | null>(null);
    const [isGeneratingAi, setIsGeneratingAi] = useState(false);
    const [aiError, setAiError] = useState<string | null>(null);
    const [modalBudget, setModalBudget] = useState<string | number>("");
    const [modalDeadline, setModalDeadline] = useState<string | number>("");

    // Suporte a templates na geração manual
    const [templates, setTemplates] = useState<any[]>([]);
    const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
    const [currentGeneratingProjectId, setCurrentGeneratingProjectId] = useState<string | null>(null);

    useEffect(() => {
        const loadTemplates = async () => {
            try {
                const res = await api.getTemplates();
                setTemplates(res);
                
                const sessionTemplateId = sessionStorage.getItem("preferred_generation_template_id");
                const defaultTpl = res.find((t: any) => t.is_default);
                
                if (sessionTemplateId) {
                    const exists = res.some((t: any) => t.template_ref === sessionTemplateId);
                    if (exists) {
                        setSelectedTemplateId(sessionTemplateId);
                    } else {
                        sessionStorage.removeItem("preferred_generation_template_id");
                        setSelectedTemplateId(defaultTpl?.template_ref || null);
                    }
                } else {
                    setSelectedTemplateId(defaultTpl?.template_ref || null);
                }
            } catch (error) {
                console.error("Erro ao carregar templates para geração:", error);
            }
        };
        loadTemplates();
    }, []);

    const handleGenerateAiProposal = async (projectId: string, templateIdOverride?: string | null) => {
        setShowAiModal(true);
        setIsGeneratingAi(true);
        setAiError(null);
        setAiProposal(null);
        setCurrentGeneratingProjectId(projectId);

        try {
            const tId = templateIdOverride !== undefined ? templateIdOverride : selectedTemplateId;
            const result = await api.generateProposal(projectId, tId);
            if (result.success) {
                setAiProposal({
                    proposal: result.proposal,
                    suggested_price: result.suggested_price,
                    justification: result.justification
                });
                
                // Aplicar default_budget e default_deadline_days com precedência
                const currentTemplate = templates.find((t: any) => t.template_ref === tId);
                let initialBudget = "";
                if (currentTemplate && currentTemplate.default_budget && currentTemplate.default_budget > 0) {
                    initialBudget = String(currentTemplate.default_budget);
                } else if (result.suggested_price) {
                    const priceClean = result.suggested_price.replace(/[^\d]/g, "");
                    initialBudget = priceClean || "";
                }
                if (!initialBudget && selectedProject) {
                    const projPriceClean = (selectedProject.budget || "").replace(/[^\d]/g, "");
                    initialBudget = projPriceClean || "100";
                }
                setModalBudget(initialBudget);

                let initialDeadline = "7";
                if (currentTemplate && currentTemplate.default_deadline_days && currentTemplate.default_deadline_days > 0) {
                    initialDeadline = String(currentTemplate.default_deadline_days);
                }
                setModalDeadline(initialDeadline);
            } else {
                setAiError(result.error || "Erro ao gerar proposta com IA.");
            }
        } catch (error: any) {
            console.error("Erro ao gerar proposta IA:", error);
            const errorMessage = error.message || "Erro desconhecido";
            
            if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
                setAiError("Não foi possível conectar ao servidor. Verifique se o backend está rodando e se as dependências (google-generativeai) estão instaladas.");
            } else {
                setAiError(errorMessage);
            }
        } finally {
            setIsGeneratingAi(false);
        }
    };

    const [isSubmittingProposal, setIsSubmittingProposal] = useState(false);

    const handleSubmitProposal = async () => {
        if (!selectedProject || !aiProposal?.proposal) return;
        setIsSubmittingProposal(true);
        try {
            const budgetVal = Number(modalBudget) || 100;
            const deadlineVal = Number(modalDeadline) || 7;

            const response = await api.submitProposal(selectedProject.id, {
                project_id: selectedProject.id,
                template_id: selectedTemplateId,
                custom_message: aiProposal.proposal,
                budget: budgetVal,
                deadline_days: deadlineVal
            });

            if (response.success) {
                toast.success(response.message || "Proposta enviada com sucesso no Workana!");
                setShowAiModal(false);
            } else {
                toast.error("Erro ao enviar proposta: " + response.message);
            }
        } catch (error: any) {
            console.error("Erro ao submeter proposta:", error);
            toast.error(error.message || "Erro de conexão ao enviar proposta.");
        } finally {
            setIsSubmittingProposal(false);
        }
    };

    const handleCopyProposal = () => {
        if (aiProposal?.proposal) {
            navigator.clipboard.writeText(aiProposal.proposal);
            toast.success("Proposta copiada para a área de transferência!", "Copiado!");
        }
    };

    const handleSaveFilter = async () => {
        if (!newFilterName.trim()) return;

        setIsSavingFilter(true);
        try {
            const cleanFilters: Record<string, any> = {};
            if (filters.keywords) cleanFilters.keywords = filters.keywords;
            if (filters.category) cleanFilters.category = filters.category;
            if (filters.min_budget) cleanFilters.min_budget = Number(filters.min_budget);
            if (filters.max_budget) cleanFilters.max_budget = Number(filters.max_budget);
            if (filters.project_type && filters.project_type !== "any") cleanFilters.project_type = filters.project_type;
            if (filters.sort && filters.sort !== "relevance") cleanFilters.sort = filters.sort;
            if (filters.publication && filters.publication !== "any") cleanFilters.publication = filters.publication;
            if (filters.language && filters.language !== "any") cleanFilters.language = filters.language;
            if (filters.proposals && filters.proposals !== "any") cleanFilters.proposals = filters.proposals;
            if (filters.payment_verified) cleanFilters.payment_verified = true;

            await api.createFilter(newFilterName, cleanFilters);
            toast.success("Filtro salvo com sucesso!");
            setShowSaveModal(false);
            setNewFilterName("");
        } catch (error: any) {
            console.error("Erro ao salvar filtro:", error);
            toast.error("Erro ao salvar filtro.");
        } finally {
            setIsSavingFilter(false);
        }
    };

    const handleResetFilters = () => {
        // Clear session storage
        sessionStorage.removeItem(STORAGE_KEY);
        
        setFilters({
            keywords: "",
            category: "",
            min_budget: "",
            max_budget: "",
            project_type: "any",
            sort: "relevance",
            publication: "any",
            language: "any",
            proposals: "any",
            payment_verified: false,
            pages_to_fetch: 10,
        });
    };

    const [selectedProject, setSelectedProject] = useState<Project | null>(null);

    // Close panel when clicking outside/pressing escape would be handled by a global listener or overlay if strict modal behavior was desired,
    // but for this "Dashboard" feel, clicking another project switches, and a close button exists.

    const [showAdvanced, setShowAdvanced] = useState(false);

    // Auxiliary function to calculate "Match Score"
    const calculateMatch = (project: Project) => {
        if (project.match_score !== undefined && project.match_score !== null) {
            return Math.round(project.match_score);
        }
        // Simple logic: fewer proposals && recent = higher match
        let score = 100;
        if (project.proposals_count) score -= (project.proposals_count * 2);
        const minutes = parseRelativeDate(project.posted_at);
        if (minutes > 60) score -= 10;
        if (minutes > 1440) score -= 20;
        return Math.max(10, Math.min(98, score)); // Clamp between 10 and 98
    };

    return (
        <div className={styles.container}>
            {isSearching && <div className={styles.scanline}></div>}
            
            {/* Mission Header */}
            <CyberHeader 
                title="PROJECT INTERCEPT" 
                subtitle="SYSTEM_READY // INITIATE_SEARCH"
                description="Identifique e capture as melhores oportunidades do mercado. Protocolo de caça ativado."
            />

            {/* Control Deck (Filters) */}
            <div className={styles.controlDeck}>
                <div className={styles.searchRow}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <svg 
                            width="20" 
                            height="20" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="2" 
                            style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }}
                        >
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input
                            type="text"
                            className={styles.controlInput}
                            style={{ paddingLeft: '48px' }}
                            placeholder="Buscar palavras-chave (ex: React, Python)..."
                            value={filters.keywords}
                            onChange={(e) => setFilters({ ...filters, keywords: e.target.value })}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        />
                    </div>
                    <button 
                        className="btn btn-primary" 
                        style={{ minWidth: '120px' }}
                        onClick={handleSearch}
                        disabled={isSearching}
                    >
                        {isSearching ? <span className="spinner spinner-sm"></span> : 'SCANEAR'}
                    </button>
                    <button 
                        className={`btn ${showAdvanced ? 'btn-secondary' : 'btn-ghost'}`}
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        style={{ border: '1px solid var(--color-border)' }}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '8px' }}>
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                        </svg>
                        {showAdvanced ? 'Ocultar Filtros' : 'Filtros Avançados'}
                    </button>
                </div>

                <div className={`${styles.filterGrid} ${showAdvanced ? styles.expanded : ''}`}>
                    <div className="form-group">
                        <label className="form-label">Categoria</label>
                        <select className={styles.controlInput} value={filters.category} onChange={e => setFilters({...filters, category: e.target.value})}>
                            {categories.map(cat => <option key={cat.value} value={cat.value}>{cat.label}</option>)}
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Orçamento (Mín - Máx)</label>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="number" className={styles.controlInput} placeholder="Min" value={filters.min_budget} onChange={e => setFilters({...filters, min_budget: e.target.value})} />
                            <input type="number" className={styles.controlInput} placeholder="Max" value={filters.max_budget} onChange={e => setFilters({...filters, max_budget: e.target.value})} />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Publicação</label>
                        <select className={styles.controlInput} value={filters.publication} onChange={e => setFilters({...filters, publication: e.target.value})}>
                            <option value="any">Qualquer data</option>
                            <option value="1d">Últimas 24h</option>
                            <option value="3d">Últimos 3 dias</option>
                            <option value="1w">Última semana</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Idioma</label>
                        <select className={styles.controlInput} value={filters.language} onChange={e => setFilters({...filters, language: e.target.value})}>
                            <option value="any">Todas as línguas</option>
                            <option value="pt">Português</option>
                            <option value="en">Inglês</option>
                            <option value="es">Espanhol</option>
                        </select>
                    </div>

                    {/* Quick Filters Row */}
                    <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '16px', alignItems: 'center', marginTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
                        <label className="checkbox-container" style={{ background: 'transparent', border: 'none', padding: 0 }}>
                            <input type="checkbox" checked={filters.payment_verified} onChange={e => setFilters({...filters, payment_verified: e.target.checked})} />
                            <span className="checkbox-label" style={{ color: 'var(--color-text-secondary)' }}>Pagamento Verificado</span>
                        </label>

                        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                             <span className="text-sm text-muted">Resultados por página:</span>
                             <select 
                                className={styles.controlInput} 
                                style={{ width: '80px', padding: '4px 8px' }}
                                value={filters.pages_to_fetch}
                                onChange={e => setFilters({...filters, pages_to_fetch: Number(e.target.value)})}
                             >
                                <option value={1}>10</option>
                                <option value={3}>30</option>
                                <option value={5}>50</option>
                                <option value={10}>100</option>
                             </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Results Grid & Side Panel Layout */}
            <div className={styles.mainLayout}>
                <div className={`${styles.gridContent} ${selectedProject ? styles.shrink : ''}`}>
                    {isSearching && projects.length === 0 ? (
                        <div style={{ padding: '40px' }}>
                            <Loader type="scanning" message="Interceptando sinais de projetos..." />
                        </div>
                    ) : hasSearched && projects.length === 0 ? (
                        <div className="empty-state">
                            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🛰️</div>
                            <h3 className="empty-state-title">Nenhum sinal detectado</h3>
                            <p className="empty-state-description">Ajuste os parâmetros dos sensores e tente novamente.</p>
                        </div>
                    ) : (
                        <>
                            {projects.length > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
                                    <span className="badge badge-neutral">{projects.length} Projetos Encontrados</span>
                                    <select 
                                        className={styles.controlInput} 
                                        style={{ width: 'auto', padding: '6px 12px' }}
                                        value={filters.sort}
                                        onChange={e => {
                                            setFilters({...filters, sort: e.target.value});
                                            setProjects(sortProjectsLocal(projects, e.target.value));
                                        }}
                                    >
                                        <option value="relevance">Relevância</option>
                                        <option value="created_at_desc">Mais Recentes</option>
                                        <option value="budget_desc">Maior Orçamento</option>
                                        <option value="bids_asc">Menos Concorridos</option>
                                    </select>
                                </div>
                            )}


                            <div className={`${styles.missionGrid} reveal-grid`}>
                                {projects.map((project, index) => {
                                    const matchScore = calculateMatch(project);
                                    const isNew = parseRelativeDate(project.posted_at) < 60;
                                    const isSelected = selectedProject?.id === project.id;

                                    return (
                                        <div 
                                            key={project.id} 
                                            className={`${styles.holoCard} ${isSelected ? styles.active : ''} reveal-item`}
                                            style={{ animationDelay: `${index * 0.05}s` }}
                                        >
                                            <div className={`${styles.cornerMarker} ${styles.cornerTL}`}></div>
                                            <div className={`${styles.cornerMarker} ${styles.cornerTR}`}></div>
                                            <div className={`${styles.cornerMarker} ${styles.cornerBL}`}></div>
                                            <div className={`${styles.cornerMarker} ${styles.cornerBR}`}></div>

                                            {isNew && <div className={styles.newBadge}>NOVO</div>}
                                            
                                            <div className={styles.cardHeader} onClick={() => setSelectedProject(project)}>
                                                <h3 className={styles.cardTitle} title="Clique para ver Detalhes">{project.title}</h3>
                                                <div className={styles.rewardBadge}>
                                                    {project.budget || 'A Combinar'}
                                                </div>
                                            </div>

                                            <div className={styles.cardBody} onClick={() => setSelectedProject(project)}>
                                                <div className={styles.techStack}>
                                                    {project.skills.slice(0, 4).map(skill => (
                                                        <span key={skill} className={styles.techTag}>{skill}</span>
                                                    ))}
                                                    {project.skills.length > 4 && (
                                                        <span className={styles.techTag}>+{project.skills.length - 4}</span>
                                                    )}
                                                </div>
                                                <p className={styles.description}>{project.description}</p>
                                                
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Compatibilidade: {matchScore}%</span>
                                                    <div className={styles.matchIndicator}>
                                                        <div 
                                                            className={styles.matchBar} 
                                                            style={{ 
                                                                width: `${matchScore}%`,
                                                                background: matchScore > 80 ? 'var(--gradient-success)' : matchScore > 50 ? 'var(--color-warning)' : 'var(--color-error)'
                                                            }}
                                                        ></div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className={styles.cardFooter}>
                                                <div className={styles.metaInfo}>
                                                    <div className={styles.metaItem}>
                                                        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                                        {project.posted_at}
                                                    </div>
                                                </div>
                                                <div className={styles.proposalCount}>
                                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                                                    {project.proposals_count} propostas
                                                </div>
                                            </div>

                                            {/* Quick Actions Toolbar (Slides up on Hover) */}
                                            <div className={styles.quickActions}>
                                                <button className={styles.actionBtn} onClick={(e) => { e.stopPropagation(); setSelectedProject(project); }}>
                                                    <span>👁️</span> BRIEFING
                                                </button>
                                                <button className={`${styles.actionBtn} ${styles.primary}`} onClick={(e) => { e.stopPropagation(); handleGenerateAiProposal(project.id); }}>
                                                    <span>⚡</span> IA STRATEGY
                                                </button>
                                                <a href={project.url} target="_blank" rel="noreferrer" className={styles.actionBtn} onClick={e => e.stopPropagation()}>
                                                    <span>🔗</span> LINK
                                                </a>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {hasMore && (
                                <div className={styles.loadMoreArea}>
                                    <button className="btn btn-secondary btn-lg" onClick={handleLoadMore} disabled={isLoadingMore}>
                                        {isLoadingMore ? 'Carregando dados...' : 'CARREGAR MAIS PROJETOS'}
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Mission Dossier Modal (Replaces Side Panel) */}
                {selectedProject && (
                    <div className={styles.dossierOverlay} onClick={() => setSelectedProject(null)}>
                        <div className={styles.dossierContainer} onClick={e => e.stopPropagation()}>
                            <div className={styles.dossierHeader} style={{ display: 'block', position: 'relative', paddingRight: '60px' }}>
                                <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                                    <span style={{ color: 'var(--color-primary)', fontSize: '0.85rem', letterSpacing: '4px', fontWeight: '600', textShadow: '0 0 10px rgba(99, 102, 241, 0.5)' }}>
                                        TOP SECRET // MISSION FILE
                                    </span>
                                </div>
                                
                                <button 
                                    className={styles.closeButton} 
                                    onClick={() => setSelectedProject(null)} 
                                    aria-label="Abort Mission"
                                    style={{ position: 'absolute', top: '24px', right: '24px' }}
                                >
                                    ×
                                </button>

                                <div>
                                    <h2 style={{ fontSize: '1.8rem', fontWeight: 'bold', lineHeight: '1.2', marginBottom: '8px' }}>{selectedProject.title}</h2>
                                    <div style={{ fontSize: '1.1rem', color: '#34d399', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ opacity: 0.7, fontSize: '0.9rem', fontWeight: 'normal', color: 'var(--color-text-muted)' }}>ORÇAMENTO DO PROJETO:</span>
                                        {selectedProject.budget || 'NEGOCIÁVEL'}
                                    </div>
                                </div>
                            </div>
                            
                            <div className={styles.dossierBody} style={{ padding: 0, overflow: 'hidden' }}>
                                <div className={styles.dossierContentGrid}>
                                    <div className={styles.dossierMain} style={{ padding: '2rem' }}>
                                        <h4 style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginBottom: '1rem', textTransform: 'uppercase' }}>
                                            &gt; Descrição da Missão (Decoded)
                                        </h4>
                                        <div className={styles.decryptText}>
                                            {selectedProject.description}
                                        </div>
                                    </div>
                                    
                                    <div className={styles.dossierSidebar}>
                                        <div>
                                            <h4 style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                                &gt; Arsenal (Skills)
                                            </h4>
                                            <div className={styles.techStack} style={{ flexWrap: 'wrap' }}>
                                                {selectedProject.skills.map(skill => (
                                                    <span key={skill} className={styles.techTag} style={{ marginBottom: '6px', fontSize: '0.75rem' }}>{skill}</span>
                                                ))}
                                            </div>
                                        </div>

                                        <div>
                                            <h4 style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                                &gt; Dados de Inteligência
                                            </h4>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>DATA DE PUBLICAÇÃO</span>
                                                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{selectedProject.posted_at}</span>
                                                </div>
                                                <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>CONCORRÊNCIA</span>
                                                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{selectedProject.proposals_count} Candidatos</span>
                                                </div>
                                                <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>CLIENTE</span>
                                                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                                        {selectedProject.client_name || 'Não informado'}
                                                        {selectedProject.client_country ? ` · ${selectedProject.client_country}` : ''}
                                                    </span>
                                                </div>
                                                <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                    <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>CONFIABILIDADE</span>
                                                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                                        {selectedProject.payment_verified ? '✓ Pagamento verificado' : 'Pagamento não verificado'}
                                                        {selectedProject.client_rating != null ? ` · ★ ${selectedProject.client_rating.toFixed(1)}` : ''}
                                                    </span>
                                                </div>
                                                {(selectedProject.project_type || selectedProject.deadline) && (
                                                    <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                        <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>CONTRATO</span>
                                                        <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                                            {selectedProject.project_type === 'hourly' ? 'Por hora' : 'Preço fixo'}
                                                            {selectedProject.deadline ? ` · ${selectedProject.deadline}` : ''}
                                                        </span>
                                                    </div>
                                                )}
                                                {(selectedProject.client_projects_posted != null || selectedProject.client_projects_paid != null) && (
                                                    <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                        <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '4px' }}>HISTÓRICO DO CLIENTE</span>
                                                        <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                                            {selectedProject.client_projects_posted ?? 0} publicados · {selectedProject.client_projects_paid ?? 0} pagos
                                                        </span>
                                                        {selectedProject.client_member_since && <small style={{ display: 'block' }}>Desde {selectedProject.client_member_since}</small>}
                                                    </div>
                                                )}
                                                {selectedProject.details && Object.keys(selectedProject.details).length > 2 && (
                                                    <div className="card p-3 bg-glass" style={{ border: '1px solid rgba(255,255,255,0.05)' }}>
                                                        <span style={{ display: 'block', fontSize: '0.7rem', color: '#64748b', marginBottom: '6px' }}>BRIEFING ESTRUTURADO</span>
                                                        {Object.entries(selectedProject.details)
                                                            .filter(([key]) => !['category', 'subcategory'].includes(key))
                                                            .map(([key, value]) => <small key={key} style={{ display: 'block' }}><strong>{key.replace(/_/g, ' ')}:</strong> {value}</small>)}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                            <button 
                                                className="btn btn-primary w-full"
                                                onClick={() => handleGenerateAiProposal(selectedProject.id)}
                                                style={{ height: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                                            >
                                                <span>⚡</span> Gerar Proposta
                                            </button>
                                            <a 
                                                href={selectedProject.url} 
                                                target="_blank" 
                                                rel="noreferrer" 
                                                className="btn btn-secondary w-full"
                                                style={{ textAlign: 'center', height: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                                            >
                                                Abrir no Workana ↗
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Modais (Save Filter & AI Proposal) permanecem iguais */}
            {showSaveModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3 className="modal-title">Salvar Configuração de Busca</h3>
                            <button className="btn-close" onClick={() => setShowSaveModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label className="form-label">Nome do Perfil</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={newFilterName}
                                    onChange={(e) => setNewFilterName(e.target.value)}
                                    placeholder="Ex: Hunter Python"
                                    autoFocus
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-ghost" onClick={() => setShowSaveModal(false)}>Cancelar</button>
                            <button className="btn btn-primary" onClick={handleSaveFilter}>Salvar</button>
                        </div>
                    </div>
                </div>
            )}
            
            {showAiModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '800px' }}>
                        <div className="modal-header">
                            <h3 className="modal-title">✨ Mega Proposta IA</h3>
                            <button className="btn-close" onClick={() => setShowAiModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group mb-4">
                                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                    <span style={{ fontWeight: 600 }}>Selecione o Template</span>
                                    <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>(a escolha será lembrada nesta sessão)</span>
                                </label>
                                <select
                                    className="form-input"
                                    value={selectedTemplateId || ""}
                                    onChange={(e) => {
                                        const val = e.target.value || null;
                                        setSelectedTemplateId(val);
                                        if (val) {
                                            sessionStorage.setItem("preferred_generation_template_id", val);
                                        } else {
                                            sessionStorage.removeItem("preferred_generation_template_id");
                                        }
                                        if (currentGeneratingProjectId) {
                                            handleGenerateAiProposal(currentGeneratingProjectId, val);
                                        }
                                    }}
                                    disabled={isGeneratingAi}
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        borderRadius: 'var(--radius-md)',
                                        border: '1px solid var(--color-border)',
                                        backgroundColor: 'var(--color-bg-secondary)',
                                        color: 'var(--color-text)',
                                        outline: 'none'
                                    }}
                                >
                                    <option value="">Prompt Padrão (Sem Template / Legacy)</option>
                                    {templates.map((t) => (
                                        <option key={t.template_ref} value={t.template_ref}>
                                            {t.name} {t.is_system ? "🛡️ (Oficial)" : ""} {t.is_default ? "⭐ (Padrão)" : ""}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            
                            {isGeneratingAi ? (
                                <Loader type="scanning" message="Analisando missão e gerando estratégia..." />
                            ) : aiError ? (
                                <div className="alert alert-error">{aiError}</div>
                            ) : (
                                <div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                                        <div className="card text-center p-4">
                                            <div className="text-sm text-muted">Valor Sugerido</div>
                                            <div className="text-xl font-bold text-primary">{aiProposal?.suggested_price}</div>
                                        </div>
                                        <div className="card p-4">
                                            <div className="text-sm text-muted mb-2">Justificativa</div>
                                            <div className="text-xs">{aiProposal?.justification}</div>
                                        </div>
                                    </div>
                                    
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
                                        <div className="form-group">
                                            <label className="form-label" style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Valor da Proposta (R$)</label>
                                            <input 
                                                type="number" 
                                                className="form-input" 
                                                value={modalBudget}
                                                onChange={(e) => setModalBudget(e.target.value)}
                                                placeholder="Ex: 500"
                                                style={{
                                                    width: '100%',
                                                    padding: '0.5rem',
                                                    borderRadius: 'var(--radius-md)',
                                                    border: '1px solid var(--color-border)',
                                                    backgroundColor: 'var(--color-bg-secondary)',
                                                    color: 'var(--color-text)',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label" style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Prazo de Entrega (Dias)</label>
                                            <input 
                                                type="number" 
                                                className="form-input" 
                                                value={modalDeadline}
                                                onChange={(e) => setModalDeadline(e.target.value)}
                                                placeholder="Ex: 7"
                                                style={{
                                                    width: '100%',
                                                    padding: '0.5rem',
                                                    borderRadius: 'var(--radius-md)',
                                                    border: '1px solid var(--color-border)',
                                                    backgroundColor: 'var(--color-bg-secondary)',
                                                    color: 'var(--color-text)',
                                                    outline: 'none'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Proposta Gerada</label>
                                        <textarea 
                                            className="form-input" 
                                            rows={10} 
                                            value={aiProposal?.proposal} 
                                            readOnly 
                                        />
                                    </div>
                                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                                        <button 
                                            className="btn w-full" 
                                            style={{ backgroundColor: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }} 
                                            onClick={handleCopyProposal}
                                        >
                                            Copiar Proposta
                                        </button>
                                        <button 
                                            className="btn btn-primary w-full" 
                                            onClick={handleSubmitProposal}
                                            disabled={isSubmittingProposal}
                                        >
                                            {isSubmittingProposal ? "Enviando..." : "Enviar Proposta"}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
