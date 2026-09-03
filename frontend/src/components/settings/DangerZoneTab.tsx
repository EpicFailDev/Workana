import React from 'react';
import styles from '../../pages/Settings.module.css';

interface DangerZoneTabProps {
  onClearHistory: () => void;
  onResetFactory: () => void;
}

export const DangerZoneTab: React.FC<DangerZoneTabProps> = ({ onClearHistory, onResetFactory }) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle} style={{ color: '#ef4444' }}>
        Zona de Perigo
      </h2>
      <p className={styles.sectionSubtitle}>Cuidado: Ações irreversíveis</p>

      <div className={`${styles.card} ${styles.dangerZone}`}>
        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Limpar Histórico de Propostas</h4>
            <p>Apaga permanentemente o registro de propostas enviadas.</p>
          </div>
          <button className={styles.dangerBtn} onClick={onClearHistory}>
            Limpar Tudo
          </button>
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Resetar Aplicação</h4>
            <p>Restaura todas as configurações para o padrão de fábrica.</p>
          </div>
          <button className={styles.dangerBtn} onClick={onResetFactory}>
            Resetar Fábrica
          </button>
        </div>
      </div>
    </div>
  );
};
