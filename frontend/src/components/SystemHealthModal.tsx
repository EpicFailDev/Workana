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
  Globe,
  Clipboard,
  Upload,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import {
  api,
  type AutomationStatus,
  type SessionHealthResponse,
  type AntibanStatus,
  type RealtimeStatusResponse,
} from '../services/api';
import { useToast } from '../context/ToastContext';
import styles from './SystemHealthModal.module.css';

interface SystemHealthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SystemHealthModal({ isOpen, onClose }: SystemHealthModalProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [autoStatus, setAutoStatus] = useState<AutomationStatus | null>(null);
  const [sessionHealth, setSessionHealth] = useState<SessionHealthResponse | null>(null);
  const [antiban, setAntiban] = useState<AntibanStatus | null>(null);
  const [realtime, setRealtime] = useState<RealtimeStatusResponse | null>(null);

  // Estados do Atualizador Rápido de Sessão
  const [showSessionUpdater, setShowSessionUpdater] = useState(false);
  const [activeMode, setActiveMode] = useState<'paste' | 'auto' | 'file'>('paste');
  const [sessionInput, setSessionInput] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isSavingSession, setIsSavingSession] = useState(false);

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
    if (sessionHealth.status === 'warning' || sessionHealth.status === 'saved_offline') {
      return { label: 'Atenção (Cookies)', className: styles.pillWarning };
    }
    if (sessionHealth.status === 'blocked_waf') {
      return { label: 'Desafio Cloudflare', className: styles.pillWarning };
    }
    if (sessionHealth.status === 'expired') {
      return { label: 'Expirada', className: styles.pillError };
    }
    return { label: 'Desconectada', className: styles.pillError };
  };

  const handleStartRealtime = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.startRealtime();
      await loadDiagnostics();
    } catch (err) {
      console.error('Falha ao iniciar realtime:', err);
    }
  };

  const handleOpenBrowserLogin = async () => {
    setIsLoggingIn(true);
    toast.info('Abrindo navegador no Windows para login/resolução de desafio...', 'Iniciando');
    try {
      const res = await api.googleLogin();
      if (res.success) {
        toast.success('Sessão capturada e renovada com sucesso!', 'Conectado');
        setShowSessionUpdater(false);
        await loadDiagnostics();
      } else {
        toast.error(res.message || 'O login não foi concluído no navegador.', 'Atenção');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Falha ao iniciar login pelo navegador.', 'Erro');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handlePasteFromClipboard = async () => {
    try {
      if (navigator?.clipboard?.readText) {
        const text = await navigator.clipboard.readText();
        if (text && text.trim()) {
          setSessionInput(text.trim());
          toast.success('Conteúdo colado da área de transferência!', 'Clipboard');
          return;
        }
      }
      toast.info(
        'Área de transferência vazia ou sem permissão. Cole com Ctrl + V no campo.',
        'Info'
      );
    } catch (err) {
      toast.info('Não foi possível ler automaticamente. Use Ctrl + V no campo.', 'Aviso');
    }
  };

  const handleSaveSessionText = async () => {
    if (!sessionInput.trim()) {
      toast.warning('Insira os cookies ou JSON da sessão antes de salvar.', 'Campo Vazio');
      return;
    }
    setIsSavingSession(true);
    try {
      const res = await api.importSession(
        sessionInput.trim(),
        sessionHealth?.account_email || undefined
      );
      if (res.success) {
        toast.success(res.message || 'Cookies salvos e sessão sincronizada!', 'Sucesso');
        setSessionInput('');
        setShowSessionUpdater(false);
        await loadDiagnostics();
      } else {
        toast.error(res.message || 'Formato inválido de sessão.', 'Erro');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Falha ao salvar sessão.', 'Erro');
    } finally {
      setIsSavingSession(false);
    }
  };

  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      if (!content) return;
      setIsSavingSession(true);
      try {
        const res = await api.importSession(content, sessionHealth?.account_email || undefined);
        if (res.success) {
          toast.success('Arquivo de sessão importado com sucesso!', 'Sucesso');
          setShowSessionUpdater(false);
          await loadDiagnostics();
        } else {
          toast.error(res.message || 'Arquivo inválido.', 'Erro');
        }
      } catch (err: any) {
        toast.error(err?.message || 'Falha ao ler arquivo de sessão.', 'Erro');
      } finally {
        setIsSavingSession(false);
      }
    };
    reader.readAsText(file);
  };

  const sessionPill = getSessionPill();
  const maxPerHour = antiban?.max_per_hour || antiban?.max_searches_hour || 10;
  const searchesThisHour = antiban?.searches_this_hour || 0;

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
              <div className={styles.sessionActionRow}>
                <button
                  type="button"
                  className={styles.quickActionBtn}
                  onClick={() => setShowSessionUpdater(!showSessionUpdater)}
                  title="Atualizar ou renovar os cookies desta sessão"
                >
                  <KeyRound size={13} />
                  <span>
                    {showSessionUpdater ? 'Ocultar Atualização' : 'Renovar / Injetar Cookies'}
                  </span>
                  {showSessionUpdater ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>
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
                {antiban ? `${searchesThisHour} / ${maxPerHour}` : '--'}
                <span style={{ fontSize: '0.75rem', fontWeight: 400, opacity: 0.6, marginLeft: 6 }}>
                  buscas/hora
                </span>
              </div>
              <div className={styles.meterBar}>
                <div
                  className={styles.meterFill}
                  style={{
                    width: antiban
                      ? `${Math.min(100, (searchesThisHour / maxPerHour) * 100)}%`
                      : '0%',
                    background:
                      antiban && searchesThisHour >= maxPerHour * 0.8
                        ? 'var(--color-warning)'
                        : 'var(--color-primary)',
                  }}
                />
              </div>
            </div>

            {/* Painel Expansível de Atualização de Cookies */}
            {showSessionUpdater && (
              <div className={styles.updaterBox}>
                <div className={styles.updaterHeader}>
                  <span className={styles.updaterTitle}>
                    <Sparkles size={15} color="var(--color-primary, #6366f1)" />
                    Atualização Rápida de Cookies & Sessão
                  </span>
                </div>

                <div className={styles.updaterModes}>
                  <button
                    type="button"
                    className={`${styles.modeTab} ${activeMode === 'paste' ? styles.modeTabActive : ''}`}
                    onClick={() => setActiveMode('paste')}
                  >
                    <Clipboard size={14} />
                    <span>Colar Cookies</span>
                  </button>
                  <button
                    type="button"
                    className={`${styles.modeTab} ${activeMode === 'auto' ? styles.modeTabActive : ''}`}
                    onClick={() => setActiveMode('auto')}
                  >
                    <Globe size={14} />
                    <span>Abrir Navegador</span>
                  </button>
                  <button
                    type="button"
                    className={`${styles.modeTab} ${activeMode === 'file' ? styles.modeTabActive : ''}`}
                    onClick={() => setActiveMode('file')}
                  >
                    <Upload size={14} />
                    <span>Importar Arquivo</span>
                  </button>
                </div>

                {/* Modo 1: Colar Cookies / Clipboard */}
                {activeMode === 'paste' && (
                  <div className={styles.modeContent}>
                    <div className={styles.pasteActionBar}>
                      <p className={styles.modeHelp}>
                        Aceita <strong>JSON</strong> (extensão Cookie-Editor), <strong>HAR</strong>{' '}
                        ou <strong>string bruta</strong> (ex:{' '}
                        <code>cf_clearance=...; workana_session=...</code>).
                      </p>
                      <button
                        type="button"
                        className={styles.clipboardQuickBtn}
                        onClick={handlePasteFromClipboard}
                        title="Colar direto da área de transferência"
                      >
                        <Clipboard size={12} />
                        Colar do Clipboard
                      </button>
                    </div>
                    <textarea
                      className={styles.sessionTextarea}
                      rows={3}
                      placeholder="Cole aqui os cookies ou JSON exportado (Ctrl + V)..."
                      value={sessionInput}
                      onChange={(e) => setSessionInput(e.target.value)}
                    />
                    <button
                      type="button"
                      className={styles.primaryActionBtn}
                      onClick={handleSaveSessionText}
                      disabled={isSavingSession || !sessionInput.trim()}
                    >
                      {isSavingSession ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          Validando e salvando cookies...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 size={14} />
                          Salvar e Sincronizar Cookies
                        </>
                      )}
                    </button>
                    <div className={styles.quickTip}>
                      💡 <strong>Dica rápida:</strong> Abra o Workana no seu navegador, clique no
                      ícone da extensão <em>Cookie-Editor</em>, clique em{' '}
                      <strong>Export &gt; Export as JSON</strong> e depois clique em{' '}
                      <strong>Colar do Clipboard</strong> acima.
                    </div>
                  </div>
                )}

                {/* Modo 2: Abrir Navegador Automático */}
                {activeMode === 'auto' && (
                  <div className={styles.modeContent}>
                    <p className={styles.modeHelp}>
                      Abre uma janela real do Chrome ou Edge na sua máquina para você fazer login no
                      Workana ou resolver o desafio Cloudflare. Ao finalizar, a sessão é capturada
                      automaticamente.
                    </p>
                    <button
                      type="button"
                      className={styles.primaryActionBtn}
                      onClick={handleOpenBrowserLogin}
                      disabled={isLoggingIn}
                    >
                      {isLoggingIn ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          Aguardando conclusão do login no navegador...
                        </>
                      ) : (
                        <>
                          <ExternalLink size={14} />
                          Abrir Navegador Real e Capturar Sessão
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* Modo 3: Importar Arquivo */}
                {activeMode === 'file' && (
                  <div className={styles.modeContent}>
                    <p className={styles.modeHelp}>
                      Selecione o arquivo <code>workana_storage_state.json</code> ou arquivo{' '}
                      <code>.har</code> exportado do DevTools.
                    </p>
                    <label className={styles.fileDropZone}>
                      <Upload size={20} />
                      <span>
                        {isSavingSession
                          ? 'Importando arquivo...'
                          : 'Clique para selecionar arquivo (.json, .har, .txt)'}
                      </span>
                      <input
                        type="file"
                        accept=".json,.har,.txt"
                        onChange={handleFileImport}
                        disabled={isSavingSession}
                        style={{ display: 'none' }}
                      />
                    </label>
                  </div>
                )}
              </div>
            )}

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
                {realtime?.is_active ? (
                  `Canais: ${realtime?.channels ? realtime.channels.join(', ') : 'pt, en'}`
                ) : (
                  <button
                    onClick={handleStartRealtime}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--color-primary, #6366f1)',
                      cursor: 'pointer',
                      padding: 0,
                      fontSize: '0.8rem',
                      textDecoration: 'underline',
                    }}
                  >
                    Ativar listener WebSocket agora
                  </button>
                )}
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
