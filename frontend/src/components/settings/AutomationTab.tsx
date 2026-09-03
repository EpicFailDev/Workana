import React from 'react';
import styles from '../../pages/Settings.module.css';
import type { AutomationConfig } from '../../services/api';

interface AutomationTabProps {
  config: AutomationConfig;
  setConfig: React.Dispatch<React.SetStateAction<AutomationConfig>>;
  showApiKey: boolean;
  setShowApiKey: React.Dispatch<React.SetStateAction<boolean>>;
  handleSaveConfig: () => void;
  isSaving: boolean;
}

export const AutomationTab: React.FC<AutomationTabProps> = ({
  config,
  setConfig,
  showApiKey,
  setShowApiKey,
  handleSaveConfig,
  isSaving,
}) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Inteligência Artificial & Bots</h2>
      <p className={styles.sectionSubtitle}>Configure como o sistema trabalha por você</p>

      {/* Gemini Config */}
      <div className={styles.card}>
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <span className="text-primary">✨</span> Google Gemini AI
        </h3>
        <div className={styles.formGroup}>
          <label className={styles.label}>API Key</label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              className={styles.input}
              placeholder="Ex: AIzaSy..."
              value={config.gemini_api_key}
              onChange={(e) => setConfig({ ...config, gemini_api_key: e.target.value })}
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              style={{
                position: 'absolute',
                right: '12px',
                top: '12px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-text-muted)',
              }}
            >
              {showApiKey ? 'Ocultar' : 'Mostrar'}
            </button>
          </div>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.label}>Nome na Assinatura</label>
          <input
            type="text"
            className={styles.input}
            placeholder="Ex: João Silva - Desenvolvedor Full Stack"
            value={config.user_full_name}
            onChange={(e) => setConfig({ ...config, user_full_name: e.target.value })}
          />
          <p className="text-xs text-muted mt-2">
            Este nome será usado para assinar as propostas geradas.
          </p>
        </div>
      </div>

      {/* Bot Behavior */}
      <div className={styles.card}>
        <h3 className="text-lg font-bold mb-4">Comportamento do Robô</h3>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Modo Fantasma (Headless)</h4>
            <p>O navegador roda invisível em segundo plano</p>
          </div>
          <input
            type="checkbox"
            checked={config.headless}
            onChange={(e) => setConfig({ ...config, headless: e.target.checked })}
            style={{ width: '20px', height: '20px' }}
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Velocidade Humana</h4>
            <p>Delay de {config.delay_between_actions_ms}ms entre ações</p>
          </div>
          <input
            type="range"
            min="500"
            max="5000"
            step="100"
            value={config.delay_between_actions_ms}
            onChange={(e) =>
              setConfig({ ...config, delay_between_actions_ms: Number(e.target.value) })
            }
            style={{ width: '120px' }}
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Limite Diário</h4>
            <p>Máximo de {config.max_proposals_per_day} propostas por dia</p>
          </div>
          <input
            type="range"
            min="1"
            max="50"
            value={config.max_proposals_per_day}
            onChange={(e) =>
              setConfig({ ...config, max_proposals_per_day: Number(e.target.value) })
            }
            style={{ width: '120px' }}
          />
        </div>
      </div>

      <button className="btn btn-primary" onClick={handleSaveConfig} disabled={isSaving}>
        {isSaving ? 'Salvando...' : 'Salvar Todas Configurações'}
      </button>
    </div>
  );
};
