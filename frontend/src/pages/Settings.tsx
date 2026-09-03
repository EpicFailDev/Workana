import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Shield,
  Ban,
  Sliders,
  Settings as SettingsIcon,
  KeyRound,
  AlertTriangle,
} from 'lucide-react';
import styles from './Settings.module.css';
import {
  api,
  type CredentialsStatus,
  type AutomationConfig,
  type AntibanConfig,
  type AntibanStatus,
  type BlacklistedClient,
  type SessionHealthResponse,
} from '../services/api';
import { useToast } from '../context/ToastContext';
import Loader from '../components/Loader';
import CyberHeader from '../components/CyberHeader';
import {
  GeneralTab,
  WorkanaAccountTab,
  AutomationTab,
  AntibanTab,
  BlacklistTab,
  DangerZoneTab,
} from '../components/settings';

type SettingsTab = 'general' | 'workana' | 'automation' | 'antiban' | 'blacklist' | 'danger';

export default function Settings() {
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get('tab') as SettingsTab) || 'general';
  const [activeTab, setActiveTab] = useState<SettingsTab>(
    ['general', 'workana', 'automation', 'antiban', 'blacklist', 'danger'].includes(initialTab)
      ? initialTab
      : 'general'
  );

  // Config States
  const [currentTheme, setCurrentTheme] = useState('default');
  const [credentials, setCredentials] = useState<CredentialsStatus>({
    configured: false,
    email: null,
  });
  const [newCredentials, setNewCredentials] = useState({ email: '', password: '' });
  const [config, setConfig] = useState<AutomationConfig>({
    headless: true,
    delay_between_actions_ms: 2000,
    max_proposals_per_day: 10,
    auto_apply: false,
    preferred_template_id: null,
    gemini_api_key: '',
    user_full_name: '',
  });

  // Anti-Ban & Blacklist States
  const [antibanConfig, setAntibanConfig] = useState<AntibanConfig>({
    max_searches_per_hour: 30,
    min_delay_between_searches_sec: 5,
    max_delay_between_searches_sec: 15,
    cooldown_period_minutes: 15,
    safe_mode: true,
    user_agent_rotation: true,
  });
  const [antibanStatus, setAntibanStatus] = useState<AntibanStatus | null>(null);
  const [sessionHealth, setSessionHealth] = useState<SessionHealthResponse | null>(null);
  const [blacklist, setBlacklist] = useState<BlacklistedClient[]>([]);
  const [newClientName, setNewClientName] = useState('');
  const [newClientReason, setNewClientReason] = useState('');

  // UI States
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingAntiban, setIsSavingAntiban] = useState(false);
  const [isAddingBlacklist, setIsAddingBlacklist] = useState(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  // Login via Google / Import de sessão
  const [isGoogleLogging, setIsGoogleLogging] = useState(false);
  const [importMode, setImportMode] = useState(false);
  const [sessionJson, setSessionJson] = useState('');
  const [accountEmail, setAccountEmail] = useState('');
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [
          credentialsStatus,
          automationConfig,
          antibanCfg,
          antibanStat,
          blacklistData,
          healthData,
        ] = await Promise.allSettled([
          api.getCredentialsStatus(),
          api.getAutomationConfig(),
          api.getAntibanConfig(),
          api.getAntibanStatus(),
          api.getBlacklistedClients(),
          api.getSessionHealth(),
        ]);

        if (credentialsStatus.status === 'fulfilled') setCredentials(credentialsStatus.value);
        if (automationConfig.status === 'fulfilled') {
          setConfig((prev) => ({
            ...prev,
            ...automationConfig.value,
            gemini_api_key: automationConfig.value.gemini_api_key || '',
            user_full_name: automationConfig.value.user_full_name || '',
          }));
        }
        if (antibanCfg.status === 'fulfilled') setAntibanConfig(antibanCfg.value);
        if (antibanStat.status === 'fulfilled') setAntibanStatus(antibanStat.value);
        if (blacklistData.status === 'fulfilled') setBlacklist(blacklistData.value?.clients || []);
        if (healthData.status === 'fulfilled') setSessionHealth(healthData.value);
      } catch (error) {
        console.error('Failed to load settings:', error);
        toast.error('Erro ao carregar configurações.');
      } finally {
        setIsLoading(false);
      }
    };

    const savedTheme = localStorage.getItem('theme') || 'default';
    setCurrentTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    loadSettings();
  }, []);

  const changeTheme = (theme: string) => {
    setCurrentTheme(theme);
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    toast.info(`Tema alterado para ${theme}`);
  };

  const handleSaveCredentials = async () => {
    setIsSaving(true);
    try {
      const response: any = await api.updateCredentials(newCredentials);
      if (response.success) {
        setCredentials({ configured: true, email: newCredentials.email });
        setNewCredentials({ email: '', password: '' });
        toast.success('Credenciais salvas com sucesso!');
      } else {
        toast.error(response.message || 'Erro ao salvar credenciais.');
      }
    } catch {
      toast.error('Erro de conexão ao salvar credenciais.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveConfig = async () => {
    setIsSaving(true);
    try {
      const response: any = await api.updateAutomationConfig({
        headless: config.headless,
        delay_between_actions_ms: config.delay_between_actions_ms,
        max_proposals_per_day: config.max_proposals_per_day,
        auto_apply: config.auto_apply,
        gemini_api_key: config.gemini_api_key,
        user_full_name: config.user_full_name,
      });

      if (response.success) {
        toast.success('Configurações salvas com sucesso!');
      } else {
        toast.error(response.message || 'Erro ao salvar.');
      }
    } catch {
      toast.error('Erro ao salvar configurações.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLogging(true);
    try {
      const response: any = await api.googleLogin();
      if (response.success) {
        toast.success(
          response.email ? `Conectado como ${response.email}` : 'Login via Google concluído!'
        );
        await reloadCredentials();
      } else {
        toast.error(response.message || 'Não foi possível abrir o login via Google.');
        if (
          response.message &&
          (response.message.includes('Docker') ||
            response.message.includes('XServer') ||
            response.message.includes('headless') ||
            response.message.includes('Importar'))
        ) {
          setImportMode(true);
        }
      }
    } catch (error: any) {
      toast.error(error.message || 'Erro ao tentar login com Google.');
    } finally {
      setIsGoogleLogging(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      if (content) {
        setSessionJson(content);
        toast.info(`Arquivo "${file.name}" carregado! Clique em "Salvar e Conectar Sessão".`);
      }
    };
    reader.readAsText(file);
  };

  const handleImportSession = async () => {
    if (!sessionJson.trim()) {
      toast.error('Cole o JSON da sessão para importar.');
      return;
    }
    setIsImporting(true);
    try {
      const response: any = await api.importSession(
        sessionJson.trim(),
        accountEmail.trim() || undefined
      );
      if (response.success) {
        toast.success(response.message || 'Sessão importada!');
        setSessionJson('');
        setImportMode(false);
        await reloadCredentials();
      } else {
        toast.error(response.message || 'Erro ao importar a sessão.');
      }
    } catch (error: any) {
      toast.error(error.message || 'Erro ao importar a sessão.');
    } finally {
      setIsImporting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      const response: any = await api.disconnectWorkana();
      if (response.success) {
        toast.success('Conexão com o Workana removida.');
        await reloadCredentials();
      } else {
        toast.error(response.message || 'Erro ao desconectar.');
      }
    } catch (error: any) {
      toast.error(error.message || 'Erro ao desconectar.');
    }
  };

  const reloadCredentials = async () => {
    try {
      const status = await api.getCredentialsStatus();
      setCredentials(status);
    } catch (error) {
      console.error('Failed to reload credentials:', error);
    }
  };

  const handleSaveAntibanConfig = async () => {
    setIsSavingAntiban(true);
    try {
      const res = await api.updateAntibanConfig(antibanConfig);
      if (res.success) {
        setAntibanConfig(res.config);
        toast.success('Configuração Anti-Ban atualizada com sucesso!');
      } else {
        toast.error(res.message || 'Erro ao atualizar Anti-Ban.');
      }
    } catch {
      toast.error('Falha de conexão ao salvar Anti-Ban.');
    } finally {
      setIsSavingAntiban(false);
    }
  };

  const handleTestSessionHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await api.getSessionHealth();
      setSessionHealth(res);
      if (res.status === 'healthy') {
        toast.success('Sessão Workana ativa e saudável!');
      } else if (res.status === 'warning') {
        toast.warning(res.message || 'Sessão requer atenção.');
      } else {
        toast.error(res.message || 'Sessão desconectada ou expirada.');
      }
    } catch {
      toast.error('Erro ao testar saúde da sessão.');
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const handleAddBlacklist = async () => {
    if (!newClientName.trim()) {
      toast.error('Informe o nome do cliente a bloquear.');
      return;
    }
    setIsAddingBlacklist(true);
    try {
      const res = await api.addToBlacklist({
        client_name: newClientName.trim(),
        reason: newClientReason.trim() || undefined,
      });
      if (res.success) {
        toast.success(res.message);
        setNewClientName('');
        setNewClientReason('');
        const updated = await api.getBlacklistedClients();
        setBlacklist(updated?.clients || []);
      } else {
        toast.error(res.message || 'Erro ao adicionar à lista negra.');
      }
    } catch {
      toast.error('Falha ao adicionar à lista negra.');
    } finally {
      setIsAddingBlacklist(false);
    }
  };

  const handleRemoveBlacklist = async (id: number) => {
    try {
      const res = await api.removeFromBlacklist(id);
      if (res.success) {
        toast.success('Cliente removido da lista negra.');
        setBlacklist((prev) => prev.filter((c) => c.id !== id));
      } else {
        toast.error(res.message || 'Erro ao remover cliente.');
      }
    } catch {
      toast.error('Falha ao remover cliente da lista negra.');
    }
  };

  if (isLoading) return <Loader type="overlay" message="Carregando configurações..." />;

  return (
    <div className={styles.pageContainer}>
      <CyberHeader
        title="CONFIGURAÇÕES DO SISTEMA"
        subtitle="PREFERÊNCIAS // PARÂMETROS"
        description="Configure suas credenciais, proteções anti-ban, lista negra e preferências de automação."
      />

      <div className={styles.settingsGrid}>
        {/* Sidebar Navigation */}
        <div className={styles.sidebar}>
          <button
            className={`${styles.navItem} ${activeTab === 'general' ? styles.active : ''}`}
            onClick={() => setActiveTab('general')}
          >
            <SettingsIcon size={18} className={styles.navIcon} />
            Geral & Visual
          </button>

          <button
            className={`${styles.navItem} ${activeTab === 'workana' ? styles.active : ''}`}
            onClick={() => setActiveTab('workana')}
          >
            <KeyRound size={18} className={styles.navIcon} />
            Conta Workana
          </button>

          <button
            className={`${styles.navItem} ${activeTab === 'automation' ? styles.active : ''}`}
            onClick={() => setActiveTab('automation')}
          >
            <Sliders size={18} className={styles.navIcon} />
            Automação & IA
          </button>

          <button
            className={`${styles.navItem} ${activeTab === 'antiban' ? styles.active : ''}`}
            onClick={() => setActiveTab('antiban')}
          >
            <Shield size={18} className={styles.navIcon} />
            Segurança & Anti-Ban
          </button>

          <button
            className={`${styles.navItem} ${activeTab === 'blacklist' ? styles.active : ''}`}
            onClick={() => setActiveTab('blacklist')}
          >
            <Ban size={18} className={styles.navIcon} />
            Lista Negra
          </button>

          <div style={{ flex: 1 }}></div>

          <button
            className={`${styles.navItem} ${activeTab === 'danger' ? styles.active : ''}`}
            onClick={() => setActiveTab('danger')}
            style={{ color: activeTab === 'danger' ? '#ef4444' : 'var(--color-text-muted)' }}
          >
            <AlertTriangle size={18} className={styles.navIcon} />
            Zona de Perigo
          </button>
        </div>

        {/* Content Area */}
        <div className={styles.contentArea}>
          {activeTab === 'general' && (
            <GeneralTab currentTheme={currentTheme} changeTheme={changeTheme} />
          )}

          {activeTab === 'workana' && (
            <WorkanaAccountTab
              credentials={credentials}
              newCredentials={newCredentials}
              setNewCredentials={setNewCredentials}
              showPassword={showPassword}
              setShowPassword={setShowPassword}
              isSaving={isSaving}
              handleSaveCredentials={handleSaveCredentials}
              handleGoogleLogin={handleGoogleLogin}
              isGoogleLogging={isGoogleLogging}
              importMode={importMode}
              setImportMode={setImportMode}
              sessionJson={sessionJson}
              setSessionJson={setSessionJson}
              accountEmail={accountEmail}
              setAccountEmail={setAccountEmail}
              isImporting={isImporting}
              handleImportSession={handleImportSession}
              handleFileUpload={handleFileUpload}
              handleDisconnect={handleDisconnect}
              setCredentials={setCredentials}
            />
          )}

          {activeTab === 'automation' && (
            <AutomationTab
              config={config}
              setConfig={setConfig}
              showApiKey={showApiKey}
              setShowApiKey={setShowApiKey}
              handleSaveConfig={handleSaveConfig}
              isSaving={isSaving}
            />
          )}

          {activeTab === 'antiban' && (
            <AntibanTab
              antibanStatus={antibanStatus}
              antibanConfig={antibanConfig}
              setAntibanConfig={setAntibanConfig}
              handleSaveAntibanConfig={handleSaveAntibanConfig}
              isSavingAntiban={isSavingAntiban}
              sessionHealth={sessionHealth}
              handleTestSessionHealth={handleTestSessionHealth}
              isCheckingHealth={isCheckingHealth}
            />
          )}

          {activeTab === 'blacklist' && (
            <BlacklistTab
              blacklist={blacklist}
              newClientName={newClientName}
              setNewClientName={setNewClientName}
              newClientReason={newClientReason}
              setNewClientReason={setNewClientReason}
              handleAddBlacklist={handleAddBlacklist}
              isAddingBlacklist={isAddingBlacklist}
              handleRemoveBlacklist={handleRemoveBlacklist}
            />
          )}

          {activeTab === 'danger' && (
            <DangerZoneTab
              onClearHistory={() => toast.info('Funcionalidade em desenvolvimento')}
              onResetFactory={() => toast.info('Funcionalidade em desenvolvimento')}
            />
          )}
        </div>
      </div>
    </div>
  );
}
