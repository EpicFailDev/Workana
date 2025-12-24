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

interface ActivityLog {
  id: number;
  action_type: string;
  description: string;
  status: string;
  created_at: string;
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

  const [recentActivity, setRecentActivity] = useState<ActivityLog[]>([]);

  const [automationStatus, setAutomationStatus] = useState<AutomationStatus>({
    is_running: false,
    is_logged_in: false,
    current_action: null,
    proposals_sent_today: 0,
    max_proposals_per_day: 10,
    last_error: null,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [credentialsConfigured, setCredentialsConfigured] = useState(false);

  const API_BASE = "http://localhost:8000/api";

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Buscar status das credenciais
      const credsResponse = await fetch(`${API_BASE}/credentials/status`);
      if (credsResponse.ok) {
        const credsData = await credsResponse.json();
        setCredentialsConfigured(credsData.configured);
      }

      // Buscar status da automação
      const statusResponse = await fetch(`${API_BASE}/automation/status`);
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setAutomationStatus(statusData);
      }

      // Buscar estatísticas do dashboard
      const statsResponse = await fetch(`${API_BASE}/dashboard/stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Buscar logs de atividade recente
      const logsResponse = await fetch(`${API_BASE}/logs?limit=5`);
      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setRecentActivity(logsData.logs || []);
      }

      setError(null);
    } catch (err) {
      console.error("Erro ao carregar dados:", err);
      setError("Não foi possível conectar ao backend. Verifique se o servidor está rodando.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    // Verificar se credenciais estão configuradas
    if (!credentialsConfigured) {
      setError("Configure suas credenciais em Configurações antes de fazer login.");
      return;
    }

    try {
      setError(null);
      setAutomationStatus(prev => ({ ...prev, current_action: "Verificando credenciais..." }));

      const response = await fetch(`${API_BASE}/automation/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setAutomationStatus(prev => ({
          ...prev,
          is_logged_in: true,
          current_action: null,
          last_error: null
        }));
      } else {
        setAutomationStatus(prev => ({
          ...prev,
          current_action: null,
          last_error: data.detail || data.message || "Falha no login"
        }));
        setError(data.detail || data.message || "Falha no login. Verifique suas credenciais.");
      }
    } catch (err) {
      console.error("Erro no login:", err);
      setAutomationStatus(prev => ({ ...prev, current_action: null }));
      setError("Erro ao conectar com o servidor.");
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/automation/logout`, { method: 'POST' });
      setAutomationStatus(prev => ({ ...prev, is_logged_in: false }));
    } catch (err) {
      console.error("Erro no logout:", err);
    }
  };

  // ===== LOGIN SOCIAL (Google/Facebook/Apple) =====
  const [manualLoginInProgress, setManualLoginInProgress] = useState(false);
  const [hasSession, setHasSession] = useState(false);

  // ===== MODAL DE LOGIN =====
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Verificar sessão ao carregar
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/automation/session-status`);
        if (response.ok) {
          const data = await response.json();
          setHasSession(data.has_session);
        }
      } catch (err) {
        console.error("Erro ao verificar sessão:", err);
      }
    };
    checkSession();
  }, []);

  const handleLoginWithSession = async () => {
    try {
      setError(null);
      setAutomationStatus(prev => ({ ...prev, current_action: "Verificando sessão salva..." }));

      const response = await fetch(`${API_BASE}/automation/login-with-session`, { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        setAutomationStatus(prev => ({ ...prev, is_logged_in: true, current_action: null }));
      } else {
        setAutomationStatus(prev => ({ ...prev, current_action: null }));
        setError(data.message || "Sessão expirada. Faça login novamente.");
      }
    } catch (err) {
      console.error("Erro:", err);
      setAutomationStatus(prev => ({ ...prev, current_action: null }));
      setError("Erro ao conectar com o servidor.");
    }
  };

  const handleStartManualLogin = async () => {
    try {
      setError(null);
      setAutomationStatus(prev => ({ ...prev, current_action: "Abrindo navegador..." }));

      const response = await fetch(`${API_BASE}/automation/start-manual-login`, { method: 'POST' });
      const data = await response.json();

      setAutomationStatus(prev => ({ ...prev, current_action: null }));

      if (data.success) {
        setManualLoginInProgress(true);
      } else {
        setError(data.message || "Erro ao abrir navegador.");
      }
    } catch (err) {
      console.error("Erro:", err);
      setAutomationStatus(prev => ({ ...prev, current_action: null }));
      setError("Erro ao conectar com o servidor.");
    }
  };

  const handleConfirmManualLogin = async () => {
    try {
      setError(null);
      setAutomationStatus(prev => ({ ...prev, current_action: "Verificando login..." }));

      const response = await fetch(`${API_BASE}/automation/confirm-manual-login`, { method: 'POST' });
      const data = await response.json();

      setAutomationStatus(prev => ({ ...prev, current_action: null }));

      if (data.success) {
        setManualLoginInProgress(false);
        setAutomationStatus(prev => ({ ...prev, is_logged_in: true }));
        setHasSession(true);
      } else {
        setError(data.message || "Login não detectado. Complete o login no navegador.");
      }
    } catch (err) {
      console.error("Erro:", err);
      setAutomationStatus(prev => ({ ...prev, current_action: null }));
      setError("Erro ao confirmar login.");
    }
  };

  const handleCancelManualLogin = async () => {
    try {
      await fetch(`${API_BASE}/automation/cancel-manual-login`, { method: 'POST' });
      setManualLoginInProgress(false);
    } catch (err) {
      console.error("Erro:", err);
    }
  };

  // ===== LOGIN DIRETO COM EMAIL/SENHA =====
  const handleDirectLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) {
      setError("Preencha email e senha");
      return;
    }

    setIsLoggingIn(true);
    setError(null);
    setAutomationStatus(prev => ({ ...prev, current_action: "Fazendo login..." }));

    try {
      // Primeiro, salvar as credenciais
      const saveResponse = await fetch(`${API_BASE}/credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });

      if (!saveResponse.ok) {
        throw new Error("Erro ao salvar credenciais");
      }

      // Depois, fazer login
      const loginResponse = await fetch(`${API_BASE}/automation/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await loginResponse.json();

      if (loginResponse.ok && data.success) {
        setAutomationStatus(prev => ({ ...prev, is_logged_in: true, current_action: null, last_error: null }));
        setCredentialsConfigured(true);
        setShowLoginModal(false);
        setLoginEmail("");
        setLoginPassword("");
      } else {
        setAutomationStatus(prev => ({ ...prev, current_action: null }));
        setError(data.detail || data.message || "Falha no login. Verifique suas credenciais.");
      }
    } catch (err) {
      console.error("Erro no login:", err);
      setAutomationStatus(prev => ({ ...prev, current_action: null }));
      setError("Erro ao conectar com o servidor.");
    } finally {
      setIsLoggingIn(false);
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
              <>
                {!manualLoginInProgress ? (
                  <div className={styles.loginOptions}>
                    {/* Botão principal - Entrar */}
                    <button
                      className="btn btn-primary"
                      onClick={() => setShowLoginModal(true)}
                      disabled={!!automationStatus.current_action}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                        <polyline points="10 17 15 12 10 7" />
                        <line x1="15" y1="12" x2="3" y2="12" />
                      </svg>
                      Entrar
                    </button>

                    {/* Usar sessão salva (se existir) */}
                    {hasSession && (
                      <button
                        className="btn btn-ghost"
                        onClick={handleLoginWithSession}
                        disabled={!!automationStatus.current_action}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M12 8v4l3 3" />
                          <circle cx="12" cy="12" r="10" />
                        </svg>
                        Usar Sessão Salva
                      </button>
                    )}
                  </div>
                ) : (
                  <div className={styles.manualLoginButtons}>
                    <button
                      className="btn btn-success"
                      onClick={handleConfirmManualLogin}
                      disabled={!!automationStatus.current_action}
                    >
                      ✓ Confirmar Login
                    </button>
                    <button
                      className="btn btn-ghost"
                      onClick={handleCancelManualLogin}
                    >
                      ✕ Cancelar
                    </button>
                  </div>
                )}
              </>
            ) : (
              <button className="btn btn-secondary" onClick={handleLogout}>
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

        {/* Instruções de Login Manual */}
        {manualLoginInProgress && (
          <div className={styles.infoBanner}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <div>
              <strong>Navegador aberto!</strong> Faça login pelo Google no navegador que foi aberto.
              Após entrar no Workana, clique em "Confirmar Login".
            </div>
          </div>
        )}

        {/* Mensagem de Erro */}
        {error && (
          <div className={styles.errorBanner}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm">✕</button>
          </div>
        )}

        {/* Aviso de sessão disponível */}
        {hasSession && !automationStatus.is_logged_in && !error && !manualLoginInProgress && (
          <div className={styles.successBanner}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span>Você tem uma sessão salva! Clique em "Usar Sessão Salva" para conectar rapidamente.</span>
          </div>
        )}

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
          {recentActivity.length > 0 ? (
            recentActivity.map((log) => (
              <div key={log.id} className={styles.activityItem}>
                <div className={styles.activityIcon} style={{
                  background: log.status === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                  color: log.status === 'success' ? 'var(--color-success)' : 'var(--color-info)'
                }}>
                  <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                </div>
                <div className={styles.activityContent}>
                  <p>{log.description}</p>
                  <span className="text-sm text-muted">
                    {new Date(log.created_at).toLocaleString("pt-BR")}
                  </span>
                </div>
                <span className={`badge ${log.status === 'success' ? 'badge-success' : 'badge-neutral'}`}>
                  {log.action_type}
                </span>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-muted">
              Nenhuma atividade recente registrada.
            </div>
          )}
        </div>
      </div>

      {/* Modal de Login */}
      {showLoginModal && (
        <div className={styles.modalOverlay} onClick={() => setShowLoginModal(false)}>
          <div className={styles.loginModal} onClick={e => e.stopPropagation()}>
            <button className={styles.modalClose} onClick={() => setShowLoginModal(false)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>

            <div className={styles.modalHeader}>
              <div className={styles.modalIcon}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                  <line x1="9" y1="9" x2="9.01" y2="9" />
                  <line x1="15" y1="9" x2="15.01" y2="9" />
                </svg>
              </div>
              <h2>Entrar no Workana</h2>
              <p>Digite suas credenciais do Workana para conectar</p>
            </div>

            <form onSubmit={handleDirectLogin} className={styles.loginForm}>
              <div className={styles.formGroup}>
                <label htmlFor="login-email">Email</label>
                <input
                  id="login-email"
                  type="email"
                  value={loginEmail}
                  onChange={e => setLoginEmail(e.target.value)}
                  placeholder="seu@email.com"
                  required
                  autoFocus
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="login-password">Senha</label>
                <input
                  id="login-password"
                  type="password"
                  value={loginPassword}
                  onChange={e => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary btn-lg" disabled={isLoggingIn} style={{ width: '100%' }}>
                {isLoggingIn ? (
                  <>
                    <span className="spinner"></span>
                    Entrando...
                  </>
                ) : "Entrar"}
              </button>
            </form>

            <div className={styles.divider}>
              <span>ou continue com</span>
            </div>

            <button
              type="button"
              className={styles.googleBtnLarge}
              onClick={() => { setShowLoginModal(false); handleStartManualLogin(); }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Google
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
