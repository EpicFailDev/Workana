import { useState, useEffect } from "react";
import styles from "./Settings.module.css";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import Loader from "../components/Loader";
import CyberHeader from "../components/CyberHeader";

interface CredentialsStatus {
    configured: boolean;
    email: string | null;
}

interface AutomationConfig {
    headless: boolean;
    delay_between_actions_ms: number;
    max_proposals_per_day: number;
    auto_apply: boolean;
    gemini_api_key?: string;
    user_full_name?: string;
}

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
        gemini_api_key: "",
        user_full_name: ""
    });

    // UI States
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showApiKey, setShowApiKey] = useState(false);

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

    if (isLoading) return <Loader type="overlay" message="Carregando configurações..." />;

    return (
        <div className={styles.pageContainer}>
            <CyberHeader 
                title="SYSTEM CONFIG" 
                subtitle="OPERATIONAL_PARAMETERS // SETUP"
                description="Personalize sua experiência no Workana Accelerator."
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
                                        <span className="badge badge-success">● Conectado como {credentials.email}</span>
                                    ) : (
                                        <span className="badge badge-neutral">● Desconectado</span>
                                    )}
                                </div>

                                {!credentials.configured ? (
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
                                ) : (
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
