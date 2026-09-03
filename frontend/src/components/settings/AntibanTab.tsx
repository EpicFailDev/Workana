import React from 'react';
import { Shield, Sliders, KeyRound, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';
import styles from '../../pages/Settings.module.css';
import type { AntibanConfig, AntibanStatus, SessionHealthResponse } from '../../services/api';

interface AntibanTabProps {
  antibanStatus: AntibanStatus | null;
  antibanConfig: AntibanConfig;
  setAntibanConfig: React.Dispatch<React.SetStateAction<AntibanConfig>>;
  handleSaveAntibanConfig: () => void;
  isSavingAntiban: boolean;
  sessionHealth: SessionHealthResponse | null;
  handleTestSessionHealth: () => void;
  isCheckingHealth: boolean;
}

export const AntibanTab: React.FC<AntibanTabProps> = ({
  antibanStatus,
  antibanConfig,
  setAntibanConfig,
  handleSaveAntibanConfig,
  isSavingAntiban,
  sessionHealth,
  handleTestSessionHealth,
  isCheckingHealth,
}) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Segurança & Proteção Anti-Ban</h2>
      <p className={styles.sectionSubtitle}>
        Parâmetros heurísticos para evitar detecção e bloqueio pela Workana
      </p>

      {/* Status ao Vivo */}
      <div className={styles.card}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px',
          }}
        >
          <h3
            className="text-lg font-bold"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Shield size={20} color="#10b981" />
            Status do Escudo Anti-Ban
          </h3>
          <span className={antibanStatus?.in_cooldown ? styles.badgeError : styles.badgeSuccess}>
            {antibanStatus?.in_cooldown ? 'EM COOLDOWN' : 'PROTEÇÃO ATIVA'}
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
          }}
        >
          <div
            style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '12px',
              borderRadius: '8px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Buscas nesta hora
            </div>
            <div
              style={{
                fontSize: '1.4rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}
            >
              {antibanStatus?.searches_this_hour || 0}{' '}
              <span style={{ fontSize: '0.9rem', opacity: 0.5 }}>
                / {antibanConfig.max_searches_per_hour}
              </span>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '12px',
              borderRadius: '8px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Status de Cooldown
            </div>
            <div
              style={{
                fontSize: '1.1rem',
                fontWeight: 600,
                color: antibanStatus?.in_cooldown ? '#ef4444' : '#10b981',
              }}
            >
              {antibanStatus?.in_cooldown
                ? `Aguarde ${antibanStatus.cooldown_remaining_seconds || 0}s`
                : 'Livre / Operando'}
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0,0,0,0.2)',
              padding: '12px',
              borderRadius: '8px',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Modo de Segurança
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#10b981' }}>
              {antibanConfig.safe_mode ? 'Ativo (Humano)' : 'Agressivo'}
            </div>
          </div>
        </div>
      </div>

      {/* Ajuste de Limites */}
      <div className={styles.card}>
        <h3
          className="text-lg font-bold mb-4"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Sliders size={20} />
          Limites e Delays Heurísticos
        </h3>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Máximo de Buscas por Hora</h4>
            <p>Recomendado: 25-35 buscas para evitar restrições de IP</p>
          </div>
          <input
            type="number"
            min="5"
            max="60"
            className={styles.input}
            style={{ width: '100px' }}
            value={antibanConfig.max_searches_per_hour}
            onChange={(e) =>
              setAntibanConfig({
                ...antibanConfig,
                max_searches_per_hour: Number(e.target.value),
              })
            }
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Intervalo Mínimo entre Ações</h4>
            <p>Delay mínimo em segundos entre raspagens consecutivas</p>
          </div>
          <input
            type="number"
            min="2"
            max="30"
            className={styles.input}
            style={{ width: '100px' }}
            value={antibanConfig.min_delay_between_searches_sec}
            onChange={(e) =>
              setAntibanConfig({
                ...antibanConfig,
                min_delay_between_searches_sec: Number(e.target.value),
              })
            }
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Intervalo Máximo entre Ações</h4>
            <p>Adiciona variação randômica para simular comportamento humano</p>
          </div>
          <input
            type="number"
            min="5"
            max="60"
            className={styles.input}
            style={{ width: '100px' }}
            value={antibanConfig.max_delay_between_searches_sec}
            onChange={(e) =>
              setAntibanConfig({
                ...antibanConfig,
                max_delay_between_searches_sec: Number(e.target.value),
              })
            }
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Período de Cooldown (Minutos)</h4>
            <p>Tempo de pausa total caso o limite por hora seja atingido</p>
          </div>
          <input
            type="number"
            min="5"
            max="60"
            className={styles.input}
            style={{ width: '100px' }}
            value={antibanConfig.cooldown_period_minutes}
            onChange={(e) =>
              setAntibanConfig({
                ...antibanConfig,
                cooldown_period_minutes: Number(e.target.value),
              })
            }
          />
        </div>

        <div className={styles.configItem}>
          <div className={styles.itemInfo}>
            <h4>Rotação de Assinatura (User-Agent)</h4>
            <p>Altera cabeçalhos HTTP e navegadores a cada requisição</p>
          </div>
          <input
            type="checkbox"
            checked={antibanConfig.user_agent_rotation}
            onChange={(e) =>
              setAntibanConfig({
                ...antibanConfig,
                user_agent_rotation: e.target.checked,
              })
            }
            style={{ width: '20px', height: '20px' }}
          />
        </div>

        <button
          className="btn btn-primary mt-4"
          onClick={handleSaveAntibanConfig}
          disabled={isSavingAntiban}
        >
          {isSavingAntiban ? 'Salvando...' : 'Salvar Parâmetros Anti-Ban'}
        </button>
      </div>

      {/* Diagnóstico da Sessão Workana */}
      <div className={styles.card}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px',
          }}
        >
          <h3
            className="text-lg font-bold"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <KeyRound size={20} />
            Diagnóstico da Sessão Workana
          </h3>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleTestSessionHealth}
            disabled={isCheckingHealth}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={isCheckingHealth ? 'animate-spin' : ''} />
            {isCheckingHealth ? 'Verificando...' : 'Testar Conexão'}
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {sessionHealth?.status === 'healthy' ? (
              <CheckCircle2 size={18} color="#10b981" />
            ) : (
              <AlertTriangle size={18} color="#f59e0b" />
            )}
            <span style={{ fontSize: '0.9rem' }}>
              {sessionHealth?.message || 'Status da sessão não verificado'}
            </span>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
            Cookies ativos detectados: <strong>{sessionHealth?.cookies_count || 0}</strong>
            {sessionHealth?.has_cloudflare_clearance && ' • Cloudflare Bypass Ativo'}
            {sessionHealth?.valid && ' • Sessão de Usuário Válida'}
          </div>
        </div>
      </div>
    </div>
  );
};
