import React from 'react';
import Loader from '../Loader';
import { ProposalBatch } from '../../services/api';
import styles from '../../pages/Projects.module.css';
import { MaterialIcon } from '../ui/MaterialIcon';

interface QueueDrawerModalProps {
  isOpen: boolean;
  batches: ProposalBatch[];
  isLoading: boolean;
  selectedBatchDetail: ProposalBatch | null;
  onClose: () => void;
  onSelectBatch: (batchId: number) => void;
  onCancelBatch: (batchId: number) => void;
  onRetryBatch: (batchId: number) => void;
}

export const QueueDrawerModal: React.FC<QueueDrawerModalProps> = ({
  isOpen,
  batches,
  isLoading,
  selectedBatchDetail,
  onClose,
  onSelectBatch,
  onCancelBatch,
  onRetryBatch,
}) => {
  if (!isOpen) return null;

  return (
    <div className={styles.queueDrawerOverlay} onClick={onClose}>
      <div className={styles.queueDrawerContainer} onClick={(e) => e.stopPropagation()}>
        <div className={styles.queueDrawerHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3
              style={{
                margin: 0,
                fontSize: '1.2rem',
                color: '#f1f5f9',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <MaterialIcon name="format_list_bulleted" size={22} />
              Fila de Envios & Lotes
            </h3>
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className={styles.queueDrawerBody}>
          {isLoading && batches.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <Loader type="scanning" message="Consultando status da fila..." />
            </div>
          ) : batches.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px 20px', textAlign: 'center' }}>
              <div style={{ marginBottom: '12px', color: '#94a3b8' }}>
                <MaterialIcon name="inbox" size={48} />
              </div>
              <h4 style={{ color: '#94a3b8', margin: '0 0 8px' }}>Nenhum lote na fila</h4>
              <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
                Selecione projetos no catálogo e clique em "Gerar e Revisar em Lote" ou "Enfileirar
                Direto" para disparar propostas.
              </p>
            </div>
          ) : (
            batches.map((batch) => {
              const percent =
                batch.total > 0
                  ? Math.round(
                      ((batch.sent_count + batch.failed_count + batch.skipped_count) /
                        batch.total) *
                        100
                    )
                  : 0;
              const isSelected = selectedBatchDetail?.id === batch.id;
              return (
                <div
                  key={batch.id}
                  className={styles.queueBatchCard}
                  style={{
                    borderColor: isSelected ? 'var(--color-primary)' : 'rgba(255,255,255,0.08)',
                  }}
                  onClick={() => onSelectBatch(batch.id)}
                >
                  <div className={styles.queueBatchTop}>
                    <div>
                      <span className={styles.queueBatchTitle}>Lote #{batch.id}</span>
                      <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '8px' }}>
                        {batch.created_at ? new Date(batch.created_at).toLocaleTimeString() : ''}
                      </span>
                    </div>
                    <span
                      className={`${styles.queueStatusBadge} ${
                        batch.status === 'completed'
                          ? styles.statusSent
                          : batch.status === 'running'
                            ? styles.statusSending
                            : batch.status === 'cancelled'
                              ? styles.statusCancelled
                              : batch.status === 'failed'
                                ? styles.statusFailed
                                : styles.statusQueued
                      }`}
                    >
                      {batch.status === 'completed'
                        ? 'Concluído'
                        : batch.status === 'running'
                          ? 'Em Envio'
                          : batch.status === 'cancelled'
                            ? 'Cancelado'
                            : batch.status === 'failed'
                              ? 'Falhou'
                              : 'Na Fila'}
                    </span>
                  </div>

                  <div className={styles.queueProgressTrack}>
                    <div className={styles.queueProgressBar} style={{ width: `${percent}%` }}></div>
                  </div>

                  <div className={styles.queueStatsRow}>
                    <span>
                      Progresso: {batch.sent_count}/{batch.total} enviadas
                    </span>
                    <span>{percent}% concluído</span>
                  </div>

                  {batch.failed_count > 0 && (
                    <div
                      style={{
                        fontSize: '0.78rem',
                        color: '#f87171',
                        marginTop: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <MaterialIcon name="warning" size={14} />
                      {batch.failed_count} proposta(s) falharam
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    {batch.status === 'running' || batch.status === 'queued' ? (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{
                          color: '#f87171',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          padding: '4px 10px',
                          fontSize: '0.75rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onCancelBatch(batch.id);
                        }}
                      >
                        <MaterialIcon name="cancel" size={14} />
                        Cancelar
                      </button>
                    ) : null}

                    {batch.failed_count > 0 ||
                    batch.status === 'cancelled' ||
                    batch.status === 'failed' ? (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{
                          padding: '4px 10px',
                          fontSize: '0.75rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onRetryBatch(batch.id);
                        }}
                      >
                        <MaterialIcon name="replay" size={14} />
                        Reenviar Falhas
                      </button>
                    ) : null}

                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      style={{ marginLeft: 'auto', padding: '4px 10px', fontSize: '0.75rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectBatch(batch.id);
                      }}
                    >
                      {isSelected ? 'Ocultar Detalhes' : 'Ver Itens ▾'}
                    </button>
                  </div>

                  {isSelected && selectedBatchDetail?.items && (
                    <div
                      style={{
                        marginTop: '14px',
                        borderTop: '1px solid rgba(255,255,255,0.06)',
                        paddingTop: '10px',
                      }}
                    >
                      <div
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          color: '#94a3b8',
                          marginBottom: '8px',
                        }}
                      >
                        Itens do Lote ({selectedBatchDetail.items.length}):
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {selectedBatchDetail.items.map((item) => (
                          <div key={item.id} className={styles.queueItemRow}>
                            <div
                              style={{
                                flex: 1,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                paddingRight: '10px',
                              }}
                            >
                              <a
                                href={
                                  item.project_url ||
                                  `https://www.workana.com/job/${item.workana_id}`
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: '#e2e8f0', textDecoration: 'none' }}
                              >
                                {item.project_title || item.workana_id}
                              </a>
                              {item.error && (
                                <div
                                  style={{
                                    fontSize: '0.72rem',
                                    color: '#f87171',
                                    marginTop: '2px',
                                  }}
                                >
                                  {item.error}
                                </div>
                              )}
                            </div>
                            <span
                              className={`${styles.queueStatusBadge} ${
                                item.status === 'sent'
                                  ? styles.statusSent
                                  : item.status === 'sending'
                                    ? styles.statusSending
                                    : item.status === 'ready'
                                      ? styles.statusReady
                                      : item.status === 'generating'
                                        ? styles.statusGenerating
                                        : item.status === 'failed'
                                          ? styles.statusFailed
                                          : item.status === 'skipped'
                                            ? styles.statusSkipped
                                            : item.status === 'cancelled'
                                              ? styles.statusCancelled
                                              : styles.statusQueued
                              }`}
                            >
                              {item.status === 'sent'
                                ? 'Enviada'
                                : item.status === 'sending'
                                  ? 'Enviando...'
                                  : item.status === 'ready'
                                    ? 'Pronta'
                                    : item.status === 'generating'
                                      ? 'Gerando IA'
                                      : item.status === 'failed'
                                        ? 'Falhou'
                                        : item.status === 'skipped'
                                          ? 'Ignorada'
                                          : item.status === 'cancelled'
                                            ? 'Cancelada'
                                            : 'Na Fila'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
