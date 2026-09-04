import React, { useState } from 'react';
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
} from 'lucide-react';
import styles from '../../pages/Settings.module.css';
import type { CredentialsStatus, SessionHealthResponse } from '../../services/api';
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
  const [activeMode, setActiveMode] = useState<'paste' | 'auto' | 'file'>('paste');

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

  const handlePasteFromClipboard = async () => {
    try {
      if (navigator?.clipboard?.readText) {
        const text = await navigator.clipboard.readText();
        if (text && text.trim()) {
          setSessionJson(text.trim());
          toast.success('Conteúdo colado da área de transferência!', 'Clipboard');
          return;
        }
      }
      toast.info('Área de transferência vazia ou sem permissão. Cole com Ctrl + V no campo.');
    } catch {
      toast.info('Não foi possível ler automaticamente. Use Ctrl + V no campo.');
    }
  };

  const sessionPill = getSessionPill();
  const isConnected = credentials.configured || credentials.session_ready;
  const displayEmail = credentials.email || sessionHealth?.account_email || accountEmail || null;

  // Render the 3-mode updater box
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
          <p className={styles.modeHelp}>
            Abre uma janela real do Chrome ou Edge no seu Windows para você fazer login no Workana
            ou resolver o desafio da Cloudflare. Ao finalizar, a sessão é capturada e salva
            automaticamente pelo sistema.
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
        </div>
      )}
    </div>
  );

  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Conexão Workana</h2>
      <p className={styles.sectionSubtitle}>Gerencie o acesso e a sessão da sua conta</p>

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
                    : sessionHealth?.status === 'blocked_waf'
                      ? styles.messageBoxWarning
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
              <button
                type="button"
                className="btn btn-primary w-full"
                onClick={handleSaveCredentials}
                disabled={!newCredentials.email || !newCredentials.password || isSaving}
              >
                {isSaving ? 'Salvando...' : 'Conectar Conta com Senha'}
              </button>
              <p className="text-xs text-muted mt-4 text-center flex items-center justify-center gap-2">
                <Lock size={13} />
                Suas credenciais são criptografadas e salvas apenas localmente no seu ambiente.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
