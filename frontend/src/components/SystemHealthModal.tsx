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
  Zap,
} from 'lucide-react';
import { MaterialIcon } from './ui/MaterialIcon';
import {
  api,
  type AutomationStatus,
  type SessionHealthResponse,
  type AntibanStatus,
  type RealtimeStatusResponse,
} from '../services/api';
import { useToast } from '../context/ToastContext';
import { useExtensionBridge } from '../hooks/useExtensionBridge';
import styles from './SystemHealthModal.module.css';

interface SystemHealthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SystemHealthModal({ isOpen, onClose }: SystemHealthModalProps) {
  const { toast } = useToast();
  const { isExtensionActive, extensionVersion, isSyncingCookies, syncCookiesViaExtension } =
    useExtensionBridge();
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

  const handleTriggerExtensionSync = async () => {
    try {
      toast.info('Solicitando sincronização de cookies à extensão...', 'Extensão');
      const res = await syncCookiesViaExtension();
      if (res.success) {
        toast.success(
          res.count
            ? `${res.count} cookies sincronizados com sucesso!`
            : res.message || 'Cookies sincronizados com sucesso!',
          'Extensão Sincronizada'
        );
        await loadDiagnostics();
      } else {
        toast.warning(res.message || 'Extensão não encontrou cookies ou não respondeu.', 'Aviso');
      }
    } catch {
      toast.error('Erro ao comunicar com a extensão oficial.', 'Erro');
    }
  };

