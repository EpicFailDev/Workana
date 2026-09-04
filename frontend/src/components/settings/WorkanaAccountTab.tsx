import React, { useState, useEffect } from 'react';
import {
  KeyRound,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clipboard,
  Globe,
  Upload,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Lock,
  Radio,
  Activity,
  Terminal,
  Cpu,
  Bookmark,
  ShieldCheck,
} from 'lucide-react';
import styles from '../../pages/Settings.module.css';
import {
  automationApi,
  type CredentialsStatus,
  type SessionHealthResponse,
  type SessionDiagnosticsResponse,
  type LocalSessionDetectionResponse,
} from '../../services/api';
import { useToast } from '../../context/ToastContext';

interface WorkanaAccountTabProps {
  credentials: CredentialsStatus;
  newCredentials: { email: string; password: string };
  setNewCredentials: React.Dispatch<React.SetStateAction<{ email: string; password: string }>>;
  showPassword: boolean;
  setShowPassword: React.Dispatch<React.SetStateAction<boolean>>;
  isSaving: boolean;
  handleSaveCredentials: () => void;
  handleGoogleLogin: () => void;
  isGoogleLogging: boolean;
  importMode: boolean;
  setImportMode: React.Dispatch<React.SetStateAction<boolean>>;
  sessionJson: string;
  setSessionJson: React.Dispatch<React.SetStateAction<string>>;
  accountEmail: string;
  setAccountEmail: React.Dispatch<React.SetStateAction<string>>;
  isImporting: boolean;
  handleImportSession: () => void;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleDisconnect: () => void;
  setCredentials: React.Dispatch<React.SetStateAction<CredentialsStatus>>;
  sessionHealth?: SessionHealthResponse | null;
  handleTestSessionHealth?: () => void;
  isCheckingHealth?: boolean;
}

