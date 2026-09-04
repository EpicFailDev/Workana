import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import styles from './Dashboard.module.css';
import {
  api,
  type DashboardStats,
  type AutomationStatus,
  type DailyStatistic,
  type AntibanStatus,
  type SessionHealthResponse,
  API_BASE_URL,
} from '../services/api';
import Loader from '../components/Loader';
import ActivityChart from '../components/ActivityChart';
import CyberHeader from '../components/CyberHeader';
import SystemLog from '../components/SystemLog';
import { useCounter } from '../hooks/useCounter';
import { useAuth } from '../context/AuthContext';
import { MaterialIcon } from '../components/ui/MaterialIcon';
import {
  Shield,
  KeyRound,
  Layers,
  Sparkles,
  FolderSearch,
  History,
  Settings,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const displayName =
    user?.user_metadata?.full_name || (user?.email ? user.email.split('@')[0] : 'Operador');

  // Stats / Metrics State
  const [metrics, setMetrics] = useState<DashboardStats>({
    total_proposals_sent: 0,
    proposals_today: 0,
    proposals_this_week: 0,
    proposals_this_month: 0,
    response_rate: 0,
    accepted_proposals: 0,
    pending_proposals: 0,
    last_activity: null,
  });

  const [automationStatus, setAutomationStatus] = useState<AutomationStatus>({
    is_running: false,
    is_logged_in: false,
    current_action: null,
    proposals_sent_today: 0,
    max_proposals_per_day: 10,
    last_error: null,
  });

  const [antibanStatus, setAntibanStatus] = useState<AntibanStatus | null>(null);
  const [sessionHealth, setSessionHealth] = useState<SessionHealthResponse | null>(null);
  const [statsHistory, setStatsHistory] = useState<DailyStatistic[]>([]);
  const [chartMetric, setChartMetric] = useState<'proposals' | 'projects'>('proposals');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Animated Counters
  const animatedTotalProposals = useCounter(metrics.total_proposals_sent);
  const animatedActiveProjects = useCounter(metrics.accepted_proposals);
  const animatedResponseRate = useCounter(metrics.response_rate);
  const animatedEarnings = useCounter(0);

  const fetchDashboardData = async () => {
    try {
      const [statusRes, statsRes, histRes, antibanRes, healthRes] = await Promise.allSettled([
        api.getAutomationStatus(),
        api.getDashboardStats(),
        api.getStatistics(7),
        api.getAntibanStatus(),
        api.getSessionHealth(),
      ]);

      if (statusRes.status === 'fulfilled') setAutomationStatus(statusRes.value);
      if (statsRes.status === 'fulfilled') setMetrics(statsRes.value);
      if (histRes.status === 'fulfilled' && histRes.value?.statistics) {
        setStatsHistory(histRes.value.statistics);
      }
      if (antibanRes.status === 'fulfilled') setAntibanStatus(antibanRes.value);
      if (healthRes.status === 'fulfilled') setSessionHealth(healthRes.value);

      setError(null);
    } catch {
      if (isLoading) {
        setError(`Não foi possível conectar ao backend (${API_BASE_URL}).`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Gráfico com dados reais dos últimos 7 dias
  const { chartData, chartLabels } = useMemo(() => {
    if (statsHistory && statsHistory.length > 0) {
      const sorted = [...statsHistory].sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      const labels = sorted.map((s) => {
        const d = new Date(s.date + 'T00:00:00');
        return d.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
      });
      const data = sorted.map((s) =>
        chartMetric === 'proposals' ? s.proposals_sent || 0 : s.projects_found || 0
      );
      return { chartData: data, chartLabels: labels };
    }

    // Fallback gracioso
    return {
      chartData: [
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.1)),
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.15)),
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.2)),
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.15)),
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.25)),
        Math.max(0, Math.round((metrics.proposals_this_week - metrics.proposals_today) * 0.15)),
        metrics.proposals_today || 0,
      ],
      chartLabels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Hoje'],
    };
  }, [statsHistory, chartMetric, metrics]);

  if (isLoading) {
    return <Loader type="overlay" message="Sincronizando seu dashboard..." />;
  }

  return (
    <div className={styles.container}>
      <CyberHeader
        title="PAINEL DE CONTROLE"
        subtitle="VISÃO GERAL // MÉTRICAS EM TEMPO REAL"
        description={`Olá, ${displayName}. Acompanhe seu desempenho e a segurança operacional no Workana.`}
      />

      {/* Metrics Grid */}
      <div className={styles.grid}>
        <div className={`${styles.card} holo-card`}>
          <div className={styles.cardIcon}>
            <MaterialIcon name="analytics" size={28} />
          </div>
          <div className="stat-value-big">{animatedTotalProposals}</div>
          <div className={styles.cardLabel}>Propostas Enviadas</div>
        </div>

        <div className={`${styles.card} holo-card`}>
          <div className={styles.cardIcon}>
            <MaterialIcon name="task_alt" size={28} />
          </div>
          <div className="stat-value-big">{animatedActiveProjects}</div>
          <div className={styles.cardLabel}>Propostas Aceitas</div>
        </div>

        <div className={`${styles.card} holo-card`}>
          <div className={styles.cardIcon}>
            <MaterialIcon name="target" size={28} />
          </div>
          <div className="stat-value-big">{animatedResponseRate}%</div>
          <div className={styles.cardLabel}>Taxa de Resposta</div>
        </div>

        <div className={`${styles.card} holo-card`}>
          <div className={styles.cardIcon}>
            <MaterialIcon name="payments" size={28} />
          </div>
          <div className="stat-value-big">R$ {animatedEarnings}</div>
          <div className={styles.cardLabel}>Ganhos Estimados</div>
        </div>
      </div>

      {/* Chart Section & Real Logs */}
      <div
        className={styles.chartSection}
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
          gap: 'var(--spacing-lg)',
          marginTop: 'var(--spacing-lg)',
        }}
      >
        <div className="holo-card" style={{ padding: 'var(--spacing-lg)', height: '340px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '12px',
            }}
          >
            <h2 className={styles.chartTitle} style={{ margin: 0 }}>
              Atividade dos Últimos 7 Dias
            </h2>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                className="btn btn-xs"
                style={{
                  background:
                    chartMetric === 'proposals'
                      ? 'var(--color-primary)'
                      : 'rgba(255, 255, 255, 0.05)',
                  color: chartMetric === 'proposals' ? '#fff' : 'var(--color-text-secondary)',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.72rem',
                }}
                onClick={() => setChartMetric('proposals')}
              >
                Propostas
              </button>
              <button
                type="button"
                className="btn btn-xs"
                style={{
                  background:
                    chartMetric === 'projects'
                      ? 'var(--color-secondary)'
                      : 'rgba(255, 255, 255, 0.05)',
                  color: chartMetric === 'projects' ? '#fff' : 'var(--color-text-secondary)',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.72rem',
                }}
                onClick={() => setChartMetric('projects')}
              >
                Oportunidades
              </button>
            </div>
          </div>
          <ActivityChart
            data={chartData}
            labels={chartLabels}
            color={chartMetric === 'proposals' ? 'var(--color-primary)' : 'var(--color-secondary)'}
            height={200}
          />
        </div>

        <div className="holo-card" style={{ padding: 'var(--spacing-lg)', height: '340px' }}>
          <SystemLog />
        </div>
      </div>

      {/* --- TELEMETRIA OPERACIONAL & SEGURANÇA --- */}
      <div
        className={styles.grid}
        style={{
          marginBottom: 'var(--spacing-xl)',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          marginTop: 'var(--spacing-lg)',
        }}
      >
        {/* Status da Automação */}
        <div className={`${styles.consoleCard} holo-card`}>
          <div className={styles.consoleContent}>
            <div className={styles.consoleSection}>
              <div
                className={`${styles.statusDot} ${
                  automationStatus.is_running ? styles.online : styles.offline
                }`}
              ></div>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Estado Operacional</span>
                <span className={styles.consoleValue}>
                  {automationStatus.is_running ? 'SISTEMAS ONLINE' : 'EM ESPERA'}
                </span>
              </div>
            </div>

            <div className={styles.consoleSection}>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Capacidade Diária</span>
                <span className={styles.consoleValue}>
                  {automationStatus.proposals_sent_today}{' '}
                  <span style={{ opacity: 0.4 }}>/ {automationStatus.max_proposals_per_day}</span>
                </span>
              </div>
            </div>

            <div className={styles.consoleAction}>
              <Link
                to="/projects"
                className="btn btn-primary btn-sm"
                style={{ padding: '8px 18px', fontWeight: 600 }}
              >
                Buscar Projetos
              </Link>
            </div>
          </div>

          <div className={styles.consoleProgress}>
            <div
              className={styles.consoleProgressFill}
              style={{
                width: `${Math.min(
                  100,
                  (automationStatus.proposals_sent_today /
                    (automationStatus.max_proposals_per_day || 1)) *
                    100
                )}%`,
              }}
            />
          </div>
        </div>

        {/* Escudo Anti-Ban */}
        <div className={`${styles.consoleCard} holo-card`}>
          <div className={styles.consoleContent}>
            <div className={styles.consoleSection}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(16, 185, 129, 0.12)',
                  color: '#10b981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Shield size={18} />
              </div>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Proteção Anti-Ban</span>
                <span className={styles.consoleValue} style={{ fontSize: '0.95rem' }}>
                  {antibanStatus?.in_cooldown ? 'EM COOLDOWN' : 'ESCUDO ATIVO'}
                </span>
              </div>
            </div>

            <div className={styles.consoleSection}>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Buscas nesta hora</span>
                <span className={styles.consoleValue}>
                  {antibanStatus?.searches_this_hour || 0}{' '}
                  <span style={{ opacity: 0.4 }}>/ {antibanStatus?.max_per_hour || 30}</span>
                </span>
              </div>
            </div>

            <div className={styles.consoleAction}>
              <Link
                to="/settings"
                className="btn btn-secondary btn-sm"
                style={{ padding: '8px 14px' }}
              >
                Ajustar Limites
              </Link>
            </div>
          </div>

          <div className={styles.consoleProgress}>
            <div
              className={styles.consoleProgressFill}
              style={{
                background:
                  antibanStatus &&
                  antibanStatus.searches_this_hour >=
                    (antibanStatus.max_per_hour || antibanStatus.max_searches_hour || 30) * 0.8
                    ? 'var(--color-warning)'
                    : '#10b981',
                width: `${Math.min(
                  100,
                  ((antibanStatus?.searches_this_hour || 0) /
                    (antibanStatus?.max_per_hour || antibanStatus?.max_searches_hour || 30)) *
                    100
                )}%`,
              }}
            />
          </div>
        </div>

        {/* Saúde da Sessão */}
        <div className={`${styles.consoleCard} holo-card`}>
          <div className={styles.consoleContent}>
            <div className={styles.consoleSection}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background:
                    sessionHealth?.status === 'healthy'
                      ? 'rgba(16, 185, 129, 0.12)'
                      : 'rgba(245, 158, 11, 0.12)',
                  color: sessionHealth?.status === 'healthy' ? '#10b981' : '#f59e0b',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <KeyRound size={18} />
              </div>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Sessão Workana</span>
                <span className={styles.consoleValue} style={{ fontSize: '0.95rem' }}>
                  {sessionHealth?.status === 'healthy'
                    ? 'CONECTADA'
                    : sessionHealth?.status === 'warning'
                      ? 'REQUER ATENÇÃO'
                      : 'DESCONECTADA'}
                </span>
              </div>
            </div>

            <div className={styles.consoleSection}>
              <div className={styles.consoleInfo}>
                <span className={styles.consoleLabel}>Cookies Armazenados</span>
                <span className={styles.consoleValue}>
                  {sessionHealth?.cookies_count || 0} ativos
                </span>
              </div>
            </div>

            <div className={styles.consoleAction}>
              <Link
                to="/settings"
                className="btn btn-secondary btn-sm"
                style={{ padding: '8px 14px' }}
              >
                Gerenciar
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className={styles.errorBanner}>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="btn btn-ghost btn-sm"
              aria-label="Fechar erro"
            >
              <MaterialIcon name="close" size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className={`holo-card ${styles.quickActions}`} style={{ padding: 'var(--spacing-lg)' }}>
        <h3 className="card-title">Ações e Atalhos Rápidos</h3>
        <div className={styles.actionsGrid}>
          <Link to="/projects" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-primary)' }}>
              <FolderSearch size={22} color="#fff" />
            </div>
            <div className={styles.actionText}>
              <h4>Catálogo de Projetos</h4>
              <p>Oportunidades em tempo real</p>
            </div>
          </Link>

          <Link to="/batches" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-secondary)' }}>
              <Layers size={22} color="#fff" />
            </div>
            <div className={styles.actionText}>
              <h4>Lotes de Propostas</h4>
              <p>Envios em massa e rascunhos</p>
            </div>
          </Link>

          <Link to="/templates" className={styles.actionCard}>
            <div
              className={styles.actionIcon}
              style={{ background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)' }}
            >
              <Sparkles size={22} color="#fff" />
            </div>
            <div className={styles.actionText}>
              <h4>Modelos Consultivos</h4>
              <p>Blueprints com inteligência Gemini</p>
            </div>
          </Link>

          <Link to="/history" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-success)' }}>
              <History size={22} color="#fff" />
            </div>
            <div className={styles.actionText}>
              <h4>Histórico & Kanban</h4>
              <p>Acompanhe propostas enviadas</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