  const getSessionPill = () => {
    if (!sessionHealth) return { label: 'Desconhecido', className: styles.pillWarning };
    if (sessionHealth.status === 'healthy') {
      return { label: 'Ativa & Saudável', className: styles.pillHealthy };
    }
    if (sessionHealth.status === 'warning' || sessionHealth.status === 'saved_offline') {
      return { label: 'Atenção (Cookies)', className: styles.pillWarning };
    }
    if (sessionHealth.status === 'blocked_waf') {
      return {
        label: isExtensionActive ? 'Protegido p/ Extensão' : 'Desafio Cloudflare',
        className: isExtensionActive ? styles.pillHealthy : styles.pillWarning,
      };
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
                {sessionHealth?.status === 'blocked_waf' && isExtensionActive
                  ? 'Cloudflare WAF na API direta, mas protegido pela Extensão Oficial.'
                  : sessionHealth?.message || 'Verificando integridade da sessão...'}
              </div>
              {isExtensionActive ? (
                <div className={styles.extensionActiveCard}>
                  <div className={styles.extensionBadgeRow}>
                    <div className={styles.extensionBadgeIcon}>
                      <Zap size={15} />
                    </div>
                    <div className={styles.extensionBadgeText}>
                      <span className={styles.extensionBadgeTitle}>
                        Extensão Oficial Ativa (v{extensionVersion || '2.0.0'})
                      </span>
                      <span className={styles.extensionBadgeSub}>
                        Zero-Click Sync • Proteção Anti-Ban
                      </span>
                    </div>
                  </div>

                  <div className={styles.extensionActionsGrid}>
                    <button
                      type="button"
                      className={styles.syncExtensionPrimaryBtn}
                      onClick={handleTriggerExtensionSync}
                      disabled={isSyncingCookies}
                      title="Sincronizar cookies do Workana via extensão agora"
                    >
                      <RefreshCw size={13} className={isSyncingCookies ? 'animate-spin' : ''} />
                      <span>{isSyncingCookies ? 'Sincronizando...' : 'Sincronizar Agora'}</span>
                    </button>

                    <button
                      type="button"
                      className={styles.openWorkanaBtn}
                      onClick={() => window.open('https://www.workana.com', '_blank')}
                      title="Abrir o Workana no seu navegador"
                    >
                      <ExternalLink size={13} />
                      <span>Abrir Workana</span>
                    </button>
                  </div>

                  <div className={styles.contingencyRow}>
                    <button
                      type="button"
                      className={styles.contingencyLink}
                      onClick={() => setShowSessionUpdater(!showSessionUpdater)}
                      title="Opções manuais caso a extensão esteja indisponível"
                    >
                      <KeyRound size={12} />
                      <span>
                        {showSessionUpdater ? 'Ocultar Opções' : 'Modo Contingência (Manual)'}
                      </span>
                      {showSessionUpdater ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  </div>
                </div>
              ) : (
                <div className={styles.extensionInactiveCard}>
                  <div className={styles.extensionNotice}>
                    <div className={styles.extensionNoticeHeader}>
                      <Sparkles size={14} color="#818cf8" />
                      <span>Extensão Não Detectada</span>
                    </div>
                    <p className={styles.extensionNoticeText}>
                      Carregue a pasta <code>extension/</code> no Chrome para sincronização
                      automática e envio protegido sem risco anti-ban.
                    </p>
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
                        {showSessionUpdater ? 'Ocultar Atualização' : 'Conectar / Injetar Cookies'}
                      </span>
                      {showSessionUpdater ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </button>
                  </div>
                </div>
              )}
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
                    {isExtensionActive
                      ? 'Opções de Contingência Manual'
                      : 'Atualização Rápida de Cookies & Sessão'}
                  </span>
                </div>

                {isExtensionActive && (
                  <div className={styles.contingencyAlert}>
                    <Shield size={15} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>Extensão Oficial em Operação:</strong> Seus cookies já são
                      sincronizados automaticamente pelo navegador real. Os métodos manuais abaixo
                      são necessários apenas em servidores remotos ou falha no navegador.
                    </div>
                  </div>
                )}

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
                        Aceita <strong>JSON</strong> de cookies, arquivo <strong>HAR</strong> ou{' '}
                        <strong>string bruta</strong> (ex:{' '}
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
                    <div
                      className={styles.quickTip}
                      style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}
                    >
                      <MaterialIcon
                        name="lightbulb"
                        size={18}
                        style={{ color: '#f59e0b', flexShrink: 0, marginTop: '2px' }}
                      />
                      <div>
                        <strong>Dica:</strong> Para não precisar colar cookies manualmente, mantenha
                        a <strong>Extensão Oficial do Workana Accelerator</strong> ativa no seu
                        navegador. Ela mantém a sessão sincronizada em segundo plano com zero
                        esforço.
                      </div>
                    </div>
                  </div>
                )}

                {/* Modo 2: Abrir Navegador Automático / Extensão */}
                {activeMode === 'auto' && (
                  <div className={styles.modeContent}>
                    {isExtensionActive ? (
                      <div
                        style={{
                          background:
                            'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%)',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          borderRadius: '8px',
                          padding: '12px',
                          marginBottom: '12px',
                          fontSize: '0.8rem',
                          lineHeight: '1.4',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            fontWeight: 600,
                            color: '#34d399',
                            marginBottom: '4px',
                          }}
                        >
                          <Zap size={14} />
                          Extensão Oficial Detectada & Ativa (v{extensionVersion || '2.0.0'})
                        </div>
                        <p style={{ margin: 0, color: 'var(--color-text-muted, #94a3b8)' }}>
                          Como você já está com a Extensão instalada no seu navegador,{' '}
                          <strong>você não precisa abrir o navegador pelo servidor Docker</strong>!
                          Suas propostas são enviadas diretamente pela aba do seu Chrome/Edge com
                          resolução transparente de Cloudflare e zero risco anti-ban.
                        </p>
                        <div
                          style={{
                            display: 'flex',
                            gap: '8px',
                            marginTop: '10px',
                            flexWrap: 'wrap',
                          }}
                        >
                          <button
                            type="button"
                            className={styles.primaryActionBtn}
                            style={{
                              flex: 1,
                              minWidth: '150px',
                              padding: '8px 12px',
                              fontSize: '0.78rem',
                            }}
                            onClick={() => window.open('https://www.workana.com', '_blank')}
                          >
                            <ExternalLink size={13} />
                            Abrir Workana no Navegador
                          </button>
                          <button
                            type="button"
                            className={styles.clipboardQuickBtn}
                            style={{ padding: '8px 12px', fontSize: '0.78rem' }}
                            onClick={handleTriggerExtensionSync}
                          >
                            <RefreshCw size={13} />
                            Sincronizar Cookies Agora
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div
                        style={{
                          background: 'rgba(245, 158, 11, 0.08)',
                          border: '1px solid rgba(245, 158, 11, 0.25)',
                          borderRadius: '8px',
                          padding: '10px',
                          marginBottom: '12px',
                          fontSize: '0.78rem',
                          color: '#fbbf24',
                          lineHeight: '1.4',
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '6px',
                        }}
                      >
                        <MaterialIcon
                          name="info"
                          size={18}
                          style={{ color: '#fbbf24', flexShrink: 0, marginTop: '2px' }}
                        />
                        <div>
                          <strong>Ambiente Docker:</strong> O servidor rodando em Docker não possui
                          interface gráfica (XServer) para abrir uma janela na sua tela. Se estiver
                          no Docker, use a aba <strong>Colar Cookies</strong> ou carregue a pasta{' '}
                          <code>extension/</code> no seu navegador em{' '}
                          <code>chrome://extensions</code>.
                        </div>
                      </div>
                    )}
                    <p className={styles.modeHelp}>
                      {isExtensionActive
                        ? 'Se desejar forçar o login automatizado via servidor (requer rodar fora do Docker):'
                        : 'Abre uma janela real do Chrome ou Edge no host para você fazer login ou resolver o desafio Cloudflare (requer execução fora do Docker):'}
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
                          Abrir Navegador pelo Servidor (Playwright)
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
