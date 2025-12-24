"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";

interface DashboardStats {
  total_proposals_sent: number;
  proposals_today: number;
  proposals_this_week: number;
  proposals_this_month: number;
  response_rate: number;
  accepted_proposals: number;
  pending_proposals: number;
  last_activity: string | null;
}

interface AutomationStatus {
  is_running: boolean;
  is_logged_in: boolean;
  current_action: string | null;
  proposals_sent_today: number;
  max_proposals_per_day: number;
  last_error: string | null;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
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

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Em desenvolvimento, usar dados mock
      // Em produção, fazer chamada real à API
      setStats({
        total_proposals_sent: 42,
        proposals_today: 3,
        proposals_this_week: 15,
        proposals_this_month: 42,
        response_rate: 23.5,
        accepted_proposals: 10,
        pending_proposals: 32,
        last_activity: new Date().toISOString(),
      });

      setAutomationStatus({
        is_running: false,
        is_logged_in: false,
        current_action: null,
        proposals_sent_today: 3,
        max_proposals_per_day: 10,
        last_error: null,
      });
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    try {
      setAutomationStatus(prev => ({ ...prev, current_action: "Realizando login..." }));
      // await fetch('http://localhost:8000/api/automation/login', { method: 'POST' });
      setTimeout(() => {
        setAutomationStatus(prev => ({ ...prev, is_logged_in: true, current_action: null }));
      }, 2000);
    } catch (error) {
      console.error("Erro no login:", error);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className="spinner spinner-lg"></div>
        <p className="mt-md text-muted">Carregando dashboard...</p>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">
          <span className="text-gradient">Dashboard</span>
        </h1>
        <p className="page-subtitle">
          Bem-vindo ao seu painel de automação do Workana
        </p>
      </div>

      {/* Status da Automação */}
      <div className={`card ${styles.statusCard}`}>
        <div className={styles.statusHeader}>
          <div className={styles.statusInfo}>
            <div className={styles.statusIndicator}>
              <span className={`status-dot ${automationStatus.is_logged_in ? 'online' : 'offline'}`}></span>
              <span>{automationStatus.is_logged_in ? 'Conectado' : 'Desconectado'}</span>
            </div>
            {automationStatus.current_action && (
              <p className={styles.currentAction}>
                <span className="spinner"></span>
                {automationStatus.current_action}
              </p>
            )}
          </div>
          <div className={styles.statusActions}>
            {!automationStatus.is_logged_in ? (
              <button className="btn btn-primary" onClick={handleLogin}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                  <polyline points="10 17 15 12 10 7" />
                  <line x1="15" y1="12" x2="3" y2="12" />
                </svg>
                Fazer Login
              </button>
            ) : (
              <button className="btn btn-secondary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Desconectar
              </button>
            )}
          </div>
        </div>
        <div className={styles.proposalLimit}>
          <span>Propostas hoje: {automationStatus.proposals_sent_today}/{automationStatus.max_proposals_per_day}</span>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${(automationStatus.proposals_sent_today / automationStatus.max_proposals_per_day) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4">
        <div className="stat-card" style={{ '--stat-color': 'var(--gradient-primary)' } as React.CSSProperties}>
          <div className="stat-value text-gradient">{stats.total_proposals_sent}</div>
          <div className="stat-label">Total de Propostas</div>
        </div>

        <div className="stat-card" style={{ '--stat-color': 'var(--gradient-secondary)' } as React.CSSProperties}>
          <div className="stat-value" style={{ color: 'var(--color-secondary)' }}>{stats.proposals_today}</div>
          <div className="stat-label">Propostas Hoje</div>
          <div className="stat-change positive">
            <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9V3m0 0L3 6m3-3l3 3" />
            </svg>
            +2 vs ontem
          </div>
        </div>

        <div className="stat-card" style={{ '--stat-color': 'var(--gradient-success)' } as React.CSSProperties}>
          <div className="stat-value" style={{ color: 'var(--color-success)' }}>{stats.response_rate}%</div>
          <div className="stat-label">Taxa de Resposta</div>
        </div>

        <div className="stat-card" style={{ '--stat-color': 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)' } as React.CSSProperties}>
          <div className="stat-value" style={{ color: '#f472b6' }}>{stats.accepted_proposals}</div>
          <div className="stat-label">Propostas Aceitas</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className={`card ${styles.quickActions}`}>
        <h3 className="card-title">Ações Rápidas</h3>
        <div className={styles.actionsGrid}>
          <a href="/projects" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-primary)' }}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </div>
            <div className={styles.actionText}>
              <h4>Buscar Projetos</h4>
              <p>Encontre novos projetos</p>
            </div>
          </a>

          <a href="/templates" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-secondary)' }}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <div className={styles.actionText}>
              <h4>Templates</h4>
              <p>Gerencie suas propostas</p>
            </div>
          </a>

          <a href="/history" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'var(--gradient-success)' }}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 8v4l3 3" />
                <circle cx="12" cy="12" r="10" />
              </svg>
            </div>
            <div className={styles.actionText}>
              <h4>Histórico</h4>
              <p>Veja propostas enviadas</p>
            </div>
          </a>

          <a href="/settings" className={styles.actionCard}>
            <div className={styles.actionIcon} style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </div>
            <div className={styles.actionText}>
              <h4>Configurações</h4>
              <p>Ajuste suas preferências</p>
            </div>
          </a>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Atividade Recente</h3>
          <a href="/history" className="btn btn-ghost btn-sm">Ver tudo</a>
        </div>
        <div className={styles.activityList}>
          <div className={styles.activityItem}>
            <div className={styles.activityIcon} style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--color-success)' }}>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <div className={styles.activityContent}>
              <p>Proposta enviada para <strong>Desenvolvimento de App Mobile</strong></p>
              <span className="text-sm text-muted">Há 2 horas</span>
            </div>
            <span className="badge badge-success">Enviada</span>
          </div>

          <div className={styles.activityItem}>
            <div className={styles.activityIcon} style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--color-info)' }}>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <div className={styles.activityContent}>
              <p>Cliente visualizou proposta para <strong>Sistema Web PHP</strong></p>
              <span className="text-sm text-muted">Há 5 horas</span>
            </div>
            <span className="badge badge-info">Visualizada</span>
          </div>

          <div className={styles.activityItem}>
            <div className={styles.activityIcon} style={{ background: 'rgba(99, 102, 241, 0.15)', color: 'var(--color-primary)' }}>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </div>
            <div className={styles.activityContent}>
              <p>Busca automática encontrou <strong>12 novos projetos</strong></p>
              <span className="text-sm text-muted">Ontem às 14:30</span>
            </div>
            <span className="badge badge-neutral">Sistema</span>
          </div>
        </div>
      </div>
    </div>
  );
}
