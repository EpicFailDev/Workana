import React from 'react';
import Loader from '../Loader';
import { ProposalTemplate } from '../../services/api';
import styles from '../../pages/Projects.module.css';

export interface BatchReviewItem {
  workana_id: string;
  title: string;
  url: string;
  proposal_text: string;
  budget: number;
  deadline_days: number;
  score: number;
  selected: boolean;
  status: 'ready' | 'generating' | 'error';
  error?: string;
}

interface BatchCreateModalProps {
  isOpen: boolean;
  batchItems: BatchReviewItem[];
  templates: ProposalTemplate[];
  batchTemplateRef: string | null;
  isBatchGenerating: boolean;
  isSubmittingBatch: boolean;
  onClose: () => void;
  onTemplateChange: (ref: string | null) => void;
  onRegenerateAll: () => void;
  onItemToggle: (index: number, selected: boolean) => void;
  onItemTextChange: (index: number, text: string) => void;
  onItemBudgetChange: (index: number, budget: number) => void;
  onItemDeadlineChange: (index: number, days: number) => void;
  onSubmit: () => void;
}

export const BatchCreateModal: React.FC<BatchCreateModalProps> = ({
  isOpen,
  batchItems,
  templates,
  batchTemplateRef,
  isBatchGenerating,
  isSubmittingBatch,
  onClose,
  onTemplateChange,
  onRegenerateAll,
  onItemToggle,
  onItemTextChange,
  onItemBudgetChange,
  onItemDeadlineChange,
  onSubmit,
}) => {
  if (!isOpen) return null;

  const selectedReadyCount = batchItems.filter((i) => i.selected && i.proposal_text.trim()).length;

  return (
    <div className={styles.batchModalOverlay} onClick={() => !isSubmittingBatch && onClose()}>
      <div className={styles.batchModalContainer} onClick={(e) => e.stopPropagation()}>
        <div className={styles.batchModalHeader}>
          <div className={styles.batchModalTitle}>
            <h2>⚡ Envio de Propostas em Lote</h2>
            <span className={styles.batchModalBadge}>
              {batchItems.filter((i) => i.selected).length} de {batchItems.length} selecionados
            </span>
          </div>
          <button
            className="btn-close"
            onClick={() => !isSubmittingBatch && onClose()}
            aria-label="Fechar"
          >
            ×
          </button>
        </div>

        <div className={styles.batchModalToolbar}>
          <div className={styles.batchTemplateSelect}>
            <label>Template de IA:</label>
            <select
              value={batchTemplateRef || ''}
              onChange={(e) => onTemplateChange(e.target.value || null)}
              disabled={isBatchGenerating || isSubmittingBatch}
            >
              <option value="">Prompt Padrão (Sem Template)</option>
              {templates.map((t) => (
                <option key={t.template_ref || t.id} value={t.template_ref || String(t.id)}>
                  {t.name} {t.is_system ? '🛡️ (Oficial)' : ''} {t.is_default ? '⭐' : ''}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={isBatchGenerating || isSubmittingBatch}
              onClick={onRegenerateAll}
              title="Regera todas as propostas usando o template selecionado"
            >
              {isBatchGenerating ? (
                <span className="spinner spinner-sm"></span>
              ) : (
                '✨ Regerar Todas com IA'
              )}
            </button>
          </div>
        </div>

        <div className={styles.batchModalBody}>
          {isBatchGenerating && batchItems.every((i) => i.status === 'generating') ? (
            <div style={{ padding: '60px 20px', textAlign: 'center' }}>
              <Loader
                type="scanning"
                message="Gerando propostas hiper-personalizadas com IA para os projetos selecionados..."
              />
            </div>
          ) : (
            batchItems.map((item, idx) => {
              const scoreClass =
                item.score >= 80
                  ? styles.batchScoreHigh
                  : item.score >= 60
                    ? styles.batchScoreMed
                    : styles.batchScoreLow;
              return (
                <div
                  key={item.workana_id}
                  className={`${styles.batchProjectCard} ${!item.selected ? styles.batchProjectCardDisabled : ''}`}
                >
                  <div className={styles.batchCardTop}>
                    <div className={styles.batchCardTitleGroup}>
                      <input
                        type="checkbox"
                        checked={item.selected}
                        onChange={(e) => onItemToggle(idx, e.target.checked)}
                        disabled={isSubmittingBatch}
                        style={{
                          width: '18px',
                          height: '18px',
                          cursor: 'pointer',
                          accentColor: 'var(--color-primary)',
                        }}
                      />
                      <div>
                        <h4>{item.title}</h4>
                        <div className={styles.batchCardMeta}>
                          <span>Score de Match:</span>
                          <span className={`${styles.batchScoreBadge} ${scoreClass}`}>
                            {item.score}%
                          </span>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: 'var(--color-primary)', textDecoration: 'underline' }}
                          >
                            Ver no Workana ↗
                          </a>
                        </div>
                      </div>
                    </div>
                    {item.status === 'generating' ? (
                      <span className={`${styles.queueStatusBadge} ${styles.statusGenerating}`}>
                        Gerando IA...
                      </span>
                    ) : item.status === 'error' ? (
                      <span className={`${styles.queueStatusBadge} ${styles.statusFailed}`}>
                        Erro IA
                      </span>
                    ) : (
                      <span className={`${styles.queueStatusBadge} ${styles.statusReady}`}>
                        Pronta
                      </span>
                    )}
                  </div>

                  {item.selected && (
                    <>
                      <textarea
                        className={styles.batchProposalTextarea}
                        value={item.proposal_text}
                        placeholder="Texto da proposta personalizada..."
                        onChange={(e) => onItemTextChange(idx, e.target.value)}
                        disabled={isSubmittingBatch || item.status === 'generating'}
                      />
                      <div className={styles.batchInputRow}>
                        <div className={styles.batchInputGroup}>
                          <label>Orçamento (R$):</label>
                          <input
                            type="number"
                            className={styles.batchSmallInput}
                            value={item.budget}
                            onChange={(e) => onItemBudgetChange(idx, Number(e.target.value))}
                            disabled={isSubmittingBatch}
                          />
                        </div>
                        <div className={styles.batchInputGroup}>
                          <label>Prazo (dias):</label>
                          <input
                            type="number"
                            className={styles.batchSmallInput}
                            style={{ width: '80px' }}
                            value={item.deadline_days}
                            onChange={(e) => onItemDeadlineChange(idx, Number(e.target.value))}
                            disabled={isSubmittingBatch}
                          />
                        </div>
                      </div>
                    </>
                  )}
                </div>
              );
            })
          )}
        </div>

        <div className={styles.batchModalFooter}>
          <div className={styles.batchFooterInfo}>
            <span>
              🛡️ O envio será executado sequencialmente com proteção anti-ban e delays inteligentes.
            </span>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
              disabled={isSubmittingBatch}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onSubmit}
              disabled={isSubmittingBatch || isBatchGenerating || selectedReadyCount === 0}
              style={{
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                boxShadow: '0 0 15px rgba(16, 185, 129, 0.35)',
              }}
            >
              {isSubmittingBatch ? (
                <span className="spinner spinner-sm"></span>
              ) : (
                `🚀 Iniciar Disparo em Fila (${selectedReadyCount})`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
