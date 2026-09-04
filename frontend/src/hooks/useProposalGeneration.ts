import { useState } from 'react';
import { api, type ProposalVersion } from '../services/api';
import { useToast } from '../context/ToastContext';
import { useExtensionBridge } from './useExtensionBridge';

export interface AiProposalState {
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
}

interface UseProposalGenerationOptions {
  selectedTemplateId: string | null;
  setSelectedTemplateId: (id: string | null) => void;
  priceLevel: 'budget' | 'standard' | 'premium';
  setPriceLevel: (level: 'budget' | 'standard' | 'premium') => void;
}

export function useProposalGeneration({
  selectedTemplateId,
  setSelectedTemplateId,
  priceLevel,
  setPriceLevel,
}: UseProposalGenerationOptions) {
  const { toast } = useToast();
  const { isExtensionActive, extensionVersion, isSendingViaExtension, sendViaExtension } =
    useExtensionBridge();

  const [showAiModal, setShowAiModal] = useState(false);
  const [aiProposal, setAiProposal] = useState<AiProposalState | null>(null);
  const [proposalVersions, setProposalVersions] = useState<ProposalVersion[]>([]);
  const [activeVersionId, setActiveVersionId] = useState<number | null>(null);
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [isSubmittingProposal, setIsSubmittingProposal] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [modalBudget, setModalBudget] = useState<string>('500');
  const [modalDeadline, setModalDeadline] = useState<string>('7');
  const [proposalTone, setProposalTone] = useState<
    'consultivo' | 'persuasivo' | 'direto' | 'tecnico'
  >('consultivo');
  const [currentGeneratingProjectId, setCurrentGeneratingProjectId] = useState<string | null>(null);

  const openAiModal = async (
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
        const versionsList: ProposalVersion[] =
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
      generateAiProposal(projectId, templateRef, level, true);
    }
  };

  const generateAiProposal = async (
    projectId: string,
    templateRef?: string | null,
    level?: 'budget' | 'standard' | 'premium',
    saveAsNewVersion = true,
    tone?: 'consultivo' | 'persuasivo' | 'direto' | 'tecnico'
  ) => {
    setCurrentGeneratingProjectId(projectId);
    setShowAiModal(true);
    setIsGeneratingAi(true);
    setAiError(null);

    const activeRef = templateRef !== undefined ? templateRef : selectedTemplateId;
    const activeLevel = level || priceLevel;
    const activeTone = tone || proposalTone;

    try {
      const res = await api.generateProposal(
        projectId,
        activeRef || undefined,
        true,
        activeLevel,
        saveAsNewVersion,
        activeTone
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
        toast.success('Nova versão gerada com sucesso!');
      } else {
        setAiError(res.error || 'Não foi possível gerar a proposta.');
      }
    } catch (err: any) {
      setAiError(err.message || 'Erro de conexão ao gerar proposta.');
    } finally {
      setIsGeneratingAi(false);
    }
  };

  const selectProposalVersion = (version: ProposalVersion) => {
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

  const deleteProposalVersion = async (versionId: number) => {
    if (!currentGeneratingProjectId) return;
    try {
      const res = await api.deleteProjectProposalVersion(currentGeneratingProjectId, versionId);
      if (res.success) {
        const nextVersions = res.versions || [];
        setProposalVersions(nextVersions);
        if (nextVersions.length > 0) {
          if (activeVersionId === versionId) {
            selectProposalVersion(nextVersions[0]);
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

  const saveProposalDraft = async () => {
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
        toast.success('Proposta salva com sucesso! Visível em Lotes / Batches.');
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

  const submitProposal = async (forceMode?: 'extension' | 'playwright') => {
    if (!currentGeneratingProjectId || !aiProposal?.proposal) return;
    setIsSubmittingProposal(true);
    try {
      const investmentText = aiProposal.investment_breakdown?.breakdown_text || '';
      const messageToSend =
        investmentText && !aiProposal.proposal.includes(investmentText)
          ? `${aiProposal.proposal}\n\n${investmentText}`
          : aiProposal.proposal;

      const budgetVal = Number(modalBudget) || 500;
      const deadlineVal = Number(modalDeadline) || 7;

      // 1. Priorizar envio direto via extensão (0% risco anti-ban e preenchimento rápido)
      if ((isExtensionActive && forceMode !== 'playwright') || forceMode === 'extension') {
        toast.info('Enviando via Extensão (Modo Seguro Anti-Ban)...');
        const extResult = await sendViaExtension({
          project_id: currentGeneratingProjectId,
          custom_message: messageToSend,
          budget: budgetVal,
          deadline_days: deadlineVal,
          template_id: selectedTemplateId || undefined,
        });

        if (extResult.success) {
          toast.success('Proposta enviada com sucesso no Workana via Extensão (0% Risco)!');
          setShowAiModal(false);
          return;
        } else {
          toast.warning(`Extensão: ${extResult.message}. Tentando via API...`);
        }
      }

      // 2. Fallback ou envio pelo backend
      const res = await api.submitProposal(currentGeneratingProjectId, {
        project_id: currentGeneratingProjectId,
        custom_message: messageToSend,
        budget: budgetVal,
        deadline_days: deadlineVal,
        template_id: selectedTemplateId || undefined,
        dispatch_mode: isExtensionActive ? 'extension' : 'auto',
      });
      if (res.success) {
        toast.success(res.message || 'Proposta processada com sucesso!');
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

  const copyProposal = () => {
    if (aiProposal?.proposal) {
      const investmentText = aiProposal.investment_breakdown?.breakdown_text || '';
      const fullProposal = investmentText
        ? `${aiProposal.proposal}\n\n${investmentText}`
        : aiProposal.proposal;
      navigator.clipboard.writeText(fullProposal);
      toast.success('Proposta completa copiada para a área de transferência!');
    }
  };

  return {
    showAiModal,
    setShowAiModal,
    aiProposal,
    setAiProposal,
    proposalVersions,
    activeVersionId,
    isGeneratingAi,
    isSavingDraft,
    isSubmittingProposal,
    isExtensionActive,
    extensionVersion,
    isSendingViaExtension,
    aiError,
    modalBudget,
    setModalBudget,
    modalDeadline,
    setModalDeadline,
    proposalTone,
    setProposalTone,
    currentGeneratingProjectId,
    openAiModal,
    generateAiProposal,
    selectProposalVersion,
    deleteProposalVersion,
    saveProposalDraft,
    submitProposal,
    copyProposal,
  };
}
