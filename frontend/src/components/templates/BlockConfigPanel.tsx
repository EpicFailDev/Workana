import React from 'react';
import { TemplateBlock } from '../../services/api';
import { BLOCK_CATALOG, TEMPLATE_VARIABLES } from '../../constants/templates';
import styles from '../../pages/Templates.module.css';

interface BlockConfigPanelProps {
  block: TemplateBlock | undefined;
  isSystem: boolean;
  onUpdateBlock: (blockId: string, updates: Partial<TemplateBlock>) => void;
}

export const BlockConfigPanel: React.FC<BlockConfigPanelProps> = ({
  block,
  isSystem,
  onUpdateBlock,
}) => {
  if (!block) {
    return (
      <div className={styles.noBlockSelected}>
        <p>Selecione uma peça no Canvas para editar seus parâmetros e instruções.</p>
      </div>
    );
  }

  const catalogItem = BLOCK_CATALOG.find((c) => c.type === block.type);

  return (
    <div className={styles.blockConfigPanel}>
      <div className={styles.blockConfigHeader}>
        <h4>Configuração da Peça: {catalogItem?.label || block.type}</h4>
        <span className={styles.blockConfigTypeBadge}>{block.type}</span>
      </div>

      <div className="form-group mb-md">
        <label className="form-label">Modo de Operação</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <label
            className={`radio-label ${block.mode === 'instruction' ? 'selected' : ''}`}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              background: block.mode === 'instruction' ? 'rgba(99,102,241,0.15)' : 'transparent',
              borderColor:
                block.mode === 'instruction' ? 'var(--color-primary)' : 'var(--color-border)',
            }}
          >
            <input
              type="radio"
              name="blockMode"
              checked={block.mode === 'instruction'}
              onChange={() => !isSystem && onUpdateBlock(block.id, { mode: 'instruction' })}
              disabled={isSystem}
              style={{ marginRight: '6px' }}
            />
            Diretriz IA (Adaptável)
          </label>
          <label
            className={`radio-label ${block.mode === 'literal' ? 'selected' : ''}`}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: '1px solid var(--color-border)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              background: block.mode === 'literal' ? 'rgba(99,102,241,0.15)' : 'transparent',
              borderColor:
                block.mode === 'literal' ? 'var(--color-primary)' : 'var(--color-border)',
            }}
          >
            <input
              type="radio"
              name="blockMode"
              checked={block.mode === 'literal'}
              onChange={() => !isSystem && onUpdateBlock(block.id, { mode: 'literal' })}
              disabled={isSystem}
              style={{ marginRight: '6px' }}
            />
            Texto Literal (Exato)
          </label>
        </div>
      </div>

      <div className="form-group mb-md">
        <label className="form-label">Conteúdo / Instrução</label>
        <textarea
          className="form-input"
          rows={6}
          value={block.content || ''}
          onChange={(e) => onUpdateBlock(block.id, { content: e.target.value })}
          disabled={isSystem}
          placeholder="Instrução ou texto para este bloco..."
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--color-bg-secondary)',
            color: 'var(--color-text)',
            border: '1px solid var(--color-border)',
          }}
        />
      </div>

      <div className={styles.variablesSection}>
        <span className={styles.variablesTitle}>Variáveis Disponíveis para Inserir:</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
          {TEMPLATE_VARIABLES.map((v) => (
            <button
              key={v.tag}
              type="button"
              className="btn btn-ghost btn-xs"
              disabled={isSystem}
              title={v.description}
              onClick={() => {
                if (isSystem) return;
                const current = block.content || '';
                onUpdateBlock(block.id, { content: `${current} ${v.tag}` });
              }}
              style={{
                fontSize: '0.75rem',
                padding: '3px 8px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '4px',
              }}
            >
              {v.tag}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
