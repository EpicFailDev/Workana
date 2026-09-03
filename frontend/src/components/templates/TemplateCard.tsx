import React from 'react';
import { ChevronRight, FileText } from 'lucide-react';
import { ProposalTemplate } from '../../services/api';
import { BLOCK_CATALOG } from '../../constants/templates';
import styles from '../../pages/Templates.module.css';

interface TemplateCardProps {
  template: ProposalTemplate;
  onSetDefault: (id: number | null) => void;
  onViewSystem: (template: ProposalTemplate) => void;
  onDuplicateSystem: (template: ProposalTemplate) => void;
  onEdit: (template: ProposalTemplate) => void;
  onDelete: (template: ProposalTemplate) => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onSetDefault,
  onViewSystem,
  onDuplicateSystem,
  onEdit,
  onDelete,
}) => {
  const getBlockLabel = (type: string) => {
    const item = BLOCK_CATALOG.find((c) => c.type === type);
    return item ? item.label : type;
  };

  return (
    <div
      className={`card ${styles.templateCard} ${template.is_default ? styles.defaultTemplate : ''}`}
    >
      <div className={styles.templateHeader}>
        <div>
          <h3 className={styles.templateName}>
            {template.name}
            {template.is_system && (
              <span
                className="badge badge-primary"
                style={{
                  marginLeft: '8px',
                  background: 'var(--color-primary)',
                  color: 'white',
                  fontSize: '0.75rem',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}
              >
                Oficial
              </span>
            )}
            {template.is_default && (
              <span className="badge badge-success">Padrão da Automação</span>
            )}
          </h3>
          <div className={styles.templateMeta}>
            {template.default_budget && <span>Min Budget: R$ {template.default_budget}</span>}
            {template.default_deadline_days && (
              <span>Prazo: {template.default_deadline_days} dias</span>
            )}
            <span>Peças: {template.blueprint?.length || 0}</span>
          </div>
        </div>
        <div className={styles.templateActions}>
          {!template.is_default && !template.is_system && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => onSetDefault(template.id)}
            >
              Definir Padrão
            </button>
          )}
          {template.is_system ? (
            <>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onViewSystem(template)}
              >
                Visualizar
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onDuplicateSystem(template)}
              >
                Duplicar
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onEdit(template)}
              >
                Editar Blueprint
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onDelete(template)}
                style={{ color: 'var(--color-error)' }}
              >
                Excluir
              </button>
            </>
          )}
        </div>
      </div>
      <div className={styles.blueprintFlowPreview}>
        {template.blueprint && template.blueprint.length > 0 ? (
          template.blueprint.map((b, i) => (
            <div key={b.id || i} className={styles.previewFlowBlock}>
              <FileText size={14} />
              <span>{getBlockLabel(b.type)}</span>
              {i < template.blueprint.length - 1 && (
                <ChevronRight size={12} className={styles.arrow} />
              )}
            </div>
          ))
        ) : (
          <span style={{ color: 'var(--color-text-muted)' }}>Blueprint vazio</span>
        )}
      </div>
    </div>
  );
};
