import { useState, useEffect } from 'react';
import styles from './History.module.css';
import { api } from '../services/api';
import { useToast } from '../context/ToastContext';
import Loader from '../components/Loader';
import CyberHeader from '../components/CyberHeader';
import { MaterialIcon } from '../components/ui/MaterialIcon';

interface ProposalHistory {
  id: number;
  project_id: string;
  project_title: string;
  project_url?: string;
  budget: number;
  deadline_days: number;
  status: 'generated' | 'sent' | 'viewed' | 'accepted' | 'rejected';
  sent_at: string;
  message?: string;
}

const COLUMNS = [
  { id: 'generated', label: 'Geradas (AI)', color: 'var(--color-accent)' },
  { id: 'sent', label: 'Enviadas', color: 'var(--color-text-secondary)' },
  { id: 'viewed', label: 'Visualizada', color: 'var(--color-info)' },
  { id: 'accepted', label: 'Aceita', color: 'var(--color-success)' },
  { id: 'rejected', label: 'Rejeitada', color: 'var(--color-error)' },
];

export default function History() {
  const { toast } = useToast();
  const [history, setHistory] = useState<ProposalHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [draggedItem, setDraggedItem] = useState<ProposalHistory | null>(null);
  const [selectedProposal, setSelectedProposal] = useState<ProposalHistory | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await api.getProposalHistory();
      setHistory(data);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
      toast.error('Erro ao carregar histórico de propostas.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async (item: ProposalHistory) => {
    setIsRegenerating(true);
    try {
      const response = await api.generateProposal(item.project_id);
      if (response.success && response.proposal) {
        toast.success('Proposta regenerada com sucesso!');
        // Update local state immediately
        const updatedItem = { ...item, message: response.proposal };
        setSelectedProposal(updatedItem);
        setHistory((prev) =>
          prev.map((h) => (h.id === item.id ? { ...h, message: response.proposal } : h))
        );

        // Optionally refetch full history to get new ID if backend creates new entry
        // But for UX speed, local update is better first.
        // ideally we should reload history in background
        fetchHistory();
      } else {
        toast.error('Erro ao regenerar proposta: ' + response.error);
      }
    } catch (error) {
      console.error('Erro ao regenerar:', error);
      toast.error('Falha ao comunicar com o servidor.');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleDragStart = (e: React.DragEvent, item: ProposalHistory) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
    // Make ghost image cleaner if needed
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e: React.DragEvent, status: string) => {
    e.preventDefault();

    if (!draggedItem || draggedItem.status === status) return;

    // Optimistic update
    const originalStatus = draggedItem.status;
    const updatedHistory = history.map((item) =>
      item.id === draggedItem.id ? { ...item, status: status as any } : item
    );
    setHistory(updatedHistory);
    setDraggedItem(null);

    try {
      await api.updateProposalStatus(draggedItem.id, status);
      toast.success(`Proposta movida para ${COLUMNS.find((c) => c.id === status)?.label}`);
    } catch (error) {
      console.error('Failed to update status', error);
      toast.error('Erro ao atualizar status.');
      // Revert
      setHistory(
        history.map((item) =>
          item.id === draggedItem.id ? { ...item, status: originalStatus } : item
        )
      );
    }
  };

  const formatCurrency = (value: number) => {
    return value.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Loader />
        <p className="mt-md text-muted">Carregando pipeline...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <CyberHeader
        title="HISTÓRICO DE PROPOSTAS"
        subtitle="PROPOSTAS // ACOMPANHAMENTO"
        description="Gerencie o fluxo e o status das suas propostas enviadas. Arraste os cards para atualizar."
      />

      <div className={styles.kanbanBoard}>
        {COLUMNS.map((column) => {
          const items = history.filter((h) => h.status === column.id);
          return (
            <div
              key={column.id}
              className={styles.column}
              data-status={column.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column.id)}
            >
              <div className={styles.columnHeader}>
                <span className={styles.columnTitle}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: column.color,
                    }}
                  />
                  {column.label}
                </span>
                <span className={styles.columnCount}>{items.length}</span>
              </div>
              <div className={styles.columnContent}>
                {items.map((item) => (
                  <div
                    key={item.id}
                    className={styles.card}
                    draggable
                    onDragStart={(e) => handleDragStart(e, item)}
                    onClick={() => setSelectedProposal(item)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className={styles.cardHeader}>
                      <span className={styles.projectTitle} title={item.project_title}>
                        {item.project_title}
                      </span>
                    </div>
                    <div className={styles.cardMeta}>
                      <span className={styles.budget}>{formatCurrency(item.budget)}</span>
                      <span
                        className={styles.date}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                      >
                        <MaterialIcon name="schedule" size={13} />
                        {formatDate(item.sent_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {selectedProposal && (
        <div className={styles.modalOverlay} onClick={() => setSelectedProposal(null)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <span className={styles.modalTitle}>{selectedProposal.project_title}</span>
              <button className={styles.modalClose} onClick={() => setSelectedProposal(null)}>
                <MaterialIcon name="close" size={20} />
              </button>
            </div>
            <div className={styles.modalContent}>
              {isRegenerating ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '2rem',
                  }}
                >
                  <Loader />
                  <p>Gerando nova proposta com IA...</p>
                </div>
              ) : (
                selectedProposal.message || 'Conteúdo indisponível.'
              )}
            </div>
            <div className={styles.modalActions}>
              <button
                className={`${styles.button} ${styles.secondaryButton}`}
                onClick={() => handleRegenerate(selectedProposal)}
                disabled={isRegenerating}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <MaterialIcon name="sync" size={16} />
                Regenerar
              </button>
              <button
                className={`${styles.button} ${styles.secondaryButton}`}
                onClick={() => {
                  if (selectedProposal.message) {
                    navigator.clipboard.writeText(selectedProposal.message);
                    toast.success('Proposta copiada!');
                  }
                }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <MaterialIcon name="content_copy" size={16} />
                Copiar Texto
              </button>
              {selectedProposal.project_url && (
                <a
                  href={selectedProposal.project_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${styles.button} ${styles.ctaButton}`}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <MaterialIcon name="open_in_new" size={16} />
                  Ver no Workana
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
