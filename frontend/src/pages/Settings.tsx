import { useState, useEffect } from "react";
import styles from "./Settings.module.css";
import { api, type CredentialsStatus, type AutomationConfig } from "../services/api";
import { useToast } from "../context/ToastContext";
import Loader from "../components/Loader";
import CyberHeader from "../components/CyberHeader";

type SettingsTab = 'general' | 'workana' | 'automation' | 'danger';

export default function Settings() {
    const { toast } = useToast();
    const [activeTab, setActiveTab] = useState<SettingsTab>('general');
    
    // Config States
    const [currentTheme, setCurrentTheme] = useState('default');
    const [credentials, setCredentials] = useState<CredentialsStatus>({ configured: false, email: null });
    const [newCredentials, setNewCredentials] = useState({ email: "", password: "" });
    const [config, setConfig] = useState<AutomationConfig>({
        headless: true,
        delay_between_actions_ms: 2000,
        max_proposals_per_day: 10,
        auto_apply: false,
        preferred_template_id: null,
        gemini_api_key: "",
        user_full_name: ""
    });

    // UI States
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);

    // Login via Google / Import de sessão
    const [isGoogleLogging, setIsGoogleLogging] = useState(false);
    const [importMode, setImportMode] = useState(false);
    const [sessionJson, setSessionJson] = useState("");
    const [accountEmail, setAccountEmail] = useState("");
    const [isImporting, setIsImporting] = useState(false);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const [credentialsStatus, automationConfig] = await Promise.all([
                    api.getCredentialsStatus(),
                    api.getAutomationConfig()
                ]);

                setCredentials(credentialsStatus);
                setConfig(prev => ({
                    ...prev,
                    ...automationConfig,
                    gemini_api_key: automationConfig.gemini_api_key || "",
                    user_full_name: automationConfig.user_full_name || ""
                }));
            } catch (error) {
                console.error("Failed to load settings:", error);
                toast.error("Erro ao carregar configurações.");
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
                setNewCredentials({ email: "", password: "" });
                toast.success("Credenciais salvas com sucesso!");
            } else {
                toast.error(response.message || "Erro ao salvar credenciais.");
            }
        } catch (error) {
            toast.error("Erro de conexão ao salvar credenciais.");
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
                user_full_name: config.user_full_name
            });
            
            if (response.success) {
                 toast.success("Configurações salvas com sucesso!");
            } else {
                 toast.error(response.message || "Erro ao salvar.");
            }
        } catch (error) {
            toast.error("Erro ao salvar configurações.");
        } finally {
            setIsSaving(false);
        }
    };

    const handleGoogleLogin = async () => {
        setIsGoogleLogging(true);
        try {
            const response: any = await api.googleLogin();
            if (response.success) {
                toast.success(response.email ? `Conectado como ${response.email}` : "Login via Google concluído!");
                await reloadCredentials();
            } else {
                toast.error(response.message || "Não foi possível abrir o login via Google.");
                if (response.message && (response.message.includes("Docker") || response.message.includes("XServer") || response.message.includes("headless") || response.message.includes("Importar"))) {
                    setImportMode(true);
                }
            }
        } catch (error: any) {
            toast.error(error.message || "Erro ao abrir o login via Google.");
            setImportMode(true);
        } finally {
            setIsGoogleLogging(false);
        }
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;
            if (content) {
                setSessionJson(content);
                toast.info(`Arquivo "${file.name}" carregado! Clique em "Importar Sessão" para salvar.`);
            }
        };
        reader.readAsText(file);
    };

    const handleImportSession = async () => {
        if (!sessionJson.trim()) {
            toast.error("Cole o JSON da sessão para importar.");
            return;
        }
        setIsImporting(true);
        try {
            const response: any = await api.importSession(sessionJson.trim(), accountEmail.trim() || undefined);
            if (response.success) {
                toast.success(response.message || "Sessão importada!");
                setSessionJson("");
                setImportMode(false);
                await reloadCredentials();
            } else {
                toast.error(response.message || "Erro ao importar a sessão.");
            }
        } catch (error: any) {
            toast.error(error.message || "Erro ao importar a sessão.");
        } finally {
            setIsImporting(false);
        }
    };

    const handleDisconnect = async () => {
        try {
            const response: any = await api.disconnectWorkana();
            if (response.success) {
                toast.success("Conexão com o Workana removida.");
                await reloadCredentials();
            } else {
                toast.error(response.message || "Erro ao desconectar.");
            }
        } catch (error: any) {
            toast.error(error.message || "Erro ao desconectar.");
        }
    };

    const reloadCredentials = async () => {
        try {
            const status = await api.getCredentialsStatus();
            setCredentials(status);
        } catch (error) {
            console.error("Failed to reload credentials:", error);
        }
    };

    if (isLoading) return <Loader type="overlay" message="Carregando configurações..." />;

    return (
        <div className={styles.pageContainer}>
            <CyberHeader 
                title="CONFIGURAÇÕES DO SISTEMA" 
                subtitle="PREFERÊNCIAS // PARÂMETROS" 
                description="Configure suas credenciais, chave da IA Gemini e preferências de automação."
            />

            <div className={styles.settingsGrid}>
                {/* Sidebar Navigation */}
                <div className={styles.sidebar}>
                    <button 
                        className={`${styles.navItem} ${activeTab === 'general' ? styles.active : ''}`}
                        onClick={() => setActiveTab('general')}
                    >
                        <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                        Geral & Visual
                    </button>

                    <button 
                        className={`${styles.navItem} ${activeTab === 'workana' ? styles.active : ''}`}
                        onClick={() => setActiveTab('workana')}
                    >
                        <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        Conta Workana
                    </button>

                    <button 
                        className={`${styles.navItem} ${activeTab === 'automation' ? styles.active : ''}`}
                        onClick={() => setActiveTab('automation')}
                    >
                        <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                        </svg>
                        Automação & IA
                    </button>

                    <div style={{ flex: 1 }}></div>

                    <button 
                        className={`${styles.navItem} ${activeTab === 'danger' ? styles.active : ''}`}
                        onClick={() => setActiveTab('danger')}
                        style={{ color: activeTab === 'danger' ? '#ef4444' : 'var(--color-text-muted)' }}
                    >
                        <svg className={styles.navIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                            <line x1="12" y1="9" x2="12" y2="13"></line>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        Zona de Perigo
                    </button>
                </div>

                {/* Content Area */}
                <div className={styles.contentArea}>
                    
                    {/* GENERAL TAB */}
                    {activeTab === 'general' && (
                        <div className={styles.animated}>
                            <h2 className={styles.sectionTitle}>Aparência</h2>
                            <p className={styles.sectionSubtitle}>Personalize o visual do seu painel</p>

                            <div className={styles.card}>
                                <div className={styles.themeGrid}>
                                    {['default', 'cyberpunk', 'minimal'].map(theme => (
                                        <div 
                                            key={theme}
                                            className={`${styles.themeBtn} ${currentTheme === theme ? styles.active : ''}`}
                                            onClick={() => changeTheme(theme)}
                                        >
                                            <div style={{ fontSize: '24px' }}>
                                                {theme === 'default' ? '🌙' : theme === 'cyberpunk' ? '👾' : '☀️'}
                                            </div>
                                            <span>{theme.charAt(0).toUpperCase() + theme.slice(1)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* WORKANA TAB */}
                    {activeTab === 'workana' && (
                        <div className={styles.animated}>
                            <h2 className={styles.sectionTitle}>Conexão Workana</h2>
                            <p className={styles.sectionSubtitle}>Gerencie o acesso à sua conta</p>

                            <div className={styles.card}>
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="text-lg font-bold">Status da Conexão</h3>
                                    {credentials.configured ? (
                                        <span className="badge badge-success">
                                            ● Conectado{credentials.login_method === 'google' ? ' via Google' : ''} {credentials.email ? `como ${credentials.email}` : ''}
                                        </span>
                                    ) : (
                                        <span className="badge badge-neutral">● Desconectado</span>
                                    )}
                                </div>

                                {credentials.login_method === 'google' && credentials.session_ready ? (
                                    <div className="text-center py-6">
                                        <div className="mb-3 text-5xl">🔐</div>
                                        <p className="mb-1">Sua sessão do navegador está salva e será usada para enviar propostas.</p>
                                        <p className="text-xs text-muted mb-4">O worker restaura os cookies localmente — não precisa de senha.</p>
                                        <div className="flex flex-wrap gap-3 justify-center">
                                            <button className="btn btn-secondary" onClick={handleGoogleLogin} disabled={isGoogleLogging}>
                                                {isGoogleLogging ? "Aguardando login no navegador..." : "Refazer Login Google"}
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
                                        <div style={{ padding: '16px', background: 'rgba(59, 130, 246, 0.05)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                                            <h4 className="text-base font-bold text-primary mb-2 flex items-center gap-2">
                                                <svg width="20" height="20" viewBox="0 0 24 24">
                                                    <path fill="#EA4335" d="M12 5.04c1.62 0 3.06.56 4.2 1.65l3.1-3.1C17.4 1.67 14.9.68 12 .68 7.36.68 3.36 3.3 1.55 7.11l3.62 2.8C6 7.17 8.77 5.04 12 5.04z"/>
                                                    <path fill="#4285F4" d="M23.32 12.28c0-.85-.08-1.48-.24-2.13H12v3.86h6.5c-.14.7-.84 1.74-2.42 2.44l3.54 2.74c2.11-1.95 3.7-4.82 3.7-6.91z"/>
                                                    <path fill="#FBBC05" d="M5.17 14.09a6.7 6.7 0 0 1-.35-2.09c0-.72.13-1.42.34-2.09l-3.62-2.8C.62 8.88 0 10.37 0 12s.63 3.12 1.54 4.89l3.63-2.8z"/>
                                                    <path fill="#34A853" d="M12 23.32c3.05 0 5.62-1 7.49-2.73l-3.54-2.74c-1.02.72-2.37 1.22-3.95 1.22-3.23 0-6-2.13-6.84-5.09l-3.63 2.8C3.36 20.7 7.36 23.32 12 23.32z"/>
                                                </svg>
                                                Login com Conta Google / Importar Sessão
                                            </h4>
                                            <p className="text-xs text-muted mb-3">
                                                Como o sistema roda dentro do Docker, o navegador para o login com Google deve ser aberto no Windows pelo script <strong>LOGIN-WORKANA.bat</strong>:
                                            </p>
                                            <ol className="text-xs text-muted space-y-1 pl-4 mb-4" style={{ listStyleType: 'decimal' }}>
                                                <li>Dê dois cliques no arquivo <strong><code>LOGIN-WORKANA.bat</code></strong> na pasta do projeto.</li>
                                                <li>Faça o login com sua conta Google na janela do Chrome que abrir.</li>
                                                <li>O script fechará o navegador e <strong>copiará a sessão para sua Área de Transferência</strong> automaticamente.</li>
                                                <li>Volte aqui, cole (<code>Ctrl + V</code>) ou clique em <em>Carregar Arquivo</em> e salve.</li>
                                            </ol>

                                            <div className="flex justify-between items-center mb-2">
                                                <label className={styles.label} style={{ margin: 0, fontWeight: 'bold' }}>
                                                    JSON da Sessão / Cookies
                                                </label>
                                                <label className="btn btn-secondary text-xs" style={{ cursor: 'pointer', margin: 0, padding: '4px 8px' }}>
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
                                                placeholder='Cole aqui a sessão com Ctrl + V...'
                                                value={sessionJson}
                                                onChange={e => setSessionJson(e.target.value)}
                                            />
                                            <div className={styles.formGroup} style={{ marginTop: '8px' }}>
                                                <label className={styles.label}>Email da conta Workana (opcional)</label>
                                                <input
                                                    type="email"
                                                    className={styles.input}
                                                    placeholder="seuemail@gmail.com"
                                                    value={accountEmail}
                                                    onChange={e => setAccountEmail(e.target.value)}
                                                />
                                            </div>
                                            <button
                                                className="btn btn-primary w-full mt-3"
                                                onClick={handleImportSession}
                                                disabled={isImporting || !sessionJson.trim()}
                                            >
                                                {isImporting ? "Importando..." : "Salvar e Conectar Sessão"}
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
                                                    onChange={e => setNewCredentials({...newCredentials, email: e.target.value})}
                                                />
                                            </div>
                                            <div className={styles.formGroup}>
                                                <label className={styles.label}>Senha</label>
                                                <div className="relative">
                                                    <input 
                                                        type={showPassword ? "text" : "password"} 
                                                        className={styles.input}
                                                        placeholder="••••••••"
                                                        value={newCredentials.password}
                                                        onChange={e => setNewCredentials({...newCredentials, password: e.target.value})}
                                                    />
                                                    <button 
                                                        type="button"
                                                        onClick={() => setShowPassword(!showPassword)}
                                                        style={{ position: 'absolute', right: '12px', top: '12px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
                                                    >
                                                        {showPassword ? "Ocultar" : "Mostrar"}
                                                    </button>
                                                </div>
                                            </div>
                                            <button 
                                                className="btn btn-primary w-full"
                                                onClick={handleSaveCredentials}
                                                disabled={!newCredentials.email || !newCredentials.password || isSaving}
                                            >
                                                {isSaving ? "Salvando..." : "Conectar Conta"}
                                            </button>
                                            <p className="text-xs text-muted mt-4 text-center">
                                                Suas credenciais são criptografadas e salvas apenas no seu dispositivo.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* AUTOMATION TAB */}
                    {activeTab === 'automation' && (
                        <div className={styles.animated}>
                            <h2 className={styles.sectionTitle}>Inteligência Artificial & Bots</h2>
                            <p className={styles.sectionSubtitle}>Configure como o sistema trabalha por você</p>

                            {/* Gemini Config */}
                            <div className={styles.card}>
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                    <span className="text-primary">✨</span> Google Gemini AI
                                </h3>
                                <div className={styles.formGroup}>
                                    <label className={styles.label}>API Key</label>
                                    <div className="relative">
                                        <input 
                                            type={showApiKey ? "text" : "password"} 
                                            className={styles.input}
                                            placeholder="Ex: AIzaSy..."
                                            value={config.gemini_api_key}
                                            onChange={e => setConfig({...config, gemini_api_key: e.target.value})}
                                        />
                                        <button 
                                            type="button"
                                            onClick={() => setShowApiKey(!showApiKey)}
                                            style={{ position: 'absolute', right: '12px', top: '12px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
                                        >
                                            {showApiKey ? "Ocultar" : "Mostrar"}
                                        </button>
                                    </div>
                                </div>
                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Nome na Assinatura</label>
                                    <input 
                                        type="text" 
                                        className={styles.input}
                                        placeholder="Ex: João Silva - Desenvolvedor Full Stack"
                                        value={config.user_full_name}
                                        onChange={e => setConfig({...config, user_full_name: e.target.value})}
                                    />
                                    <p className="text-xs text-muted mt-2">Este nome será usado para assinar as propostas geradas.</p>
                                </div>
                            </div>

                            {/* Bot Behavior */}
                            <div className={styles.card}>
                                <h3 className="text-lg font-bold mb-4">Comportamento do Robô</h3>
                                
                                <div className={styles.configItem}>
                                    <div className={styles.itemInfo}>
                                        <h4>Modo Fantasma (Headless)</h4>
                                        <p>O navegador roda invisível em segundo plano</p>
                                    </div>
                                    <input 
                                        type="checkbox" 
                                        checked={config.headless}
                                        onChange={e => setConfig({...config, headless: e.target.checked})}
                                        style={{ width: '20px', height: '20px' }}
                                    />
                                </div>

                                <div className={styles.configItem}>
                                    <div className={styles.itemInfo}>
                                        <h4>Velocidade Humana</h4>
                                        <p>Delay de {config.delay_between_actions_ms}ms entre ações</p>
                                    </div>
                                    <input 
                                        type="range" 
                                        min="500" 
                                        max="5000" 
                                        step="100"
                                        value={config.delay_between_actions_ms}
                                        onChange={e => setConfig({...config, delay_between_actions_ms: Number(e.target.value)})}
                                        style={{ width: '120px' }}
                                    />
                                </div>

                                <div className={styles.configItem}>
                                    <div className={styles.itemInfo}>
                                        <h4>Limite Diário</h4>
                                        <p>Máximo de {config.max_proposals_per_day} propostas por dia</p>
                                    </div>
                                    <input 
                                        type="range" 
                                        min="1" 
                                        max="50" 
                                        value={config.max_proposals_per_day}
                                        onChange={e => setConfig({...config, max_proposals_per_day: Number(e.target.value)})}
                                        style={{ width: '120px' }}
                                    />
                                </div>
                            </div>

                            <button 
                                className="btn btn-primary"
                                onClick={handleSaveConfig}
                                disabled={isSaving}
                            >
                                {isSaving ? "Salvando..." : "Salvar Todas Configurações"}
                            </button>
                        </div>
                    )}

                    {/* DANGER TAB */}
                    {activeTab === 'danger' && (
                        <div className={styles.animated}>
                            <h2 className={styles.sectionTitle} style={{ color: '#ef4444' }}>Zona de Perigo</h2>
                            <p className={styles.sectionSubtitle}>Cuidado: Ações irreversíveis</p>

                            <div className={`${styles.card} ${styles.dangerZone}`}>
                                <div className={styles.configItem}>
                                    <div className={styles.itemInfo}>
                                        <h4>Limpar Histórico de Propostas</h4>
                                        <p>Apaga permanentemente o registro de propostas enviadas.</p>
                                    </div>
                                    <button className={styles.dangerBtn} onClick={() => toast.info('Funcionalidade em desenvolvimento')}>
                                        Limpar Tudo
                                    </button>
                                </div>

                                <div className={styles.configItem}>
                                    <div className={styles.itemInfo}>
                                        <h4>Resetar Aplicação</h4>
                                        <p>Restaura todas as configurações para o padrão de fábrica.</p>
                                    </div>
                                    <button className={styles.dangerBtn} onClick={() => toast.info('Funcionalidade em desenvolvimento')}>
                                        Resetar Fábrica
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
