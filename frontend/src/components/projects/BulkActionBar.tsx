import React from 'react';
import styles from '../../pages/Projects.module.css';
import { MaterialIcon } from '../ui/MaterialIcon';

interface BulkActionBarProps {
  selectedCount: number;
  selectAllFiltered: boolean;
  total: number;
  isSubmitting: boolean;
  onSelectAllFiltered: () => void;
  onClearSelection: () => void;
  onBulkFavorite: () => void;
  onBulkHide: () => void;
  onBulkAnalyze: () => void;
  onOpenBatchModal: () => void;
}

export const BulkActionBar: React.FC<BulkActionBarProps> = ({
  selectedCount,
  selectAllFiltered,
  total,
  isSubmitting,
  onSelectAllFiltered,
  onClearSelection,
  onBulkFavorite,
  onBulkHide,
  onBulkAnalyze,
  onOpenBatchModal,
}) => {
  if (selectedCount === 0) return null;

  const displayCount = selectAllFiltered ? total : selectedCount;

  return (
    <div className={styles.bulkActionBar}>
      <div className={styles.bulkActionInfo}>
        <span className={styles.bulkCountBadge}>{displayCount}</span>
        <span>projetos selecionados</span>
        {!selectAllFiltered && total > selectedCount && (
          <button type="button" className={styles.bulkLinkBtn} onClick={onSelectAllFiltered}>
            Selecionar todos os {total} do filtro
          </button>
        )}
      </div>

      <div className={styles.bulkActionButtons}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={isSubmitting}
          onClick={onBulkFavorite}
          title="Favoritar projetos selecionados"
        >
          <MaterialIcon
            name="star"
            fill
            size={15}
            style={{ color: '#fbbf24', marginRight: '4px' }}
          />
          Favoritar
        </button>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={isSubmitting}
          onClick={onBulkHide}
          title="Ocultar projetos selecionados"
        >
          <MaterialIcon name="visibility_off" size={15} style={{ marginRight: '4px' }} />
          Ocultar
        </button>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={isSubmitting}
          onClick={onBulkAnalyze}
          title="Executar análise IA de compatibilidade em lote"
        >
          <MaterialIcon name="auto_awesome" size={15} style={{ marginRight: '4px' }} />
          Analisar com IA
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={isSubmitting}
          onClick={onOpenBatchModal}
          title="Criar lote de envio de propostas para os selecionados"
        >
          <MaterialIcon name="rocket_launch" size={15} style={{ marginRight: '4px' }} />
          Criar Lote de Propostas
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onClearSelection}
          title="Limpar seleção"
        >
          Limpar
        </button>
      </div>
    </div>
  );
};