export const WorkanaAccountTab: React.FC<WorkanaAccountTabProps> = ({
  credentials,
  newCredentials,
  setNewCredentials,
  showPassword,
  setShowPassword,
  isSaving,
  handleSaveCredentials,
  handleGoogleLogin,
  isGoogleLogging,
  importMode,
  setImportMode,
  sessionJson,
  setSessionJson,
  accountEmail,
  setAccountEmail,
  isImporting,
  handleImportSession,
  handleFileUpload,
  handleDisconnect,
  setCredentials,
  sessionHealth,
  handleTestSessionHealth,
  isCheckingHealth = false,
}) => {
  const { toast } = useToast();

  const [showSessionUpdater, setShowSessionUpdater] = useState<boolean>(() => {
    return (
      importMode ||
      (sessionHealth !== undefined && sessionHealth !== null && sessionHealth.status !== 'healthy')
    );
  });
  const [activeMode, setActiveMode] = useState<'paste' | 'auto' | 'file' | 'companion'>('paste');

  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false);
  const [diagnosticsData, setDiagnosticsData] = useState<SessionDiagnosticsResponse | null>(null);
  const [isRunningDiagnostics, setIsRunningDiagnostics] = useState<boolean>(false);

  const [localSession, setLocalSession] = useState<LocalSessionDetectionResponse | null>(null);
  const [isSyncingLocal, setIsSyncingLocal] = useState<boolean>(false);

  const [isAutoLogging, setIsAutoLogging] = useState<boolean>(false);
  const [autoLoginStep, setAutoLoginStep] = useState<number>(0);

  const [isCdpConnecting, setIsCdpConnecting] = useState<boolean>(false);
  const [showTerminal, setShowTerminal] = useState<boolean>(false);
  const [logs, setLogs] = useState<
    Array<{ time: string; text: string; status: 'ok' | 'info' | 'warn' }>
  >([
    { time: '08:00:00', text: 'Workana Accelerator Session Engine inicializado.', status: 'info' },
  ]);

  const addLog = (text: string, status: 'ok' | 'info' | 'warn' = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev.slice(-20), { time, text, status }]);
  };

  useEffect(() => {
    if (importMode) {
      setShowSessionUpdater(true);
      setActiveMode('paste');
    }
  }, [importMode]);

  // Detectar arquivos de sessão local existentes
  useEffect(() => {
    automationApi
      .detectLocalSession()
      .then((res) => {
        if (res && res.detected) {
          setLocalSession(res);
          addLog(`Sessão local detectada no disco (${res.cookies_count} cookies)`, 'ok');
        }
      })
      .catch(() => {});
  }, []);

  const handleSyncLocal = async () => {
    setIsSyncingLocal(true);
    try {
      addLog('Sincronizando arquivo local detectado para o Session Vault...', 'info');
      const res = await automationApi.syncLocalSession(localSession?.path || undefined);
      if (res.success) {
        toast.success(res.message, 'Sessão Sincronizada');
        addLog(res.message, 'ok');
        setCredentials((prev) => ({
          ...prev,
          configured: true,
          session_ready: true,
        }));
        if (handleTestSessionHealth) {
          handleTestSessionHealth();
        }
      } else {
        toast.error(res.message, 'Erro de Sincronização');
        addLog(res.message, 'warn');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha na sincronização';
      toast.error(msg, 'Erro');
      addLog(msg, 'warn');
    } finally {
      setIsSyncingLocal(false);
    }
  };

  const handleRunDiagnostics = async () => {
    setIsRunningDiagnostics(true);
    setShowDiagnostics(true);
    addLog('Iniciando diagnóstico guiado de 5 pontos...', 'info');
    try {
      const res = await automationApi.getSessionDiagnostics();
      setDiagnosticsData(res);
      addLog(
        `Diagnóstico concluído: Status ${res.overall.toUpperCase()}`,
        res.overall === 'optimal' ? 'ok' : 'warn'
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao rodar diagnóstico';
      toast.error(msg, 'Diagnóstico');
      addLog(msg, 'warn');
    } finally {
      setIsRunningDiagnostics(false);
    }
  };

  const handleAutonomousLogin = async () => {
    setIsAutoLogging(true);
    setAutoLoginStep(1);
    addLog('Disparando motor Playwright Stealth headless...', 'info');

    const timer1 = setTimeout(() => {
      setAutoLoginStep(2);
      addLog('Inserindo credenciais com jitter biométrico humano...', 'info');
    }, 1800);

    const timer2 = setTimeout(() => {
      setAutoLoginStep(3);
      addLog('Avaliando desafio Cloudflare Turnstile...', 'info');
    }, 3800);

    try {
      const res = await automationApi.autoLogin({
        email: newCredentials.email || undefined,
        password: newCredentials.password || undefined,
      });

      clearTimeout(timer1);
      clearTimeout(timer2);

      if (res.success) {
        setAutoLoginStep(4);
        toast.success(res.message, 'Autenticação Autônoma');
        addLog(
          `Login autônomo concluído! ${res.cookies_count || 0} cookies salvos no Vault.`,
          'ok'
        );
        setCredentials((prev) => ({
          ...prev,
          configured: true,
          session_ready: true,
          email: res.email || prev.email,
        }));
        if (handleTestSessionHealth) {
          handleTestSessionHealth();
        }
      } else {
        setAutoLoginStep(0);
        toast.error(res.message, 'Falha no Login');
        addLog(`Falha no login autônomo: ${res.message}`, 'warn');
      }
    } catch (err: unknown) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setAutoLoginStep(0);
      const msg = err instanceof Error ? err.message : 'Erro ao autenticar';
      toast.error(msg, 'Erro');
      addLog(msg, 'warn');
    } finally {
      setIsAutoLogging(false);
    }
  };

  const handleCdpConnect = async () => {
    setIsCdpConnecting(true);
    addLog('Conectando via Chrome DevTools Protocol na porta 9222...', 'info');
    try {
      const res = await automationApi.cdpConnect(9222);
      if (res.success) {
        toast.success(res.message, 'Conexão CDP');
        addLog(res.message, 'ok');
        setCredentials((prev) => ({
          ...prev,
          configured: true,
          session_ready: true,
        }));
        if (handleTestSessionHealth) {
          handleTestSessionHealth();
        }
      } else {
        toast.warning(res.message, 'Aviso');
        addLog(res.message, 'warn');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha na conexão CDP';
      toast.error(msg, 'Erro');
      addLog(msg, 'warn');
    } finally {
      setIsCdpConnecting(false);
    }
  };

  const handlePasteFromClipboard = async () => {
    try {
      if (navigator?.clipboard?.readText) {
        const text = await navigator.clipboard.readText();
        if (text && text.trim()) {
          setSessionJson(text.trim());
          toast.success('Conteúdo colado da área de transferência!', 'Clipboard');
          addLog('Conteúdo colado via Clipboard.', 'info');
          return;
        }
      }
      toast.info('Área de transferência vazia ou sem permissão. Cole com Ctrl + V no campo.');
    } catch {
      toast.info('Não foi possível ler automaticamente. Use Ctrl + V no campo.');
    }
  };

  const getSessionPill = () => {
    if (!credentials.configured && !credentials.session_ready) {
      return {
        label: 'Desconectada',
        className: styles.badgeError,
        dotColor: '#ef4444',
      };
    }
    if (!sessionHealth) {
      return {
        label: credentials.session_ready ? 'Conectado (Salvo)' : 'Desconhecido',
        className: styles.badgeWarning,
        dotColor: '#f59e0b',
      };
    }
    if (sessionHealth.status === 'healthy') {
      return {
        label: 'Ativa & Saudável',
        className: styles.badgeSuccess,
        dotColor: '#10b981',
      };
    }
    if (sessionHealth.status === 'warning' || sessionHealth.status === 'saved_offline') {
      return {
        label: 'Atenção (Cookies)',
        className: styles.badgeWarning,
        dotColor: '#f59e0b',
      };
    }
    if (sessionHealth.status === 'blocked_waf') {
      return {
        label: 'Desafio Cloudflare (WAF)',
        className: styles.badgeWarning,
        dotColor: '#f59e0b',
      };
    }
    if (sessionHealth.status === 'expired') {
      return {
        label: 'Expirada',
        className: styles.badgeError,
        dotColor: '#ef4444',
      };
    }
    return {
      label: 'Desconectada',
      className: styles.badgeError,
      dotColor: '#ef4444',
    };
  };

  const sessionPill = getSessionPill();
  const isConnected = credentials.configured || credentials.session_ready;
  const displayEmail = credentials.email || sessionHealth?.account_email || accountEmail || null;

  // Cálculo do Health Score (0-100)
  const healthScore =
    sessionHealth?.health_score !== undefined
      ? sessionHealth.health_score
      : sessionHealth?.status === 'healthy'
        ? 100
        : sessionHealth?.status === 'warning'
          ? 65
          : isConnected
            ? 50
            : 0;

  const getThemeColor = () => {
    if (healthScore >= 75) return '#10b981';
    if (healthScore >= 40) return '#f59e0b';
    return '#ef4444';
  };
  const themeColor = getThemeColor();

  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (healthScore / 100) * circumference;

  const bookmarkletCode = `javascript:(function(){try{const c=document.cookie;if(!c){alert('Nenhum cookie encontrado.');return;}fetch('http://localhost:8000/api/v1/automation/workana/stream-sync',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:c})}).then(r=>r.json()).then(d=>alert(d.message||'Sincronizado!')).catch(e=>alert('Erro:'+e));}catch(err){alert('Falha:'+err);}})();`;

  // Renderizador do Updater Box unificado
  const renderUpdaterBox = (titlePrefix: string = 'Atualização e Renovação de Cookies') => (
    <div className={styles.updaterBox}>
      <div className={styles.updaterHeader}>
        <span className={styles.updaterTitle}>
          <Sparkles size={16} color="var(--color-primary, #6366f1)" />
          {titlePrefix}
        </span>
        {isConnected && (
          <button
            type="button"
            className="btn btn-secondary text-xs"
            style={{ padding: '4px 8px' }}
            onClick={() => {
              setShowSessionUpdater(false);
              setImportMode(false);
            }}
          >
            Fechar
          </button>
        )}
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
        <button
          type="button"
          className={`${styles.modeTab} ${activeMode === 'companion' ? styles.modeTabActive : ''}`}
          onClick={() => setActiveMode('companion')}
        >
          <Bookmark size={14} />
          <span>Zero-Click Companion</span>
        </button>
      </div>

      {/* Modo 1: Colar Cookies / Clipboard */}
      {activeMode === 'paste' && (
        <div className={styles.modeContent}>
          <div className={styles.pasteActionBar}>
            <p className={styles.modeHelp}>
              Aceita <strong>JSON</strong> (extensão Cookie-Editor), <strong>HAR</strong> ou{' '}
              <strong>string direta de cookies</strong> (ex:{' '}
              <code>cf_clearance=...; workana_session=...</code>).
            </p>
            <button
              type="button"
              className={styles.clipboardQuickBtn}
              onClick={handlePasteFromClipboard}
              title="Colar automaticamente da área de transferência"
            >
              <Clipboard size={12} />
              Colar do Clipboard
            </button>
          </div>

          <textarea
            className={styles.sessionTextarea}
            rows={4}
            placeholder="Cole aqui os cookies ou JSON da sessão (Ctrl + V)..."
            value={sessionJson}
            onChange={(e) => setSessionJson(e.target.value)}
          />

          <div className={styles.formGroup} style={{ marginBottom: '8px' }}>
            <label className={styles.label} style={{ fontSize: '0.78rem' }}>
              Email associado à conta Workana (opcional)
            </label>
            <input
              type="email"
              className={styles.input}
              placeholder="seuemail@gmail.com"
              value={accountEmail || displayEmail || ''}
              onChange={(e) => setAccountEmail(e.target.value)}
            />
          </div>

          <button
            type="button"
            className={styles.primaryActionBtn}
            onClick={handleImportSession}
            disabled={isImporting || !sessionJson.trim()}
          >
            {isImporting ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Validando e salvando cookies...
              </>
            ) : (
              <>
                <CheckCircle2 size={15} />
                Salvar e Sincronizar Cookies
              </>
            )}
          </button>

          <div className={styles.quickTip}>
            💡 <strong>Dica rápida:</strong> Abra o Workana no seu Chrome ou Edge, abra a extensão{' '}
            <em>Cookie-Editor</em>, clique em <strong>Export &gt; Export as JSON</strong> e depois
            clique no botão <strong>Colar do Clipboard</strong> acima.
          </div>
        </div>
      )}

      {/* Modo 2: Abrir Navegador Automático */}
      {activeMode === 'auto' && (
        <div className={styles.modeContent}>
          <div
            className={styles.quickTip}
            style={{ marginBottom: '12px', borderLeftColor: '#f59e0b' }}
          >
            ℹ️ <strong>Ambiente Docker:</strong> Se o sistema estiver rodando via Docker (
            <code>INICIAR.bat</code> opção 1), o container não possui interface gráfica (XServer)
            para abrir uma janela na tela do seu computador. Nesse caso, utilize a aba{' '}
            <strong>Colar Cookies</strong> ou execute a opção <strong>[4] Login no Workana</strong>{' '}
            no <code>INICIAR.bat</code> no Windows.
          </div>
          <p className={styles.modeHelp}>
            Abre uma janela real do Chrome ou Edge na sua máquina para você fazer login no Workana
            ou resolver o desafio da Cloudflare (requer execução fora do Docker). Ao finalizar, a
            sessão é capturada e salva automaticamente pelo sistema.
          </p>
          <button
            type="button"
            className={styles.primaryActionBtn}
            onClick={handleGoogleLogin}
            disabled={isGoogleLogging}
          >
            {isGoogleLogging ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Aguardando conclusão do login no navegador...
              </>
            ) : (
              <>
                <Globe size={15} />
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
            Selecione o arquivo <code>workana_storage_state.json</code> gerado pelo Playwright ou o
            arquivo <code>.har</code> exportado da aba Network do DevTools.
          </p>
          <label className={styles.fileDropZone}>
            <Upload size={22} color="var(--color-primary-light, #818cf8)" />
            <span>
              {isImporting
                ? 'Importando arquivo...'
                : 'Clique para selecionar arquivo (.json, .har, .txt)'}
            </span>
            <input
              type="file"
              accept=".json,.har,.txt"
              onChange={handleFileUpload}
              disabled={isImporting}
              style={{ display: 'none' }}
            />
          </label>

          {sessionJson.trim() && (
            <div style={{ marginTop: '16px' }}>
              <div className={styles.quickTip} style={{ marginBottom: '12px' }}>
                📄 <strong>Arquivo pronto para sincronização.</strong> Clique abaixo para confirmar
                e conectar a conta:
              </div>
              <button
                type="button"
                className={styles.primaryActionBtn}
                onClick={handleImportSession}
                disabled={isImporting}
              >
                {isImporting ? (
                  <>
                    <RefreshCw size={14} className="animate-spin" />
                    Validando e salvando cookies...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={15} />
                    Salvar e Sincronizar Cookies
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modo 4: Zero-Click Companion & Bookmarklet */}
      {activeMode === 'companion' && (
        <div className={styles.modeContent}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '10px',
                padding: '14px',
              }}
            >
              <div className="font-bold text-xs text-white mb-1 flex items-center gap-1">
                <Bookmark size={14} color="#818cf8" /> Smart Bookmarklet 1-Click
              </div>
              <p className="text-xs text-muted mb-3">
                Arraste o link abaixo para sua barra de favoritos do navegador.
              </p>
              <a
                href={bookmarkletCode}
                onClick={(e) => {
                  e.preventDefault();
                  toast.info('Arraste este botão para a sua Barra de Favoritos do Navegador!');
                }}
                className="btn btn-primary w-full text-xs font-bold"
                style={{ cursor: 'grab', textAlign: 'center', display: 'block' }}
              >
                ⚡ Sincronizar Workana
              </a>
            </div>

            <div
              style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '10px',
                padding: '14px',
              }}
            >
              <div className="font-bold text-xs text-white mb-1 flex items-center gap-1">
                <Globe size={14} color="#34d399" /> Chrome CDP Attach
              </div>
              <p className="text-xs text-muted mb-3">
                Conecta ao Chrome aberto com <code>--remote-debugging-port=9222</code>.
              </p>
              <button
                type="button"
                className="btn btn-secondary w-full text-xs"
                onClick={handleCdpConnect}
                disabled={isCdpConnecting}
              >
                {isCdpConnecting ? 'Conectando...' : 'Conectar Chrome Aberto'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Conexão Workana</h2>
      <p className={styles.sectionSubtitle}>Gerencie o acesso e a sessão da sua conta</p>

      {/* 1. COCKPIT HEADER COM RADAR GAUGE & METRICS */}
      <div className={styles.cockpitHeader}>
        <div className={styles.radarWidget}>
          <div className={styles.radarCircleWrapper}>
            <div
              className={styles.radarPulseRing}
              style={{
                boxShadow: `0 0 16px ${themeColor}`,
                border: `1px solid ${themeColor}`,
              }}
            />
            <svg className={styles.healthGaugeSvg} viewBox="0 0 80 80">
              <circle className={styles.healthGaugeBg} cx="40" cy="40" r={radius} strokeWidth="6" />
              <circle
                className={styles.healthGaugeProgress}
                cx="40"
                cy="40"
                r={radius}
                strokeWidth="6"
                stroke={themeColor}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <div className={styles.healthScoreCenter}>
              <span className={styles.healthScoreNumber} style={{ color: themeColor }}>
                {healthScore}%
              </span>
              <span className={styles.healthScoreLabel}>Health</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Radio size={16} color={themeColor} className="animate-pulse" />
                {isConnected ? 'Conta Conectada' : 'Aguardando Conexão'}
              </h3>
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: `${themeColor}22`,
                  color: themeColor,
                  border: `1px solid ${themeColor}44`,
                  fontWeight: 600,
                }}
              >
                {sessionHealth?.status?.toUpperCase() || (isConnected ? 'SAVED' : 'OFFLINE')}
              </span>
            </div>
            <p className="text-xs text-muted" style={{ maxWidth: '420px' }}>
              {displayEmail
                ? `Sessão ativa vinculada a ${displayEmail}`
                : 'Cofre AES-256-GCM pronto para sincronização de cookies.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn btn-secondary text-xs"
            onClick={handleRunDiagnostics}
            disabled={isRunningDiagnostics}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Activity size={13} className={isRunningDiagnostics ? 'animate-spin' : ''} />
            <span>Auto-Diagnóstico 5-Pontos</span>
          </button>

          <button
            type="button"
            className="btn btn-secondary text-xs"
            onClick={() => setShowTerminal(!showTerminal)}
            title="Exibir terminal de logs em tempo real"
          >
            <Terminal size={13} />
          </button>
        </div>
      </div>

      {/* 2. AUTO-DISCOVERY BANNER */}
      {localSession?.detected && !isConnected && (
        <div className={styles.discoveryBanner}>
          <div className={styles.discoveryInfo}>
            <Sparkles size={20} color="#818cf8" />
            <div>
              <div className="text-xs font-bold text-white">
                Sessão local detectada no seu computador ({localSession.cookies_count} cookies)!
              </div>
              <div className="text-xs text-muted">
                Arquivo <code>{localSession.path}</code> encontrado. Conecte sua conta com 1 clique.
              </div>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleSyncLocal}
            disabled={isSyncingLocal}
          >
            {isSyncingLocal ? 'Sincronizando...' : '⚡ Sincronizar Sessão Local'}
          </button>
        </div>
      )}

      {/* 3. DIAGNOSTICS CHECKLIST */}
      {showDiagnostics && (
        <div
          className={styles.card}
          style={{
            marginBottom: '20px',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            background: 'rgba(15, 23, 42, 0.8)',
          }}
        >
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-sm font-bold text-primary flex items-center gap-2">
              <Activity size={16} />
              Diagnóstico de Integridade em 5 Pontos (Health Check)
            </h4>
            <button
              type="button"
              className="btn btn-secondary text-xs"
              onClick={() => setShowDiagnostics(false)}
            >
              Ocultar
            </button>
          </div>

          <div className={styles.diagnosticsChecklist}>
            {diagnosticsData?.diagnostics?.map((item) => (
              <div key={item.id} className={styles.diagnosticRow}>
                <div className={styles.diagnosticRowName}>
                  {item.status === 'ok' ? (
                    <CheckCircle2 size={16} color="#10b981" />
                  ) : item.status === 'warning' ? (
                    <AlertTriangle size={16} color="#f59e0b" />
                  ) : (
                    <AlertTriangle size={16} color="#ef4444" />
                  )}
                  <span>{item.name}</span>
                </div>
                <div className={styles.diagnosticRowDetail}>{item.detail}</div>
              </div>
            )) || (
              <div className="text-xs text-muted py-2 text-center">
                Carregando diagnóstico do Session Vault...
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. CARD PRINCIPAL COM STATUS E TELEMETRIA */}
      <div className={styles.card}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold">Status da Conexão</h3>
          <span className={sessionPill.className}>
            ● {isConnected ? 'Conectado' : 'Desconectado'}
            {credentials.login_method === 'google' ? ' via Google' : ''}
            {displayEmail ? ` como ${displayEmail}` : ''}
          </span>
        </div>

        {isConnected ? (
          <div>
            {/* Bloco de Telemetria e Diagnóstico da Sessão */}
            <div className={styles.sessionDiagnostics}>
              <div className={styles.diagnosticsHeader}>
                <div className={styles.diagnosticsTitle}>
                  <KeyRound size={18} color="var(--color-primary, #6366f1)" />
                  Diagnóstico da Sessão Workana
                </div>
                {handleTestSessionHealth && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleTestSessionHealth}
                    disabled={isCheckingHealth}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                    title="Testar validade dos cookies e conexão com o Workana"
                  >
                    <RefreshCw size={13} className={isCheckingHealth ? 'animate-spin' : ''} />
                    {isCheckingHealth ? 'Verificando...' : 'Testar Conexão'}
                  </button>
                )}
              </div>

              <div className={styles.diagnosticsGrid}>
                <div className={styles.diagnosticItem}>
                  <div className={styles.diagnosticLabel}>Status da Sessão</div>
                  <div className={styles.diagnosticValue}>
                    <span
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: sessionPill.dotColor,
                        display: 'inline-block',
                      }}
                    />
                    {sessionPill.label}
                  </div>
                </div>

                <div className={styles.diagnosticItem}>
                  <div className={styles.diagnosticLabel}>Cookies Ativos</div>
                  <div className={styles.diagnosticValue}>
                    {sessionHealth?.cookies_count !== undefined
                      ? `${sessionHealth.cookies_count} cookies`
                      : credentials.session_ready
                        ? 'Cookies salvos'
                        : '0 cookies'}
                  </div>
                </div>

                <div className={styles.diagnosticItem}>
                  <div className={styles.diagnosticLabel}>Cloudflare Clearance</div>
                  <div className={styles.diagnosticValue}>
                    {sessionHealth?.has_cloudflare_clearance ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 size={15} /> Ativo
                      </span>
                    ) : (
                      <span className="text-amber-400 flex items-center gap-1">
                        <AlertTriangle size={15} /> Pendente
                      </span>
                    )}
                  </div>
                </div>

                <div className={styles.diagnosticItem}>
                  <div className={styles.diagnosticLabel}>Conta Conectada</div>
                  <div
                    className={styles.diagnosticValue}
                    style={{ fontSize: '0.85rem', wordBreak: 'break-all' }}
                  >
                    {displayEmail || 'Sessão Salva'}
                  </div>
                </div>
              </div>

              {/* Mensagem de Diagnóstico */}
              <div
                className={`${styles.messageBox} ${
                  sessionHealth?.status === 'healthy'
                    ? styles.messageBoxHealthy
                    : styles.messageBoxWarning
                }`}
              >
                {sessionHealth?.status === 'healthy' ? (
                  <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
                ) : (
                  <AlertTriangle size={18} style={{ flexShrink: 0 }} />
                )}
                <div>
                  {sessionHealth?.status === 'blocked_waf' ? (
                    <div>
                      <strong>Desafio Cloudflare WAF detectado:</strong> A sondagem direta foi
                      bloqueada. A automação usa o navegador Playwright com emulação humana, mas
                      você pode atualizar os cookies abaixo via <em>Colar do Clipboard</em> ou{' '}
                      <em>Abrir Navegador</em> para garantir envio contínuo.
                    </div>
                  ) : (
                    sessionHealth?.message ||
                    'Sua sessão do navegador está salva e será usada para enviar propostas. O worker restaura os cookies localmente — não precisa de senha.'
                  )}
                </div>
              </div>

              {/* Barra de Ações Rápidas */}
              <div className={styles.actionRow}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    setShowSessionUpdater(!showSessionUpdater);
                    setImportMode(!showSessionUpdater);
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <KeyRound size={14} />
                  <span>
                    {showSessionUpdater
                      ? 'Ocultar Atualizador de Cookies'
                      : 'Renovar / Injetar Cookies'}
                  </span>
                  {showSessionUpdater ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleGoogleLogin}
                  disabled={isGoogleLogging}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Globe size={14} />
                  <span>
                    {isGoogleLogging ? 'Aguardando login no navegador...' : 'Refazer Login Google'}
                  </span>
                </button>

                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={handleDisconnect}
                  style={{ marginLeft: 'auto' }}
                >
                  Desconectar
                </button>
              </div>
            </div>

            {/* Painel Expansível de Atualização */}
            {showSessionUpdater && renderUpdaterBox()}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Modo de Conexão Rápida / Inteligente (Padrão) */}
            <div
              style={{
                padding: '16px',
                background: 'rgba(59, 130, 246, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(59, 130, 246, 0.2)',
              }}
            >
              <h4 className="text-base font-bold text-primary mb-2 flex items-center gap-2">
                <Globe size={18} />
                Conectar via Sessão do Navegador (Recomendado)
              </h4>
              <p className="text-xs text-muted mb-4">
                Importe seus cookies de sessão diretamente pelo clipboard, abra uma janela do
                navegador real ou carregue um arquivo exportado.
              </p>

              {renderUpdaterBox('Conectar com Sessão / Cookies')}
            </div>

            <div className={styles.divider}>ou conecte usando email e senha</div>

            <div className="space-y-4">
              {isAutoLogging && (
                <div className={styles.stepperContainer}>
                  <div
                    className={`${styles.stepItem} ${autoLoginStep >= 1 ? styles.stepActive : ''}`}
                  >
                    <span className={styles.stepNumber}>1</span>
                    <span>Conexão Segura</span>
                  </div>
                  <div
                    className={`${styles.stepItem} ${autoLoginStep >= 2 ? styles.stepActive : ''}`}
                  >
                    <span className={styles.stepNumber}>2</span>
                    <span>Credenciais</span>
                  </div>
                  <div
                    className={`${styles.stepItem} ${autoLoginStep >= 3 ? styles.stepActive : ''}`}
                  >
                    <span className={styles.stepNumber}>3</span>
                    <span>WAF Bypass</span>
                  </div>
                  <div
                    className={`${styles.stepItem} ${autoLoginStep >= 4 ? styles.stepDone : ''}`}
                  >
                    <span className={styles.stepNumber}>4</span>
                    <span>Vault OK</span>
                  </div>
                </div>
              )}

              <div className={styles.formGroup}>
                <label className={styles.label}>Email</label>
                <input
                  type="email"
                  className={styles.input}
                  placeholder="email@workana.com"
                  value={newCredentials.email}
                  onChange={(e) => setNewCredentials({ ...newCredentials, email: e.target.value })}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Senha</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className={styles.input}
                    placeholder="••••••••"
                    value={newCredentials.password}
                    onChange={(e) =>
                      setNewCredentials({ ...newCredentials, password: e.target.value })
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
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
                    {showPassword ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  className="btn btn-primary flex-1"
                  onClick={handleSaveCredentials}
                  disabled={
                    !newCredentials.email || !newCredentials.password || isSaving || isAutoLogging
                  }
                >
                  {isSaving ? 'Salvando...' : 'Conectar Conta com Senha'}
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleAutonomousLogin}
                  disabled={!newCredentials.email || !newCredentials.password || isAutoLogging}
                  title="Autenticar em modo headless com Playwright Stealth"
                >
                  {isAutoLogging ? 'Autenticando...' : '⚡ Login Autônomo'}
                </button>
              </div>

              <p className="text-xs text-muted mt-4 text-center flex items-center justify-center gap-2">
                <Lock size={13} />
                Suas credenciais são criptografadas com envelope AES-256-GCM.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 5. TERMINAL DRAWER RETRÁTIL (RAYCAST STYLE) */}
      {showTerminal && (
        <div className={styles.terminalDrawer}>
          <div className={styles.terminalHeader}>
            <div className={styles.terminalDots}>
              <span className={styles.terminalDot} style={{ background: '#ef4444' }} />
              <span className={styles.terminalDot} style={{ background: '#f59e0b' }} />
              <span className={styles.terminalDot} style={{ background: '#10b981' }} />
            </div>
            <span>Workana Session Stream & Telemetry</span>
            <button
              type="button"
              onClick={() => setLogs([])}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                fontSize: '0.7rem',
              }}
            >
              Limpar
            </button>
          </div>
          <div className={styles.terminalBody}>
            {logs.map((l, i) => (
              <div key={i} className={styles.terminalLine}>
                <span className={styles.terminalTime}>[{l.time}]</span>
                <span
                  style={{
                    color:
                      l.status === 'ok' ? '#34d399' : l.status === 'warn' ? '#fbbf24' : '#93c5fd',
                  }}
                >
                  {l.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
