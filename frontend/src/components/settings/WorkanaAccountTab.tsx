import React from 'react';
import styles from '../../pages/Settings.module.css';
import type { CredentialsStatus } from '../../services/api';

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
}) => {
  return (
    <div className={styles.animated}>
      <h2 className={styles.sectionTitle}>Conexão Workana</h2>
      <p className={styles.sectionSubtitle}>Gerencie o acesso à sua conta</p>

      <div className={styles.card}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold">Status da Conexão</h3>
          {credentials.configured ? (
            <span className="badge badge-success">
              ● Conectado{credentials.login_method === 'google' ? ' via Google' : ''}{' '}
              {credentials.email ? `como ${credentials.email}` : ''}
            </span>
          ) : (
            <span className="badge badge-neutral">● Desconectado</span>
          )}
        </div>

        {credentials.login_method === 'google' && credentials.session_ready ? (
          <div className="text-center py-6">
            <div className="mb-3 text-5xl">🔐</div>
            <p className="mb-1">
              Sua sessão do navegador está salva e será usada para enviar propostas.
            </p>
            <p className="text-xs text-muted mb-4">
              O worker restaura os cookies localmente — não precisa de senha.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <button
                className="btn btn-secondary"
                onClick={handleGoogleLogin}
                disabled={isGoogleLogging}
              >
                {isGoogleLogging ? 'Aguardando login no navegador...' : 'Refazer Login Google'}
              </button>
              <button className="btn btn-secondary" onClick={() => setImportMode(!importMode)}>
                Importar Sessão
              </button>
              <button className="btn btn-danger" onClick={handleDisconnect}>
                Desconectar
              </button>
            </div>
          </div>
        ) : credentials.configured ? (
          <div className="text-center py-8">
            <div className="mb-4 text-6xl">🔒</div>
            <p className="mb-6">Sua conta está conectada e segura.</p>
            <button
              className="btn btn-secondary"
              onClick={() => setCredentials({ configured: false, email: null })}
            >
              Desconectar / Alterar Conta
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            <div
              style={{
                padding: '16px',
                background: 'rgba(59, 130, 246, 0.05)',
                borderRadius: '8px',
                border: '1px solid rgba(59, 130, 246, 0.2)',
              }}
            >
              <h4 className="text-base font-bold text-primary mb-2 flex items-center gap-2">
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <path
                    fill="#EA4335"
                    d="M12 5.04c1.62 0 3.06.56 4.2 1.65l3.1-3.1C17.4 1.67 14.9.68 12 .68 7.36.68 3.36 3.3 1.55 7.11l3.62 2.8C6 7.17 8.77 5.04 12 5.04z"
                  />
                  <path
                    fill="#4285F4"
                    d="M23.32 12.28c0-.85-.08-1.48-.24-2.13H12v3.86h6.5c-.14.7-.84 1.74-2.42 2.44l3.54 2.74c2.11-1.95 3.7-4.82 3.7-6.91z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.17 14.09a6.7 6.7 0 0 1-.35-2.09c0-.72.13-1.42.34-2.09l-3.62-2.8C.62 8.88 0 10.37 0 12s.63 3.12 1.54 4.89l3.63-2.8z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23.32c3.05 0 5.62-1 7.49-2.73l-3.54-2.74c-1.02.72-2.37 1.22-3.95 1.22-3.23 0-6-2.13-6.84-5.09l-3.63 2.8C3.36 20.7 7.36 23.32 12 23.32z"
                  />
                </svg>
                Login com Conta Google / Importar Sessão
              </h4>
              <p className="text-xs text-muted mb-3">
                Como o sistema roda dentro do Docker, o navegador para o login com Google deve ser
                aberto no Windows pelo script <strong>LOGIN-WORKANA.bat</strong>:
              </p>
              <ol
                className="text-xs text-muted space-y-1 pl-4 mb-4"
                style={{ listStyleType: 'decimal' }}
              >
                <li>
                  Dê dois cliques no arquivo{' '}
                  <strong>
                    <code>LOGIN-WORKANA.bat</code>
                  </strong>{' '}
                  na pasta do projeto.
                </li>
                <li>Faça o login com sua conta Google na janela do Chrome que abrir.</li>
                <li>
                  O script fechará o navegador e{' '}
                  <strong>copiará a sessão para sua Área de Transferência</strong> automaticamente.
                </li>
                <li>
                  Volte aqui, cole (<code>Ctrl + V</code>) ou clique em <em>Carregar Arquivo</em> e
                  salve.
                </li>
              </ol>

              <div className="flex justify-between items-center mb-2">
                <label className={styles.label} style={{ margin: 0, fontWeight: 'bold' }}>
                  JSON da Sessão / Cookies
                </label>
                <label
                  className="btn btn-secondary text-xs"
                  style={{ cursor: 'pointer', margin: 0, padding: '4px 8px' }}
                >
                  📁 Carregar Arquivo (.json / .har)
                  <input
                    type="file"
                    accept=".json,.har,.txt"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>

              <textarea
                className={styles.input}
                rows={5}
                style={{ fontFamily: 'monospace', fontSize: '11px' }}
                placeholder="Cole aqui a sessão com Ctrl + V..."
                value={sessionJson}
                onChange={(e) => setSessionJson(e.target.value)}
              />
              <div className={styles.formGroup} style={{ marginTop: '8px' }}>
                <label className={styles.label}>Email da conta Workana (opcional)</label>
                <input
                  type="email"
                  className={styles.input}
                  placeholder="seuemail@gmail.com"
                  value={accountEmail}
                  onChange={(e) => setAccountEmail(e.target.value)}
                />
              </div>
              <button
                className="btn btn-primary w-full mt-3"
                onClick={handleImportSession}
                disabled={isImporting || !sessionJson.trim()}
              >
                {isImporting ? 'Importando...' : 'Salvar e Conectar Sessão'}
              </button>
            </div>

            <div className={styles.divider}>ou use email e senha</div>

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
                className="btn btn-primary w-full"
                onClick={handleSaveCredentials}
                disabled={!newCredentials.email || !newCredentials.password || isSaving}
              >
                {isSaving ? 'Salvando...' : 'Conectar Conta'}
              </button>
              <p className="text-xs text-muted mt-4 text-center">
                Suas credenciais são criptografadas e salvas apenas no seu dispositivo.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
