import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  api,
  type AnalysisResult,
  type ProposalBatch,
  type BidsHistoryResponse,
  type ProposalTemplate,
  type ProposalBatchCreate,
  type ProposalVersion,
} from '../services/api';
import { SCRAPING_PAGES_OPTIONS } from '../constants/options';
import styles from './Projects.module.css';
import Loader from '../components/Loader';
import { useToast } from '../context/ToastContext';
import CyberHeader from '../components/CyberHeader';
import {
  ProjectCard,
  ProjectFiltersBar,
  ProjectDetailModal,
  ProposalModal,
  BatchCreateModal,
  BidsHistoryModal,
  SaveFilterModal,
  QueueDrawerModal,
  type SearchFilters,
  type BatchReviewItem,
} from '../components/projects';

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
  estimated_published_at?: string | null;
  proposals_delta?: number | null;
  contract_type?: string | null;
  url: string;
  match_score?: number | null;
  is_favorite?: boolean;
  is_hidden?: boolean;
  notes?: string | null;
  analysis?: AnalysisResult | null;
  analyzed_at?: string | null;
}

const CATALOG_PAGE_SIZE = 24;

export default function Projects() {
  const { toast } = useToast();
  const [searchParams] = useSearchParams();

  const STORAGE_KEY = 'workana_projects_cache_v4';

  const loadStateFromStorage = () => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.error('Failed to load state', e);
      return null;
    }
  };

  const savedState = loadStateFromStorage();
  const hasUrlParams = Array.from(searchParams.keys()).length > 0;

  const rawPages =
    Number(
      searchParams.get('pages_to_fetch') ||
        searchParams.get('pages') ||
        savedState?.filters?.pages_to_fetch
    ) || 10;
  const validPagesList = SCRAPING_PAGES_OPTIONS.map((o) => o.value);
  const initialPagesToFetch = validPagesList.includes(rawPages) ? rawPages : 10;

  const initialFilters: SearchFilters =
    hasUrlParams || !savedState
      ? {
          keywords: searchParams.get('keywords') || '',
          category: searchParams.get('category') || '',
          min_budget: searchParams.get('min_budget') || '',
          max_budget: searchParams.get('max_budget') || '',
          project_type: searchParams.get('project_type') || 'any',
          sort: searchParams.get('sort') || 'created_at_desc',
          publication: searchParams.get('publication') || 'any',
          language: searchParams.get('language') || 'any',
          proposals: searchParams.get('proposals') || 'any',
          payment_verified: searchParams.get('payment_verified') === 'true',
          pages_to_fetch: initialPagesToFetch,
          favorites_only: searchParams.get('favorites_only') === 'true',
          hidden_only: searchParams.get('hidden_only') === 'true',
        }
      : {
          ...savedState.filters,
          pages_to_fetch: initialPagesToFetch,
        };

  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [projects, setProjects] = useState<Project[]>(
    !hasUrlParams && savedState ? savedState.projects : []
  );
  const [isSearching, setIsSearching] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [hasSearched, setHasSearched] = useState(
    !hasUrlParams && savedState ? savedState.hasSearched : false
  );
  const [page, setPage] = useState(!hasUrlParams && savedState ? savedState.page : 1);
  const [total, setTotal] = useState(!hasUrlParams && savedState ? savedState.total || 0 : 0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectAllFiltered, setSelectAllFiltered] = useState(false);
  const [excludedIds, setExcludedIds] = useState<Set<string>>(new Set());
  const [analysisById, setAnalysisById] = useState<Record<string, AnalysisResult>>({});
  const activeFilterSignature = useRef<string | null>(null);
  const knownProjects = useRef<Map<string, Project>>(new Map());

  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);

  // Modal de Histórico de Propostas (Bids)
  const [bidsProject, setBidsProject] = useState<Project | null>(null);
  const [bidsData, setBidsData] = useState<BidsHistoryResponse | null>(null);
  const [bidsLoading, setBidsLoading] = useState(false);

  // Modal de IA Proposta
  const [showAiModal, setShowAiModal] = useState(false);
  const [aiProposal, setAiProposal] = useState<{
    id?: number;
    proposal?: string;
    suggested_price?: string;
    justification?: string;
    status?: string;
    sent_at?: string;
    is_cached?: boolean;
    investment_breakdown?: any;
    template_id?: any;
    template_slug?: string;
  } | null>(null);
  const [proposalVersions, setProposalVersions] = useState<ProposalVersion[]>([]);
  const [activeVersionId, setActiveVersionId] = useState<number | null>(null);
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [modalBudget, setModalBudget] = useState<string>('');
  const [modalDeadline, setModalDeadline] = useState<string>('7');
  const [currentGeneratingProjectId, setCurrentGeneratingProjectId] = useState<string | null>(null);
  const [isSubmittingProposal, setIsSubmittingProposal] = useState(false);

  // Templates
  const [templates, setTemplates] = useState<ProposalTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  // Nível de Preço (budget, standard, premium)
  const [priceLevel, setPriceLevel] = useState<'budget' | 'standard' | 'premium'>('standard');

  // Modal de Envio em Lote (Batches)
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchItems, setBatchItems] = useState<BatchReviewItem[]>([]);
  const [batchTemplateRef, setBatchTemplateRef] = useState<string | null>(null);
  const [isBatchGenerating, setIsBatchGenerating] = useState(false);
  const [isSubmittingBatch, setIsSubmittingBatch] = useState(false);

  // Drawer de Monitoramento de Lotes/Fila
  const [showQueueDrawer, setShowQueueDrawer] = useState(false);
  const [batches, setBatches] = useState<ProposalBatch[]>([]);
  const [isLoadingBatches, setIsLoadingBatches] = useState(false);
  const [selectedBatchDetail, setSelectedBatchDetail] = useState<ProposalBatch | null>(null);

  useEffect(() => {
    if (hasSearched || projects.length > 0) {
      const stateToSave = { filters, projects, hasSearched, page, total };
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    }
  }, [filters, projects, hasSearched, page, total]);

  // Carregar templates disponíveis
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const res = await api.getTemplates();
        setTemplates(res);
        const savedTemplate = sessionStorage.getItem('preferred_generation_template_id');
        if (savedTemplate) {
          setSelectedTemplateId(savedTemplate);
        } else {
          const defaultTemp = res.find((t) => t.is_default);
          if (defaultTemp)
            setSelectedTemplateId(defaultTemp.template_ref || String(defaultTemp.id));
        }
      } catch (err) {
        console.error('Erro ao carregar templates', err);
      }
    };
    loadTemplates();
  }, []);

  // Conversão de filtros para chamada de API
  const toCatalogFilters = (f: SearchFilters) => ({
    q: f.keywords.trim() || undefined,
    category: f.category || undefined,
    min_budget: f.min_budget ? Number(f.min_budget) : undefined,
    max_budget: f.max_budget ? Number(f.max_budget) : undefined,
    payment_verified: f.payment_verified ? true : undefined,
    favorites_only: f.favorites_only ? true : undefined,
    hidden_only: f.hidden_only ? true : undefined,
  });

  // Execução da busca
  const executeSearch = async (
    targetPage = 1,
    forceReset = false,
    customFilters?: SearchFilters
  ) => {
    const activeFilters = customFilters || filters;
    const signature = JSON.stringify({ ...activeFilters, targetPage });
    if (activeFilterSignature.current === signature && !forceReset) return;
    activeFilterSignature.current = signature;

    setIsSearching(true);
    try {
      const catalogFilters = toCatalogFilters(activeFilters);
      const res = await api.getCatalogProjects({
        ...catalogFilters,
        page: targetPage,
        limit: activeFilters.pages_to_fetch,
        sort: activeFilters.sort,
      });

      const mapped: Project[] = (res.projects || []).map((p) => ({
        id: p.workana_id,
        title: p.title,
        description: p.description || '',
        budget:
          p.budget_min && p.budget_max
            ? `R$ ${p.budget_min} - ${p.budget_max}`
            : p.budget_min
              ? `R$ ${p.budget_min}`
              : null,
        budget_min: p.budget_min,
        budget_max: p.budget_max,
        project_type: p.budget_type,
        category: p.category,
        subcategory: p.subcategory,
        deadline: p.deadline,
        details: (p.details as Record<string, string>) || {},
        skills: p.skills || [],
        client_name: p.client_name,
        client_country: p.client_country,
        client_rating: p.client_rating,
        client_plan: p.client_plan,
        client_projects_posted: p.client_projects_posted,
        client_projects_paid: p.client_projects_paid,
        client_member_since: p.client_member_since,
        proposals_count: p.proposals_count ?? 0,
        posted_at: p.posted_at || p.published_at || null,
        published_at: p.published_at,
        payment_verified: p.payment_verified,
        last_client_activity: p.last_client_activity,
        is_urgent: p.is_urgent,
        is_featured: p.is_featured,
        estimated_published_at: p.estimated_published_at,
        proposals_delta: p.proposals_delta,
        contract_type: p.contract_type,
        url: p.url,
        is_favorite: p.is_favorite,
        is_hidden: p.is_hidden,
        notes: p.notes,
        analysis: p.analysis as AnalysisResult | null,
        analyzed_at: p.analyzed_at,
      }));

      mapped.forEach((p) => knownProjects.current.set(p.id, p));
      setProjects(mapped);
      setTotal(res.total || 0);
      setPage(targetPage);
      setHasSearched(true);
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao buscar projetos.');
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    if (!hasSearched) {
      executeSearch(1, true);
    }
  }, []);

  const calculateMatch = (project: Project): number => {
    if (project.analysis?.score) return Math.round(project.analysis.score);
    let score = 50;
    if (project.payment_verified) score += 15;
    if (project.client_rating && project.client_rating >= 4.5) score += 15;
    if (project.proposals_count !== null && project.proposals_count < 5) score += 10;
    if (project.skills.length > 0) score += 10;
    return Math.min(100, score);
  };

  const handleSelectProject = (project: any) => {
    setSelectedProject(project);
  };

  const toggleProjectSelection = (projectId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) next.delete(projectId);
      else next.add(projectId);
      return next;
    });
  };

  const isProjectSelected = (projectId: string) => {
    if (selectAllFiltered) return !excludedIds.has(projectId);
    return selectedIds.has(projectId);
  };

  const selectedCount = selectAllFiltered
    ? Math.max(0, total - excludedIds.size)
    : selectedIds.size;

  const clearSelection = () => {
    setSelectedIds(new Set());
    setSelectAllFiltered(false);
    setExcludedIds(new Set());
  };

  const selectEveryFilteredProject = () => {
    setSelectAllFiltered(true);
    setExcludedIds(new Set());
    setSelectedIds(new Set());
    toast.info(`Todos os ${total} projetos do filtro selecionados.`);
  };

  // Histórico de Bids Modal
  const openBidsHistory = async (project: any) => {
    setBidsProject(project);
    setBidsData(null);
    setBidsLoading(true);
    try {
      const res = await api.getBidsHistory(project.id);
      setBidsData(res);
    } catch (err: any) {
      toast.error(err.message || 'Erro ao carregar histórico de propostas.');
    } finally {
      setBidsLoading(false);
    }
  };

  // Geração e Gestão de Proposta IA
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  const handleOpenProposalModal = async (
    projectId: string,
    templateRef?: string | null,
    level?: 'budget' | 'standard' | 'premium',
    autoGenerate = false
  ) => {
    setCurrentGeneratingProjectId(projectId);
    if (templateRef !== undefined) setSelectedTemplateId(templateRef);
    if (level) setPriceLevel(level);

    setAiError(null);
    setIsGeneratingAi(false);

    try {
      const proposalRes = await api.getProjectProposal(projectId);
      if (proposalRes.has_proposal && proposalRes.proposal) {
        const versionsList =
          proposalRes.versions && proposalRes.versions.length > 0
            ? proposalRes.versions
            : [
                {
                  id: proposalRes.id || 1,
                  project_id: projectId,
                  proposal: proposalRes.proposal,
                  budget: proposalRes.budget,
                  deadline_days: proposalRes.deadline_days,
                  status: proposalRes.status,
                  sent_at: proposalRes.sent_at,
                  template_id: proposalRes.template_id,
                  template_slug: proposalRes.template_slug,
                },
              ];

        setProposalVersions(versionsList);
        const latest = versionsList[0];
        setActiveVersionId(latest.id);
        setAiProposal({
          id: latest.id,
          proposal: latest.proposal,
          suggested_price: latest.budget ? `R$ ${latest.budget.toFixed(2)}` : '—',
          justification: 'Versão carregada do histórico salvo.',
          status: latest.status,
          sent_at: latest.sent_at,
          is_cached: true,
          template_id: latest.template_id,
          template_slug: latest.template_slug,
        });
        setModalBudget(latest.budget ? String(latest.budget) : '500');
        setModalDeadline(latest.deadline_days ? String(latest.deadline_days) : '7');
        setShowAiModal(true);
        return;
      }
    } catch (e) {
      console.log('No previous proposal found', e);
    }

    setProposalVersions([]);
    setActiveVersionId(null);
    setAiProposal(null);
    setModalBudget('500');
    setModalDeadline('7');
    setShowAiModal(true);

    if (autoGenerate) {
      handleGenerateAiProposal(projectId, templateRef, level, true);
    }
  };

  const handleGenerateAiProposal = async (
    projectId: string,
    templateRef?: string | null,
    level?: 'budget' | 'standard' | 'premium',
    saveAsNewVersion = true
  ) => {
    setCurrentGeneratingProjectId(projectId);
    setShowAiModal(true);
    setIsGeneratingAi(true);
    setAiError(null);

    const activeRef = templateRef !== undefined ? templateRef : selectedTemplateId;
    const activeLevel = level || priceLevel;

    try {
      const res = await api.generateProposal(
        projectId,
        activeRef || undefined,
        true,
        activeLevel,
        saveAsNewVersion
      );

      if (res.success) {
        setAiProposal(res);
        if (res.versions && res.versions.length > 0) {
          setProposalVersions(res.versions);
          if (res.proposal_id) {
            setActiveVersionId(res.proposal_id);
          } else {
            setActiveVersionId(res.versions[0].id);
          }
        }
        const suggestedNum = res.suggested_price ? res.suggested_price.replace(/[^0-9]/g, '') : '';
        setModalBudget(suggestedNum || '500');
        setModalDeadline(res.suggested_deadline_days ? String(res.suggested_deadline_days) : '7');
        toast.success('✨ Nova versão gerada com sucesso!');
      } else {
        setAiError(res.error || 'Não foi possível gerar a proposta.');
      }
    } catch (err: any) {
      setAiError(err.message || 'Erro de conexão ao gerar proposta.');
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const handleSelectProposalVersion = (version: ProposalVersion) => {
    setActiveVersionId(version.id);
    setAiProposal({
      id: version.id,
      proposal: version.proposal,
      suggested_price: version.budget ? `R$ ${version.budget.toFixed(2)}` : '—',
      justification: 'Versão carregada do histórico.',
      status: version.status,
      sent_at: version.sent_at,
      is_cached: true,
      template_id: version.template_id,
      template_slug: version.template_slug,
    });
    setModalBudget(version.budget ? String(version.budget) : '500');
    setModalDeadline(version.deadline_days ? String(version.deadline_days) : '7');
    if (version.template_slug) {
      setSelectedTemplateId(`system:${version.template_slug}`);
    } else if (version.template_id) {
      setSelectedTemplateId(String(version.template_id));
    }
  };

  const handleDeleteProposalVersion = async (versionId: number) => {
    if (!currentGeneratingProjectId) return;
    try {
      const res = await api.deleteProjectProposalVersion(currentGeneratingProjectId, versionId);
      if (res.success) {
        const nextVersions = res.versions || [];
        setProposalVersions(nextVersions);
        if (nextVersions.length > 0) {
          if (activeVersionId === versionId) {
            handleSelectProposalVersion(nextVersions[0]);
          }
        } else {
          setAiProposal(null);
          setActiveVersionId(null);
        }
        toast.info('Versão excluída com sucesso.');
      }
    } catch (err: any) {
      toast.error(err.message || 'Erro ao excluir versão.');
    }
  };

  const handleSaveProposalDraft = async () => {
    if (!currentGeneratingProjectId || !aiProposal?.proposal) return;
    setIsSavingDraft(true);
    try {
      const res = await api.saveProjectProposal(currentGeneratingProjectId, {
        proposal_id: activeVersionId,
        proposal_text: aiProposal.proposal,
        budget: Number(modalBudget) || undefined,
        deadline_days: Number(modalDeadline) || 7,
        template_id: selectedTemplateId || undefined,
        force_new_version: false,
        add_to_batch: true,
      });
      if (res.success) {
        toast.success('✨ Proposta salva com sucesso! Visível em Lotes / Batches.');
        if (res.versions) setProposalVersions(res.versions);
        if (res.proposal_id) setActiveVersionId(res.proposal_id);
        setAiProposal((prev) => (prev ? { ...prev, is_cached: true } : null));
      }
    } catch (err: any) {
      toast.error(err.message || 'Erro ao salvar rascunho de proposta.');
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handleSubmitProposal = async () => {
    if (!currentGeneratingProjectId || !aiProposal?.proposal) return;
    setIsSubmittingProposal(true);
    try {
      const investmentText = aiProposal.investment_breakdown?.breakdown_text || '';
      const messageToSend =
        investmentText && !aiProposal.proposal.includes(investmentText)
          ? `${aiProposal.proposal}\n\n${investmentText}`
          : aiProposal.proposal;

      const res = await api.submitProposal(currentGeneratingProjectId, {
        project_id: currentGeneratingProjectId,
        custom_message: messageToSend,
        budget: Number(modalBudget) || 500,
        deadline_days: Number(modalDeadline) || 7,
        template_id: selectedTemplateId || undefined,
      });
      if (res.success) {
        toast.success('🚀 Proposta enviada com sucesso ao Workana! Status: Aguardando resposta');
        setShowAiModal(false);
      } else {
        toast.error(res.message || 'Erro ao enviar proposta.');
      }
    } catch (err: any) {
      toast.error(err.message || 'Erro ao enviar proposta.');
    } finally {
      setIsSubmittingProposal(false);
    }
  };

  const handleCopyProposal = () => {
    if (aiProposal?.proposal) {
      const investmentText = aiProposal.investment_breakdown?.breakdown_text || '';
      const fullProposal = investmentText
        ? `${aiProposal.proposal}\n\n${investmentText}`
        : aiProposal.proposal;
      navigator.clipboard.writeText(fullProposal);
      toast.success('Proposta completa copiada para a área de transferência!');
    }
  };

  // Ações em Lote (Bulk)
  const runBulkAction = async (action: 'favorite' | 'unfavorite' | 'hide' | 'restore') => {
    try {
      const body = selectAllFiltered
        ? { action, filters: toCatalogFilters(filters), exclude_ids: Array.from(excludedIds) }
        : { action, project_ids: Array.from(selectedIds) };
      const res = await api.bulkState(body);
      toast.success(`${res.updated} projeto(s) atualizado(s)!`);
      clearSelection();
      executeSearch(page, true);
    } catch (err: any) {
      toast.error(err.message || 'Erro na ação em lote.');
    }
  };

  const runBulkAnalysis = async () => {
    try {
      const body = selectAllFiltered
        ? { filters: toCatalogFilters(filters), exclude_ids: Array.from(excludedIds) }
        : { project_ids: Array.from(selectedIds) };
      const res = await api.analyzeProjects(body);
      const map: Record<string, AnalysisResult> = {};
      res.forEach((r) => {
        map[r.workana_id] = r;
      });
      setAnalysisById((prev) => ({ ...prev, ...map }));
      toast.success(`${res.length} projetos analisados pela IA!`);
    } catch (err: any) {
      toast.error(err.message || 'Erro na análise em lote.');
    }
  };

  // Lotes de Envio (Batches)
  const handleOpenBatchReviewModal = async () => {
    const targetProjects: Project[] = selectAllFiltered
      ? projects.filter((p) => !excludedIds.has(p.id))
      : Array.from(selectedIds)
          .map((id) => knownProjects.current.get(id) || projects.find((p) => p.id === id))
          .filter((p): p is Project => Boolean(p));

    if (!targetProjects.length) {
      toast.error('Nenhum projeto selecionado.');
      return;
    }

    const limitedProjects = targetProjects.slice(0, 20);
    if (targetProjects.length > 20) {
      toast.info('Limitando o lote aos 20 primeiros projetos por segurança.');
    }

    const tId = selectedTemplateId || undefined;
    setBatchTemplateRef(tId || null);

    const initialItems: BatchReviewItem[] = limitedProjects.map((proj) => ({
      workana_id: proj.id,
      title: proj.title,
      url: proj.url,
      proposal_text: '',
      budget: proj.budget_max || proj.budget_min || 150,
      deadline_days: 7,
      score: calculateMatch(proj),
      selected: true,
      status: 'generating',
    }));

    setBatchItems(initialItems);
    setShowBatchModal(true);
    setIsBatchGenerating(true);

    try {
      const projectIds = limitedProjects.map((p) => p.id);
      const genRes = await api.bulkGenerateProposals(projectIds, tId);
      if (genRes.success && genRes.results) {
        const resultMap = new Map(genRes.results.map((r) => [r.workana_id, r]));
        setBatchItems((prev) =>
          prev.map((item) => {
            const res = resultMap.get(item.workana_id);
            if (res && res.success) {
              return {
                ...item,
                proposal_text: res.proposal,
                budget: res.suggested_budget || item.budget,
                deadline_days: res.suggested_deadline_days || 7,
                status: 'ready',
              };
            }
            return {
              ...item,
              status: 'error',
              error: res?.error || 'Falha ao gerar proposta',
            };
          })
        );
        toast.success(`${genRes.generated} de ${genRes.total} propostas geradas com sucesso!`);
      }
    } catch (err: any) {
      toast.error(err?.message || 'Erro na geração em lote das propostas.');
    } finally {
      setIsBatchGenerating(false);
    }
  };

  const handleSubmitBatchToQueue = async () => {
    const approvedItems = batchItems.filter((i) => i.selected && i.proposal_text.trim().length > 0);
    if (!approvedItems.length) {
      toast.error('Nenhuma proposta com texto selecionada para envio.');
      return;
    }

    setIsSubmittingBatch(true);
    try {
      const payload: ProposalBatchCreate = {
        template_ref: batchTemplateRef || undefined,
        custom_proposals: approvedItems.map((item) => ({
          workana_id: item.workana_id,
          proposal_text: item.proposal_text,
          budget: item.budget,
          deadline_days: item.deadline_days,
        })),
      };
      const res = await api.createProposalBatch(payload);
      if (res.success) {
        toast.success(`Lote #${res.batch_id} criado com ${res.total} propostas! Envio iniciado.`);
        setShowBatchModal(false);
        clearSelection();
        setShowQueueDrawer(true);
        await loadBatches();
      }
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao enfileirar lote.');
    } finally {
      setIsSubmittingBatch(false);
    }
  };

  const loadBatches = async () => {
    setIsLoadingBatches(true);
    try {
      const res = await api.listProposalBatches(20);
      setBatches(res.batches || []);
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao carregar fila de lotes.');
    } finally {
      setIsLoadingBatches(false);
    }
  };

  const loadBatchDetail = async (batchId: number) => {
    try {
      const res = await api.getProposalBatch(batchId);
      setSelectedBatchDetail((prev) => (prev?.id === batchId ? null : res));
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao obter detalhes do lote.');
    }
  };

  const handleCancelBatch = async (batchId: number) => {
    try {
      await api.cancelProposalBatch(batchId);
      toast.success('Lote cancelado!');
      await loadBatches();
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao cancelar lote.');
    }
  };

  const handleRetryBatch = async (batchId: number) => {
    try {
      await api.retryProposalBatch(batchId);
      toast.success('Lote reiniciado para processamento!');
      await loadBatches();
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao reiniciar lote.');
    }
  };

  const handleSaveFilter = async (name: string) => {
    try {
      await api.createFilter(name, toCatalogFilters(filters));
      toast.success(`Filtro "${name}" salvo com sucesso!`);
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao salvar filtro.');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / (filters.pages_to_fetch || 24)));

  return (
    <div className={styles.container}>
      {isSearching && <div className={styles.scanline}></div>}

      <CyberHeader
        title="PROJECT INTERCEPT"
        subtitle="SYSTEM_READY // INITIATE_SEARCH"
        description="Identifique e capture as melhores oportunidades do mercado. Protocolo de caça ativado."
      />

      <ProjectFiltersBar
        filters={filters}
        isSearching={isSearching}
        isSyncing={isSyncing}
        showAdvanced={showAdvanced}
        onFiltersChange={(newF) => {
          setFilters(newF);
        }}
        onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
        onSearch={() => executeSearch(1, true)}
        onSyncLive={async () => {
          setIsSyncing(true);
          try {
            const pagesLabel =
              filters.pages_to_fetch >= 100
                ? 'todas as páginas'
                : `${filters.pages_to_fetch} página(s)`;
            toast.info(`Buscando no Workana e atualizando banco de dados (${pagesLabel})...`);
            const res = await api.refreshCatalog({
              keywords: filters.keywords || undefined,
              category: filters.category || undefined,
              min_budget: filters.min_budget ? Number(filters.min_budget) : undefined,
              max_budget: filters.max_budget ? Number(filters.max_budget) : undefined,
              project_type: filters.project_type !== 'any' ? filters.project_type : undefined,
              language: filters.language !== 'any' ? filters.language : undefined,
              publication: filters.publication !== 'any' ? filters.publication : undefined,
              payment_verified: filters.payment_verified || undefined,
              pages_to_fetch: filters.pages_to_fetch,
            });
            toast.success(
              res.message || `Banco de dados atualizado: ${res.upserted || 0} novos projetos.`
            );
            executeSearch(1, true);
          } catch (err: any) {
            toast.error(err.message || 'Erro ao scanear projetos no Workana.');
          } finally {
            setIsSyncing(false);
          }
        }}
      />

      {/* Main Content Layout */}
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
              <p className="empty-state-description">
                Ajuste os parâmetros dos sensores e tente novamente.
              </p>
            </div>
          ) : (
            <>
              {projects.length > 0 && (
                <div className={styles.resultsToolbar}>
                  <div className={styles.selectionControls}>
                    <button
                      type="button"
                      className={styles.textAction}
                      onClick={selectEveryFilteredProject}
                    >
                      Selecionar todos os {total} resultados
                    </button>
                    <button
                      type="button"
                      className={styles.quickSelectPill}
                      style={{
                        background: 'rgba(16, 185, 129, 0.15)',
                        borderColor: 'rgba(16, 185, 129, 0.4)',
                        color: '#6ee7b7',
                      }}
                      onClick={() => {
                        setShowQueueDrawer(true);
                        loadBatches();
                      }}
                    >
                      📊 Fila de Envios
                    </button>
                    <button
                      type="button"
                      className={styles.quickSelectPill}
                      title="Salvar esta busca como preset"
                      onClick={() => setShowSaveModal(true)}
                    >
                      💾 Salvar Filtro
                    </button>
                    <button
                      type="button"
                      className={styles.quickSelectPill}
                      title="Baixar catálogo em CSV (Excel)"
                      onClick={async () => {
                        try {
                          await api.downloadCatalogCsv();
                          toast.success('Catálogo exportado em CSV!', 'Exportado!');
                        } catch (err: any) {
                          toast.error(err.message || 'Erro ao exportar CSV.');
                        }
                      }}
                    >
                      ⬇️ Exportar CSV
                    </button>
                  </div>
                  <select
                    className={styles.controlInput}
                    style={{ width: 'auto', padding: '6px 12px' }}
                    value={filters.sort}
                    onChange={(e) => {
                      const nextFilters = { ...filters, sort: e.target.value };
                      setFilters(nextFilters);
                      executeSearch(1, false, nextFilters);
                    }}
                  >
                    <option value="created_at_desc">Mais Recentes</option>
                    <option value="created_at_asc">Mais Antigos</option>
                    <option value="budget_desc">Maior Orçamento</option>
                    <option value="budget_asc">Menor Orçamento</option>
                    <option value="bids_asc">Menos Concorridos</option>
                    <option value="bids_desc">Mais Concorridos</option>
                    <option value="ranking">Ranking</option>
                  </select>
                </div>
              )}

              <div className={`${styles.missionGrid} reveal-grid`}>
                {projects.map((project, index) => {
                  const matchScore = calculateMatch(project);
                  const isNew = Boolean(project.posted_at && project.posted_at.includes('m'));
                  const isSelected = selectedProject?.id === project.id;
                  const isBatchSelected = isProjectSelected(project.id);
                  const analysis = project.analysis ?? analysisById[project.id] ?? null;

                  return (
                    <ProjectCard
                      key={project.id}
                      project={project}
                      index={index}
                      isSelected={isSelected}
                      isBatchSelected={isBatchSelected}
                      matchScore={matchScore}
                      isNew={isNew}
                      analysis={analysis}
                      onSelectProject={handleSelectProject}
                      onToggleBatchSelection={toggleProjectSelection}
                      onOpenBidsHistory={openBidsHistory}
                      onGenerateAiProposal={(id) => handleOpenProposalModal(id)}
                    />
                  );
                })}
              </div>

              {totalPages > 1 && (
                <div className={styles.pagination} aria-label="Paginação dos projetos">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => executeSearch(page - 1)}
                    disabled={page <= 1 || isSearching}
                  >
                    Anterior
                  </button>
                  <span>
                    Página {page} de {totalPages}
                  </span>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => executeSearch(page + 1)}
                    disabled={page >= totalPages || isSearching}
                  >
                    Próxima
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Modais Extraídos */}
      <ProjectDetailModal
        project={selectedProject}
        templates={templates}
        selectedTemplateId={selectedTemplateId}
        priceLevel={priceLevel}
        onClose={() => setSelectedProject(null)}
        onGenerateProposal={(id, tRef, pLevel) => handleOpenProposalModal(id, tRef, pLevel, false)}
      />

      <ProposalModal
        isOpen={showAiModal}
        templates={templates}
        selectedTemplateId={selectedTemplateId}
        priceLevel={priceLevel}
        versions={proposalVersions}
        activeVersionId={activeVersionId}
        isGenerating={isGeneratingAi}
        isSubmitting={isSubmittingProposal}
        isSaving={isSavingDraft}
        error={aiError}
        proposalData={aiProposal}
        budget={modalBudget}
        deadline={modalDeadline}
        onClose={() => setShowAiModal(false)}
        onTemplateChange={(ref) => {
          setSelectedTemplateId(ref);
          if (ref) sessionStorage.setItem('preferred_generation_template_id', ref);
          else sessionStorage.removeItem('preferred_generation_template_id');
        }}
        onPriceLevelChange={(level) => {
          setPriceLevel(level);
        }}
        onSelectVersion={handleSelectProposalVersion}
        onDeleteVersion={handleDeleteProposalVersion}
        onGenerateNewVersion={() => {
          if (currentGeneratingProjectId) {
            handleGenerateAiProposal(
              currentGeneratingProjectId,
              selectedTemplateId,
              priceLevel,
              true
            );
          }
        }}
        onProposalChange={(text) => {
          setAiProposal((prev) => (prev ? { ...prev, proposal: text } : null));
        }}
        onBudgetChange={setModalBudget}
        onDeadlineChange={setModalDeadline}
        onCopy={handleCopyProposal}
        onSaveDraft={handleSaveProposalDraft}
        onSubmit={handleSubmitProposal}
      />

      <BatchCreateModal
        isOpen={showBatchModal}
        batchItems={batchItems}
        templates={templates}
        batchTemplateRef={batchTemplateRef}
        isBatchGenerating={isBatchGenerating}
        isSubmittingBatch={isSubmittingBatch}
        onClose={() => setShowBatchModal(false)}
        onTemplateChange={setBatchTemplateRef}
        onRegenerateAll={handleOpenBatchReviewModal}
        onItemToggle={(idx, val) =>
          setBatchItems((prev) => prev.map((it, i) => (i === idx ? { ...it, selected: val } : it)))
        }
        onItemTextChange={(idx, val) =>
          setBatchItems((prev) =>
            prev.map((it, i) => (i === idx ? { ...it, proposal_text: val } : it))
          )
        }
        onItemBudgetChange={(idx, val) =>
          setBatchItems((prev) => prev.map((it, i) => (i === idx ? { ...it, budget: val } : it)))
        }
        onItemDeadlineChange={(idx, val) =>
          setBatchItems((prev) =>
            prev.map((it, i) => (i === idx ? { ...it, deadline_days: val } : it))
          )
        }
        onSubmit={handleSubmitBatchToQueue}
      />

      <BidsHistoryModal
        data={bidsData}
        isLoading={bidsLoading}
        onClose={() => setBidsProject(null)}
      />

      <SaveFilterModal
        isOpen={showSaveModal}
        currentFiltersCount={Object.keys(toCatalogFilters(filters)).length}
        onClose={() => setShowSaveModal(false)}
        onSave={handleSaveFilter}
      />

      <QueueDrawerModal
        isOpen={showQueueDrawer}
        batches={batches}
        isLoading={isLoadingBatches}
        selectedBatchDetail={selectedBatchDetail}
        onClose={() => setShowQueueDrawer(false)}
        onSelectBatch={loadBatchDetail}
        onCancelBatch={handleCancelBatch}
        onRetryBatch={handleRetryBatch}
      />
    </div>
  );
}
