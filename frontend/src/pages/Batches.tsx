import { useState, useEffect, useCallback } from 'react';
import styles from './Batches.module.css';
import { api, type ProposalBatch } from '../services/api';
import { useToast } from '../context/ToastContext';
import Loader from '../components/Loader';
import CyberHeader from '../components/CyberHeader';
import {
  ProposalEditorModal,
  STATUS_LABELS as PROPOSAL_STATUS_LABELS,
  type ProposalEditorTarget,
} from '../components/batches/ProposalEditorModal';

type Batch = any;
type BatchItem = any;

interface SavedProposal {
  id: number;
  project_id: string;
  project_title: string;
  project_url?: string;
  message?: string;
  budget: number;
  deadline_days: number;
  status: string;
  sent_at?: string;
  template_slug?: string;
  template_type?: string;
}

const STATUS_LABELS: Record<string, string> = {
  queued: 'Em fila',
  running: 'Processando',
  completed: 'Concluído',
  cancelled: 'Cancelado',
  failed: 'Falhou',
};

const STATUS_COLORS: Record<string, string> = {
  queued: 'var(--color-text-muted)',
  running: 'var(--color-info)',
  completed: 'var(--color-success)',
  cancelled: 'var(--color-text-muted)',
  failed: 'var(--color-error)',
};

// Mapeia qualquer status para uma classe de pílula conhecida no CSS
const PILL_CLASS_KEYS: Record<string, string> = {
  generated: 'generated',
  draft: 'draft',
  ready: 'ready',
  queued: 'queued',
  sending: 'queued',
  generating: 'queued',
  sent: 'sent',
  viewed: 'sent',
  accepted: 'sent',
  failed: 'failed',
  skipped: 'failed',
  cancelled: 'failed',
  rejected: 'failed',
};

const PROPOSAL_STATUS_FILTER = [
  { value: '', label: 'Todos os status' },
  { value: 'draft', label: 'Rascunhos' },
  { value: 'sent', label: 'Enviadas' },
  { value: 'failed', label: 'Com falha' },
];

const isDraftStatus = (status: string) =>
  ['generated', 'draft', 'ready', 'queued'].includes(status);

