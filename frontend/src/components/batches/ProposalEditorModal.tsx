import { useEffect, useState } from 'react';
import styles from '../../pages/Batches.module.css';
import { MaterialIcon } from '../ui/MaterialIcon';

export interface ProposalEditorTarget {
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

interface ProposalEditorModalProps {
  item: ProposalEditorTarget | null;
  isSaving: boolean;
  isSending: boolean;
  onClose: () => void;
  onSave: (text: string, budget: number, deadlineDays: number) => void;
  onSend: (text: string, budget: number, deadlineDays: number) => void;
  onDelete: () => void;
}

export const STATUS_LABELS: Record<string, string> = {
  generated: 'Rascunho',
  draft: 'Rascunho',
  ready: 'Pronta',
  queued: 'Na fila',
  generating: 'Gerando',
  sending: 'Enviando',
  sent: 'Enviada',
  failed: 'Falha',
  skipped: 'Ignorada',
  cancelled: 'Cancelada',
  viewed: 'Visualizada',
  accepted: 'Aceita',
  rejected: 'Rejeitada',
};

const DRAFT_STATUSES = ['generated', 'draft', 'ready', 'queued'];

export function ProposalEditorModal({
  item,
  isSaving,
  isSending,
  onClose,
  onSave,
  onSend,
  onDelete,
}: ProposalEditorModalProps) {
  const [text, setText] = useState('');
  const [budget, setBudget] = useState('');
  const [deadline, setDeadline] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (item) {
      setText(item.message || '');
      setBudget(item.budget ? String(item.budget) : '');
      setDeadline(item.deadline_days ? String(item.deadline_days) : '7');
      setCopied(false);
    }
  }, [item]);

  if (!item) return null;

  const isDraft = DRAFT_STATUSES.includes(item.status);
  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const parsedBudget = budget ? Number(String(budget).replace(',', '.')) : item.budget || 0;
  const parsedDeadline = deadline ? Number(deadline) : item.deadline_days || 7;

  const handleCopy = async () => {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{
          maxWidth: '920px',
          width: '95vw',
          maxHeight: '92vh',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 35px rgba(99, 102, 241, 0.25)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h3
              className="modal-title"
              style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, maxWidth: '520px' }}
            >
              {item.project_title}
            </h3>
            <span className={`${styles.statusPill} ${styles[item.status] || styles.queued}`}>
              {STATUS_LABELS[item.status] || item.status}
            </span>
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className="modal-body" style={{ padding: '1.25rem 1.5rem' }}>
          <div className={styles.editorMeta}>
            <span style={{ display: 'inline-flex', alignItems: 'center' }}>
              <MaterialIcon name="folder" size={15} style={{ marginRight: '4px' }} />
              Projeto: <strong>{item.project_id}</strong>
            </span>
            {item.project_url && (
              <a
                href={item.project_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.editorLink}
              >
                Ver no Workana ↗
              </a>
            )}
            {item.template_slug && (
              <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                <MaterialIcon name="extension" size={15} style={{ marginRight: '4px' }} />
                Template: <code>{item.template_slug}</code>
              </span>
            )}
          </div>

          <div className={`${styles.editorFields} form-group`} style={{ margin: 0 }}>
            <div className={styles.editorField}>
              <label
                className="form-label"
                style={{ fontWeight: 600, marginBottom: '0.35rem', fontSize: '0.85rem' }}
              >
                Valor da Proposta (R$)
              </label>
              <input
                type="number"
                className="form-input"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="Ex: 4500"
                disabled={!isDraft}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-secondary)',
                  color: 'var(--color-text)',
                  outline: 'none',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                }}
              />
            </div>
            <div className={styles.editorField}>
              <label
                className="form-label"
                style={{ fontWeight: 600, marginBottom: '0.35rem', fontSize: '0.85rem' }}
              >
                Prazo de Entrega (Dias)
              </label>
              <input
                type="number"
                className="form-input"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                placeholder="Ex: 20"
                disabled={!isDraft}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-secondary)',
                  color: 'var(--color-text)',
                  outline: 'none',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                }}
              />
            </div>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.4rem',
              }}
            >
              <label
                className="form-label"
                style={{ fontWeight: 600, margin: 0, fontSize: '0.9rem' }}
              >
                Texto da Proposta {isDraft ? '(Editável)' : '(Somente leitura)'}
              </label>
              <span style={{ fontSize: '0.75rem', opacity: 0.75, fontFamily: 'monospace' }}>
                {charCount.toLocaleString('pt-BR')} caracteres • {wordCount} palavras
              </span>
            </div>
            <textarea
              className="form-input"
              rows={16}
              value={text}
              onChange={(e) => setText(e.target.value)}
              readOnly={!isDraft}
              placeholder="A proposta estruturada aparecerá aqui..."
              style={{
                width: '100%',
                minHeight: '360px',
                maxHeight: '500px',
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg-secondary)',
                color: 'var(--color-text)',
                lineHeight: 1.65,
                fontSize: '0.925rem',
                fontFamily: 'inherit',
                resize: 'vertical',
                whiteSpace: 'pre-wrap',
              }}
            />
          </div>

          <div className={styles.editorActions}>
            <button
              type="button"
              className={styles.editorActionBtn}
              style={{
                backgroundColor: copied ? 'rgba(16, 185, 129, 0.2)' : 'var(--color-bg-tertiary)',
                borderColor: copied ? '#10b981' : 'var(--color-border)',
                color: copied ? '#10b981' : 'var(--color-text)',
              }}
              onClick={handleCopy}
            >
              {copied ? (
                <>
                  <MaterialIcon name="check" size={15} style={{ marginRight: '4px' }} /> Copiado!
                </>
              ) : (
                <>
                  <MaterialIcon name="content_copy" size={15} style={{ marginRight: '4px' }} />{' '}
                  Copiar Texto
                </>
              )}
            </button>

            {isDraft && (
              <button
                type="button"
                className={styles.editorActionBtn}
                onClick={() => onSave(text, parsedBudget, parsedDeadline)}
                disabled={isSaving || !text}
                style={{
                  flex: 1.2,
                  backgroundColor: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  color: '#60a5fa',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isSaving ? (
                  'Salvando...'
                ) : (
                  <>
                    <MaterialIcon name="save" size={15} style={{ marginRight: '4px' }} /> Salvar
                    Rascunho
                  </>
                )}
              </button>
            )}

            {isDraft && (
              <button
                type="button"
                className={styles.editorActionBtn}
                onClick={() => onSend(text, parsedBudget, parsedDeadline)}
                disabled={isSending || !text}
                style={{
                  flex: 1.6,
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  color: '#10b981',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isSending ? (
                  'Enviando...'
                ) : (
                  <>
                    <MaterialIcon name="send" size={15} style={{ marginRight: '4px' }} /> Enviar
                    Proposta
                  </>
                )}
              </button>
            )}

            {isDraft && (
              <button
                type="button"
                className={styles.editorActionBtn}
                onClick={onDelete}
                disabled={isSaving || isSending}
                style={{
                  flex: '0 0 auto',
                  color: '#f87171',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <MaterialIcon name="delete" size={15} style={{ marginRight: '4px' }} /> Excluir
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
