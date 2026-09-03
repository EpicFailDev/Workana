import React from 'react';
import styles from '../../pages/Settings.module.css';

interface GeneralTabProps {
  currentTheme: string;
  changeTheme: (theme: string) => void;
}

export const GeneralTab: React.FC<GeneralTabProps> = ({ currentTheme, changeTheme }) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Aparência</h2>
      <p className={styles.sectionSubtitle}>Personalize o visual do seu painel</p>

      <div className={styles.card}>
        <div className={styles.themeGrid}>
          {['default', 'cyberpunk', 'minimal'].map((theme) => (
            <div
              key={theme}
              className={`${styles.themeBtn} ${currentTheme === theme ? styles.active : ''}`}
              onClick={() => changeTheme(theme)}
            >
              <div style={{ fontSize: '24px' }}>
                {theme === 'default' ? '🌙' : theme === 'cyberpunk' ? '👾' : '☀️'}
              </div>
              <span>{theme.charAt(0).toUpperCase() + theme.slice(1)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
