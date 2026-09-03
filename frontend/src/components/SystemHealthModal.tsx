import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  KeyRound,
  Radio,
  RefreshCw,
  X,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import {
  api,
  type AutomationStatus,
  type SessionHealthResponse,
  type AntibanStatus,
  type RealtimeStatusResponse,
} from '../services/api';
import styles from './SystemHealthModal.module.css';

interface SystemHealthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SystemHealthModal({ isOpen, onClose }: SystemHealthModalProps) {
  const [loading, setLoading] = useState(false);
  const [autoStatus, setAutoStatus] = useState<AutomationStatus | null>(null);
  const [sessionHealth, setSessionHealth] = useState<SessionHealthResponse | null>(null);
  const [antiban, setAntiban] = useState<AntibanStatus | null>(null);
  const [realtime, setRealtime] = useState<RealtimeStatusResponse | null>(null);

  const loadDiagnostics = async () => {
    setLoading(true);
    try {
      const [autoRes, sessionRes, antibanRes, realtimeRes] = await Promise.allSettled([
        api.getAutomationStatus(),
        api.getSessionHealth(),
        api.getAntibanStatus(),
        api.getRealtimeStatus(),
      ]);

      if (autoRes.status === 'fulfilled') setAutoStatus(autoRes.value);
      if (sessionRes.status === 'fulfilled') setSessionHealth(sessionRes.value);
      if (antibanRes.status === 'fulfilled') setAntiban(antibanRes.value);
      if (realtimeRes.status === 'fulfilled') setRealtime(realtimeRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDiagnostics();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const getSessionPill = () => {
    if (!sessionHealth) return { label: 'Desconhecido', className: styles.pillWarning };
    if (sessionHealth.status === 'healthy') {
      return { label: 'Ativa & Saudável', className: styles.pillHealthy };
    }
    if (sessionHealth.status === 'warning') {
      return { label: 'Atenção (Cookies)', className: styles.pillWarning };
    }
    if (sessionHealth.status === 'expired') {
      return { label: 'Expirada', className: styles.pillError };
    }
    return { label: 'Desconectada', className: styles.pillError };
  };

  const sessionPill = getSessionPill();

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <div className={styles.iconBadge}>
              <Activity size={20} />
            </div>
            <div>
              <h3 className={styles.title}>Diagnóstico e Saúde do Sistema</h3>
              <p className={styles.subtitle}>Telemetria em tempo real dos serviços e proteções</p>
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            <X size={20} />
          </button>
        </div>

        <div className={styles.body}>
          <div className={styles.healthGrid}>
            {/* Sessão do Workana */}
            <div className={styles.statusCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Sessão Workana</span>
                <span className={`${styles.pill} ${sessionPill.className}`}>
                  <span className={styles.pillDot} />
                  {sessionPill.label}
                </span>
              </div>
              <div className={styles.cardValue}>
                {sessionHealth?.cookies_count || 0} cookies ativos
              </div>
              <div className={styles.cardDesc}>
                {sessionHealth?.message || 'Verificando integridade da sessão...'}
              </div>
            </div>

            {/* Escudo Anti-Ban */}
            <div className={styles.statusCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Escudo Anti-Ban</span>
                <span
                  className={`${styles.pill} ${
                    antiban?.in_cooldown ? styles.pillWarning : styles.pillHealthy
                  }`}
                >
                  <span className={styles.pillDot} />
                  {antiban?.in_cooldown ? 'Em Cooldown' : 'Proteção Ativa'}
                </span>
              </div>
              <div className={styles.cardValue}>
                {antiban ? `${antiban.searches_this_hour} / ${antiban.max_per_hour}` : '--'}
                <span style={{ fontSize: '0.75rem', fontWeight: 400, opacity: 0.6, marginLeft: 4 }}>
                  buscas/hora
                </span>
              </div>
              <div className={styles.meterBar}>
                <div
                  className={styles.meterFill}
                  style={{
                    width: antiban
                      ? `${Math.min(100, (antiban.searches_this_hour / antiban.max_per_hour) * 100)}%`
                      : '0%',
                    background:
                      antiban && antiban.searches_this_hour >= antiban.max_per_hour * 0.8
                        ? 'var(--color-warning)'
                        : 'var(--color-primary)',
                  }}
                />
              </div>
            </div>

            {/* Gateway Realtime */}
            <div className={styles.statusCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>WebSocket Realtime</span>
                <span
                  className={`${styles.pill} ${
                    realtime?.is_active ? styles.pillHealthy : styles.pillWarning
                  }`}
                >
                  <span className={styles.pillDot} />
                  {realtime?.is_active ? 'Conectado' : 'Aguardando'}
                </span>
              </div>
              <div className={styles.cardValue}>Pusher Gateway</div>
              <div className={styles.cardDesc}>
                Canais: {realtime?.channels ? realtime.channels.join(', ') : 'pt, en'}
              </div>
            </div>

            {/* Motor de Automação */}
            <div className={styles.statusCard}>
              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Motor de Automação</span>
                <span
                  className={`${styles.pill} ${
                    autoStatus?.is_running ? styles.pillHealthy : styles.pillWarning
                  }`}
                >
                  <span className={styles.pillDot} />
                  {autoStatus?.is_running ? 'Executando' : 'Em Espera'}
                </span>
              </div>
              <div className={styles.cardValue}>
                {autoStatus?.proposals_sent_today || 0} / {autoStatus?.max_proposals_per_day || 10}
                <span style={{ fontSize: '0.75rem', fontWeight: 400, opacity: 0.6, marginLeft: 4 }}>
                  propostas hoje
                </span>
              </div>
              <div className={styles.cardDesc}>
                {autoStatus?.current_action || 'Pronto para novas operações'}
              </div>
            </div>
          </div>

          {/* Detalhes de Segurança */}
          <div className={styles.sectionBox}>
            <div className={styles.rowItem}>
              <span>Cloudflare Bypass Clearance:</span>
              <strong>
                {sessionHealth?.has_cloudflare_clearance ? (
                  <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle2 size={14} /> Válido
                  </span>
                ) : (
                  <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <AlertTriangle size={14} /> Não detectado
                  </span>
                )}
              </strong>
            </div>
            <div className={styles.rowItem}>
              <span>Email da Conta Workana:</span>
              <strong>{sessionHealth?.account_email || 'Não informado'}</strong>
            </div>
            {antiban?.in_cooldown && (
              <div className={styles.rowItem}>
                <span>Tempo restante de pausa:</span>
                <strong style={{ color: '#f59e0b' }}>
                  {antiban.cooldown_remaining_seconds} segundos
                </strong>
              </div>
            )}
          </div>
        </div>

        <div className={styles.footer}>
          <button className={styles.refreshBtn} onClick={loadDiagnostics} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Diagnosticando...' : 'Revalidar Todos os Serviços'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
