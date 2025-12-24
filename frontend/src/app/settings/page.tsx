"use client";

import { useState } from "react";
import styles from "./page.module.css";

interface CredentialsStatus {
    configured: boolean;
    email: string | null;
}

interface AutomationConfig {
    headless: boolean;
    delay_between_actions_ms: number;
    max_proposals_per_day: number;
    auto_apply: boolean;
}

export default function SettingsPage() {
    const [credentials, setCredentials] = useState<CredentialsStatus>({
        configured: false,
        email: null,
    });

    const [newCredentials, setNewCredentials] = useState({
        email: "",
        password: "",
    });

    const [config, setConfig] = useState<AutomationConfig>({
        headless: true,
        delay_between_actions_ms: 2000,
        max_proposals_per_day: 10,
        auto_apply: false,
    });

    const [isSaving, setIsSaving] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSaveCredentials = async () => {
        setIsSaving(true);
        try {
            // Simular salvamento
            await new Promise(resolve => setTimeout(resolve, 1000));
            setCredentials({
                configured: true,
                email: newCredentials.email.substring(0, 3) + "***" + newCredentials.email.substring(newCredentials.email.indexOf("@")),
            });
            setNewCredentials({ email: "", password: "" });
        } catch (error) {
            console.error("Erro ao salvar:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveConfig = async () => {
        setIsSaving(true);
        try {
            await new Promise(resolve => setTimeout(resolve, 500));
            // TODO: Chamar API real
        } catch (error) {
            console.error("Erro:", error);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className="page-header">
                <h1 className="page-title">
                    <span className="text-gradient">Configurações</span>
                </h1>
                <p className="page-subtitle">
                    Configure suas credenciais e preferências de automação
                </p>
            </div>

            {/* Credenciais */}
            <div className={`card ${styles.section}`}>
                <div className="card-header">
                    <div>
                        <h3 className="card-title">Credenciais do Workana</h3>
                        <p className={styles.sectionDescription}>
                            Suas credenciais são armazenadas localmente com criptografia
                        </p>
                    </div>
                    {credentials.configured && (
                        <span className="badge badge-success">
                            <span className="status-dot online"></span>
                            Configurado
                        </span>
                    )}
                </div>

                {credentials.configured ? (
                    <div className={styles.credentialsInfo}>
                        <div className={styles.infoRow}>
                            <span className={styles.infoLabel}>Email:</span>
                            <span className={styles.infoValue}>{credentials.email}</span>
                        </div>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setCredentials({ configured: false, email: null })}
                        >
                            Alterar Credenciais
                        </button>
                    </div>
                ) : (
                    <div className={styles.credentialsForm}>
                        <div className="form-group">
                            <label className="form-label">Email do Workana</label>
                            <input
                                type="email"
                                className="form-input"
                                placeholder="seu@email.com"
                                value={newCredentials.email}
                                onChange={(e) => setNewCredentials({ ...newCredentials, email: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Senha</label>
                            <div className={styles.passwordField}>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    className="form-input"
                                    placeholder="••••••••"
                                    value={newCredentials.password}
                                    onChange={(e) => setNewCredentials({ ...newCredentials, password: e.target.value })}
                                />
                                <button
                                    type="button"
                                    className={styles.passwordToggle}
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? (
                                        <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                                            <line x1="1" y1="1" x2="23" y2="23" />
                                        </svg>
                                    ) : (
                                        <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        <div className={styles.warningBox}>
                            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                <line x1="12" y1="9" x2="12" y2="13" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg>
                            <p>Suas credenciais são armazenadas apenas no seu computador e nunca são enviadas para servidores externos.</p>
                        </div>

                        <button
                            className="btn btn-primary"
                            onClick={handleSaveCredentials}
                            disabled={!newCredentials.email || !newCredentials.password || isSaving}
                        >
                            {isSaving ? (
                                <>
                                    <span className="spinner"></span>
                                    Salvando...
                                </>
                            ) : (
                                "Salvar Credenciais"
                            )}
                        </button>
                    </div>
                )}
            </div>

            {/* Configurações de Automação */}
            <div className={`card ${styles.section}`}>
                <div className="card-header">
                    <div>
                        <h3 className="card-title">Configurações de Automação</h3>
                        <p className={styles.sectionDescription}>
                            Ajuste o comportamento da automação para evitar detecção
                        </p>
                    </div>
                </div>

                <div className={styles.configGrid}>
                    <div className={styles.configItem}>
                        <div className={styles.configInfo}>
                            <h4>Modo Invisível (Headless)</h4>
                            <p>Executar o navegador em segundo plano sem janela visível</p>
                        </div>
                        <label className={styles.toggle}>
                            <input
                                type="checkbox"
                                checked={config.headless}
                                onChange={(e) => setConfig({ ...config, headless: e.target.checked })}
                            />
                            <span className={styles.toggleSlider}></span>
                        </label>
                    </div>

                    <div className={styles.configItem}>
                        <div className={styles.configInfo}>
                            <h4>Delay Entre Ações</h4>
                            <p>Tempo de espera entre ações para simular comportamento humano</p>
                        </div>
                        <div className={styles.rangeContainer}>
                            <input
                                type="range"
                                className={styles.rangeInput}
                                min="500"
                                max="5000"
                                step="100"
                                value={config.delay_between_actions_ms}
                                onChange={(e) => setConfig({ ...config, delay_between_actions_ms: Number(e.target.value) })}
                            />
                            <span className={styles.rangeValue}>{config.delay_between_actions_ms}ms</span>
                        </div>
                    </div>

                    <div className={styles.configItem}>
                        <div className={styles.configInfo}>
                            <h4>Limite Diário de Propostas</h4>
                            <p>Número máximo de propostas a enviar por dia</p>
                        </div>
                        <div className={styles.rangeContainer}>
                            <input
                                type="range"
                                className={styles.rangeInput}
                                min="1"
                                max="30"
                                step="1"
                                value={config.max_proposals_per_day}
                                onChange={(e) => setConfig({ ...config, max_proposals_per_day: Number(e.target.value) })}
                            />
                            <span className={styles.rangeValue}>{config.max_proposals_per_day}</span>
                        </div>
                    </div>

                    <div className={styles.configItem}>
                        <div className={styles.configInfo}>
                            <h4>Aplicação Automática</h4>
                            <p>Enviar propostas automaticamente para projetos que correspondam aos filtros</p>
                        </div>
                        <label className={styles.toggle}>
                            <input
                                type="checkbox"
                                checked={config.auto_apply}
                                onChange={(e) => setConfig({ ...config, auto_apply: e.target.checked })}
                            />
                            <span className={styles.toggleSlider}></span>
                        </label>
                    </div>
                </div>

                <div className={styles.configActions}>
                    <button className="btn btn-primary" onClick={handleSaveConfig}>
                        Salvar Configurações
                    </button>
                </div>
            </div>

            {/* Aviso de Segurança */}
            <div className={`card ${styles.dangerZone}`}>
                <h3 className="card-title" style={{ color: 'var(--color-error)' }}>
                    ⚠️ Zona de Perigo
                </h3>
                <p className={styles.sectionDescription}>
                    Ações irreversíveis que afetam seus dados
                </p>

                <div className={styles.dangerActions}>
                    <div className={styles.dangerItem}>
                        <div>
                            <h4>Limpar Histórico</h4>
                            <p>Remove todo o histórico de propostas enviadas</p>
                        </div>
                        <button className="btn btn-danger btn-sm">Limpar</button>
                    </div>

                    <div className={styles.dangerItem}>
                        <div>
                            <h4>Resetar Tudo</h4>
                            <p>Remove todas as configurações, credenciais e dados</p>
                        </div>
                        <button className="btn btn-danger btn-sm">Resetar</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