export default function Batches() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'proposals' | 'batches'>('proposals');

  // Propostas salvas (rascunhos + enviadas)
  const [proposals, setProposals] = useState<SavedProposal[]>([]);
  const [proposalsTotal, setProposalsTotal] = useState(0);
  const [proposalsLoading, setProposalsLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [proposalsQuery, setProposalsQuery] = useState('');
  const [proposalsStatus, setProposalsStatus] = useState('');
  const [editorItem, setEditorItem] = useState<ProposalEditorTarget | null>(null);
  const [swapBusy, setSwapBusy] = useState<'save' | 'send' | null>(null);

  // Lotes de propostas
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
      console.error('Erro ao carregar lotes:', error);
      toast.error('Erro ao carregar lotes de propostas.');
    }
  }, [statusFilter, toast]);

  const fetchProposals = useCallback(async () => {
    setProposalsLoading(true);
    try {
      const data = await api.getAllProposals({
        q: proposalsQuery || undefined,
        status: proposalsStatus || undefined,
        limit: 100,
      });
      setProposals(data.proposals || []);
      setProposalsTotal(data.total || 0);
    } catch (error) {
      console.error('Erro ao carregar propostas:', error);
      toast.error('Erro ao carregar propostas salvas.');
    } finally {
      setProposalsLoading(false);
    }
  }, [proposalsQuery, proposalsStatus, toast]);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchBatches(), fetchProposals()]).finally(() => {
      setIsLoading(false);
    });
  }, [fetchBatches, fetchProposals]);

  const handleSelectBatch = async (batch: Batch) => {
    setSelectedBatch(batch);
    setIsLoadingItems(true);
    try {
      const items = await api.getBatchItems(batch.id);
      setBatchItems(items);
    } catch (error) {
      console.error('Erro ao carregar itens:', error);
      toast.error('Erro ao carregar itens do lote.');
    } finally {
      setIsLoadingItems(false);
    }
  };

  const handleStartBatch = async (batchId: number) => {
    try {
      const result = await api.startBatch(batchId);
      if (result.success) {
        toast.success(`Lote ${batchId} iniciado: ${result.status}`);
        if (selectedBatch?.id === batchId) {
          setSelectedBatch((prev: ProposalBatch | null) =>
            prev ? { ...prev, status: result.status } : null
          );
        }
        fetchBatches();
      }
    } catch (error: any) {
      toast.error(error.message || 'Erro ao iniciar lote.');
    }
  };

  const handleSwitchTab = (tab: 'proposals' | 'batches') => {
    setActiveTab(tab);
    if (tab === 'proposals') {
      setSelectedBatch(null);
    } else {
      setEditorItem(null);
    }
  };

  const openEditor = (proposal: SavedProposal) => {
    setEditorItem({
      id: proposal.id,
      project_id: proposal.project_id,
      project_title: proposal.project_title,
      project_url: proposal.project_url,
      message: proposal.message,
      budget: proposal.budget,
      deadline_days: proposal.deadline_days,
      status: proposal.status,
      sent_at: proposal.sent_at,
      template_slug: proposal.template_slug,
      template_type: proposal.template_type,
    });
  };

  const handleSaveProposal = async (text: string, budget: number, deadlineDays: number) => {
    if (!editorItem) return;
    setSwapBusy('save');
    try {
      const result = await api.saveProjectProposal(editorItem.project_id, {
        proposal_text: text,
        budget,
        deadline_days: deadlineDays,
        add_to_batch: true,
      });
      toast.success(result.message || 'Rascunho salvo com sucesso!');
      fetchProposals();
    } catch (error: any) {
      toast.error(error.message || 'Erro ao salvar rascunho.');
    } finally {
      setSwapBusy(null);
    }
  };

  const handleSendProposal = async (text: string, budget: number, deadlineDays: number) => {
    if (!editorItem) return;
    setSwapBusy('send');
    try {
      const result = await api.submitProposal(editorItem.project_id, {
        project_id: editorItem.project_id,
        custom_message: text,
        budget,
        deadline_days: deadlineDays,
      });
      if (result.success) {
        toast.success(result.message || 'Proposta enviada com sucesso!');
        setEditorItem(null);
      } else {
        toast.error(result.message || 'Falha ao enviar proposta.');
      }
      fetchProposals();
    } catch (error: any) {
      toast.error(error.message || 'Erro ao enviar proposta.');
    } finally {
      setSwapBusy(null);
    }
  };

  const handleQuickSend = async (proposal: SavedProposal) => {
    if (!proposal.message) return;
    try {
      const result = await api.submitProposal(proposal.project_id, {
        project_id: proposal.project_id,
        custom_message: proposal.message,
        budget: proposal.budget,
        deadline_days: proposal.deadline_days,
      });
      if (result.success) {
        toast.success(result.message || 'Proposta enviada com sucesso!');
      } else {
        toast.error(result.message || 'Falha ao enviar proposta.');
      }
      fetchProposals();
    } catch (error: any) {
      toast.error(error.message || 'Erro ao enviar proposta.');
    }
  };

  const handleDeleteProposal = async () => {
    if (!editorItem) return;
    if (!window.confirm(`Excluir a proposta do projeto "${editorItem.project_title}"?`)) return;
    try {
      const result = await api.deleteProposal(editorItem.id);
      toast.success(result.message || 'Proposta excluída com sucesso.');
      setEditorItem(null);
      fetchProposals();
    } catch (error: any) {
      toast.error(error.message || 'Erro ao excluir proposta.');
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (value: number) => {
    if (!value && value !== 0) return '—';
    return value.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <CyberHeader
          title="LOTES DE PROPOSTAS"
          subtitle="AUTOMAÇÃO // BATCHES"
          description="Gerencie propostas salvas como rascunhos e envios em massa no Workana"
        />
        <Loader type="overlay" message="Carregando propostas..." />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <CyberHeader
        title="LOTES DE PROPOSTAS"
        subtitle="AUTOMAÇÃO // BATCHES"
        description="Gerencie propostas salvas como rascunhos e envios em massa no Workana"
      />

      {/* Abas */}
      <div className={styles.tabsContainer}>
        <button
          className={`${styles.tabButton} ${activeTab === 'proposals' ? styles.activeTab : ''}`}
          onClick={() => handleSwitchTab('proposals')}
        >
          📝 Propostas
          {proposalsTotal > 0 && <span className={styles.tabBadge}>{proposalsTotal}</span>}
        </button>
        <button
          className={`${styles.tabButton} ${activeTab === 'batches' ? styles.activeTab : ''}`}
          onClick={() => handleSwitchTab('batches')}
        >
          📦 Lotes
          {batches.length > 0 && <span className={styles.tabBadge}>{batches.length}</span>}
        </button>
      </div>

      {activeTab === 'proposals' && (
        <div>
          {/* Filtros */}
          <div className={styles.toolbar}>
            <div className={styles.filterGroup}>
              <div className={styles.searchBox}>
                <input
                  type="text"
                  placeholder="Buscar por título ou ID do projeto..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setProposalsQuery(searchInput.trim());
                  }}
                />
              </div>
              <select
                className={styles.select}
                value={proposalsStatus}
                onChange={(e) => setProposalsStatus(e.target.value)}
              >
                {PROPOSAL_STATUS_FILTER.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <button
                className={styles.refreshButton}
                onClick={() => {
                  setProposalsQuery(searchInput.trim());
                }}
              >
                🔍 Buscar
              </button>
            </div>
            <button className={styles.refreshButton} onClick={fetchProposals}>
              🔄 Atualizar
            </button>
          </div>

          {proposalsLoading ? (
            <Loader type="overlay" message="Carregando propostas..." />
          ) : proposals.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📝</div>
              <h3>Nenhuma proposta salva</h3>
              <p>
                Gere ou salve uma proposta a partir dos projetos, ou aguarde o processamento de um
                lote. As propostas ficam guardadas aqui como rascunhos ou enviadas.
              </p>
            </div>
          ) : (
            <div className={styles.proposalsGrid}>
              {proposals.map((proposal) => {
                const pillKey = PILL_CLASS_KEYS[proposal.status] || 'queued';
                return (
                  <div key={proposal.id} className={styles.proposalCard}>
                    <div className={styles.proposalHeader}>
                      <a
                        className={styles.proposalTitleLink}
                        href={
                          proposal.project_url ||
                          `https://www.workana.com/job/${proposal.project_id}`
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        title={proposal.project_title}
                      >
                        {proposal.project_title}
                      </a>
                      <span className={`${styles.statusPill} ${styles[pillKey] || styles.queued}`}>
                        {PROPOSAL_STATUS_LABELS[proposal.status] || proposal.status}
                      </span>
                    </div>

                    <div
                      className={styles.proposalSnippet}
                      onClick={() => openEditor(proposal)}
                      title="Clique para ver ou editar"
                    >
                      {proposal.message || 'Sem texto de proposta salvo ainda.'}
                    </div>

                    <div className={styles.proposalMetaGrid}>
                      <div className={styles.proposalMetaItem}>
                        <span className={styles.metaLabel}>Valor</span>
                        <span className={styles.metaValue}>{formatCurrency(proposal.budget)}</span>
                      </div>
                      <div className={styles.proposalMetaItem}>
                        <span className={styles.metaLabel}>Prazo</span>
                        <span className={styles.metaValue}>
                          {proposal.deadline_days || '—'} dias
                        </span>
                      </div>
                      <div className={styles.proposalMetaItem}>
                        <span className={styles.metaLabel}>Projeto</span>
                        <span className={styles.metaValue}>{proposal.project_id}</span>
                      </div>
                      <div className={styles.proposalMetaItem}>
                        <span className={styles.metaLabel}>Salvo</span>
                        <span className={styles.metaValue}>
                          {formatDate(proposal.sent_at || '')}
                        </span>
                      </div>
                    </div>

                    <div className={styles.proposalCardActions}>
                      <button className={styles.btnAction} onClick={() => openEditor(proposal)}>
                        {isDraftStatus(proposal.status) ? '✏️ Ver / Editar' : '👁 Visualizar'}
                      </button>
                      {isDraftStatus(proposal.status) && proposal.message && (
                        <button
                          className={`${styles.btnAction} ${styles.btnActionPrimary}`}
                          onClick={() => handleQuickSend(proposal)}
                        >
                          🚀 Enviar
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'batches' && (
        <div>
          {/* Filtros */}
          <div className={styles.toolbar}>
            <div className={styles.filterGroup}>
              <label>Filtrar por status:</label>
              <select
                className={styles.select}
                value={statusFilter || ''}
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

            <button className={styles.refreshButton} onClick={fetchBatches}>
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
              {batches.map((batch) => (
                <div
                  key={batch.id}
                  className={`${styles.batchCard} ${selectedBatch?.id === batch.id ? styles.selected : ''}`}
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
                      {batch.started_at && <span>Iniciado: {formatDate(batch.started_at)}</span>}
                      {batch.finished_at && (
                        <span>Finalizado: {formatDate(batch.finished_at)}</span>
                      )}
                    </div>

                    {batch.error && <div className={styles.batchError}>Erro: {batch.error}</div>}

                    {batch.template_ref && (
                      <div className={styles.batchTemplate}>
                        Template: <code>{batch.template_ref}</code>
                      </div>
                    )}
                  </div>

                  {batch.status === 'queued' && (
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
                <button className={styles.closeButton} onClick={() => setSelectedBatch(null)}>
                  ✕
                </button>
              </div>

              <div className={styles.detailStatus}>
                Status:{' '}
                <strong>{STATUS_LABELS[selectedBatch.status] || selectedBatch.status}</strong>
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
                  <div>
                    <strong>Iniciado em:</strong> {formatDate(selectedBatch.started_at)}
                  </div>
                </div>
              )}
              {selectedBatch.finished_at && (
                <div className={styles.detailMeta}>
                  <div>
                    <strong>Finalizado em:</strong> {formatDate(selectedBatch.finished_at)}
                  </div>
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
                    {batchItems.map((item) => (
                      <div key={item.id} className={styles.itemRow}>
                        <div className={styles.itemInfo}>
                          <span className={styles.itemWorkanaId}>{item.workana_id}</span>
                          <span className={styles.itemTitle}>{item.project_title}</span>
                        </div>
                        <div className={styles.itemStatus}>
                          <span className={`${styles.itemStatusBadge} ${styles[item.status]}`}>
                            {item.status}
                          </span>
                          {item.status === 'sent' && (
                            <span className={styles.itemPrice}>
                              {formatCurrency(item.budget)} • {item.deadline_days}d
                            </span>
                          )}
                          {item.status === 'failed' && item.error && (
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
                <div className={styles.noItems}>Sem itens neste lote.</div>
              )}

              {selectedBatch.status === 'queued' && (
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
      )}

      {/* Editor de proposta (rascunho/envio) */}
      <ProposalEditorModal
        item={editorItem}
        isSaving={swapBusy === 'save'}
        isSending={swapBusy === 'send'}
        onClose={() => setEditorItem(null)}
        onSave={handleSaveProposal}
        onSend={handleSendProposal}
        onDelete={handleDeleteProposal}
      />
    </div>
  );
}
