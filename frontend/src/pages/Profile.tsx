import { useState, useEffect } from "react";
import styles from "./Profile.module.css";
import { api } from "../services/api";
import Loader from "../components/Loader";
import CyberHeader from "../components/CyberHeader";

interface ProfileMetrics {
    success: boolean;
    profile_url: string | null;
    username: string | null;
    display_name: string | null;
    projects_completed: number;
    projects_in_progress: number;
    hours_worked: number;
    average_rating: number | null;
    total_reviews: number;
    member_since: string | null;
    country: string | null;
    hourly_rate: string | null;
    skills: string[];
    last_login: string | null;
    profile_photo_url?: string | null;
    last_sync: string | null;
    is_configured: boolean;
    error: string | null;
}

export default function Profile() {
    const [profileMetrics, setProfileMetrics] = useState<ProfileMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        setIsLoading(true);
        try {
            const data = await api.getProfileMetrics();
            setProfileMetrics(data);
            setError(null);
        } catch (err) {
            console.error("Erro ao carregar perfil:", err);
            setError("Não foi possível carregar as métricas do perfil.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            const data = await api.syncProfileMetrics(true);
            setProfileMetrics(data);
            setError(null);
        } catch (err) {
            console.error("Erro ao sincronizar perfil:", err);
            setError("Falha na sincronização com o Workana.");
        } finally {
            setIsSyncing(false);
        }
    };

    // New Profile Input State
    const [newProfileUrl, setNewProfileUrl] = useState("");
    const [isValidatingProfile, setIsValidatingProfile] = useState(false);
    const [isSavingProfile, setIsSavingProfile] = useState(false);
    const [profileValidation, setProfileValidation] = useState<{ valid: boolean; display_name?: string; error?: string } | null>(null);
    const [isChangingProfile, setIsChangingProfile] = useState(false);

    const handleValidateProfileUrl = async () => {
        if (!newProfileUrl) return;
        setIsValidatingProfile(true);
        setProfileValidation(null);
        try {
            const result = await api.validateProfileUrl(newProfileUrl);
            setProfileValidation(result);
        } catch (error: any) {
            setProfileValidation({ valid: false, error: error.message });
        } finally {
            setIsValidatingProfile(false);
        }
    };

    const handleSaveAndSearch = async () => {
        setIsSavingProfile(true);
        setError(null);
        try {
            // 1. Update config
            await api.updateProfileConfig({
                profile_url: newProfileUrl,
                auto_sync_enabled: true,
                sync_interval_hours: 6
            });
            
            // 2. Sync immediately
            setIsLoading(true); // Show main loader
            const data = await api.syncProfileMetrics(false);
            setProfileMetrics(data);
            setIsChangingProfile(false);
            setNewProfileUrl("");
            setProfileValidation(null);
        } catch (err: any) {
            console.error("Erro ao salvar/buscar perfil:", err);
            setError(err.message || "Erro ao configurar e buscar perfil.");
        } finally {
            setIsSavingProfile(false);
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return <Loader type="overlay" message="Carregando perfil..." />;
    }

    // Render Profile Input Form if not configured OR if user wants to change it
    if (!profileMetrics?.is_configured || isChangingProfile) {
        return (
            <div className="container py-8">
                <div className={`m3-card ${styles.notConfigured}`} style={{ maxWidth: '600px', margin: '0 auto' }}>
                    <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                        <div style={{ 
                            width: '64px', height: '64px', margin: '0 auto 1rem', 
                            background: 'var(--color-primary-light)', borderRadius: '50%', 
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: 'var(--color-primary)'
                        }}>
                            <svg width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <circle cx="12" cy="7" r="4" />
                                <path d="M5.5 21a8.38 8.38 0 0 1 13 0" />
                            </svg>
                        </div>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem' }}>Analisador de Perfil Workana</h2>
                        <p style={{ color: 'var(--color-text-secondary)' }}>
                            Cole a URL de um perfil público do Workana para visualizar métricas e histórico profissional.
                        </p>
                    </div>

                    <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                        <label className="form-label">URL do Perfil Público</label>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <input
                                type="url"
                                className="form-input"
                                placeholder="https://www.workana.com/freelancer/seu-username"
                                value={newProfileUrl}
                                onChange={(e) => {
                                    setNewProfileUrl(e.target.value);
                                    setProfileValidation(null);
                                }}
                                style={{ flex: 1 }}
                            />
                            <button
                                className="btn btn-secondary"
                                onClick={handleValidateProfileUrl}
                                disabled={!newProfileUrl || isValidatingProfile}
                            >
                                {isValidatingProfile ? (
                                    <span className="spinner spinner-sm"></span>
                                ) : (
                                    "Verificar"
                                )}
                            </button>
                        </div>
                    </div>

                    {profileValidation && (
                        <div className={`alert ${profileValidation.valid ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: '1.5rem' }}>
                             {profileValidation.valid ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5" /></svg>
                                    <span>Perfil encontrado: <strong>{profileValidation.display_name}</strong></span>
                                </div>
                            ) : (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                                    <span>{profileValidation.error || "URL inválida"}</span>
                                </div>
                            )}
                        </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                        {isChangingProfile && profileMetrics?.is_configured && (
                            <button 
                                className="btn btn-ghost"
                                onClick={() => setIsChangingProfile(false)}
                            >
                                Cancelar
                            </button>
                        )}
                        <button
                            className="btn btn-primary"
                            onClick={handleSaveAndSearch}
                            disabled={!newProfileUrl || isSavingProfile || (profileValidation ? !profileValidation.valid : false)}
                            style={{ width: isChangingProfile ? 'auto' : '100%' }}
                        >
                            {isSavingProfile ? (
                                <>
                                    <span className="spinner spinner-sm"></span>
                                    {isChangingProfile ? "Salvando..." : "Analisar Perfil"}
                                </>
                            ) : (
                                isChangingProfile ? "Salvar Novo Perfil" : "Analisar Perfil"
                            )}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.profilePage}>
            <div style={{ marginBottom: '2rem' }}>
                <CyberHeader 
                    title="OPERATIVE PROFILE" 
                    subtitle="PERSONNEL_FILE // CLASSIFIED"
                    description="Visualize e gerencie suas métricas públicas."
                />
            </div>
            
            <div className="page-header" style={{ display: 'none' }}></div>

            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'center' }}>
                 <div style={{ 
                        width: '100%',
                        maxWidth: '600px', 
                        // ... search bar styles
                        background: 'var(--color-surface)',
                        border: '1px solid var(--color-border)',
                        borderRadius: '12px',
                        padding: '0.5rem',
                        display: 'flex',
                        gap: '0.5rem',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}>
                        <input
                            type="url"
                            placeholder="Pesquisar/Alterar perfil Workana..."
                            value={newProfileUrl}
                            onChange={(e) => {
                                setNewProfileUrl(e.target.value);
                                setProfileValidation(null);
                            }}
                            style={{ 
                                flex: 1, 
                                border: 'none', 
                                background: 'transparent', 
                                outline: 'none',
                                padding: '0.5rem',
                                fontSize: '0.95rem',
                                color: 'var(--color-text)'
                            }}
                        />
                        <button
                            className="btn btn-primary btn-sm"
                            onClick={() => {
                                if (profileValidation?.valid) {
                                    handleSaveAndSearch();
                                } else {
                                    handleValidateProfileUrl();
                                }
                            }}
                            disabled={!newProfileUrl || isValidatingProfile || isSavingProfile}
                        >
                            {(isValidatingProfile || isSavingProfile) ? (
                                <span className="spinner spinner-sm"></span>
                            ) : (
                                profileValidation?.valid ? 'Analisar' : 'Buscar'
                            )}
                        </button>
                    </div>
            </div>

            <div className={styles.profileLayout}>
                {/* Lado Esquerdo: Resumo e Foto */}
                <div className={styles.sidebarSection}>
                    <div className={`m3-card ${styles.mainCard}`}>
                        <div className={styles.syncOverlay}>
                           <button 
                                className={`btn btn-primary ${styles.syncBtn}`}
                                onClick={handleSync}
                                disabled={isSyncing}
                            >
                                {isSyncing ? 'Sincronizando...' : 'Sincronizar Agora'}
                            </button>
                        </div>
                        
                        <div className={styles.photoContainer}>
                            {profileMetrics.profile_photo_url ? (
                                <img src={profileMetrics.profile_photo_url} alt={profileMetrics.display_name || ''} />
                            ) : (
                                <div className={styles.photoFallback}>
                                    {profileMetrics.display_name?.charAt(0) || 'U'}
                                </div>
                            )}
                        </div>

                        <div className={styles.basicInfo}>
                            <h2>{profileMetrics.display_name}</h2>
                            <div className={styles.badges}>
                                {profileMetrics.hourly_rate && (
                                    <span className={styles.hourlyRateBadge}>
                                        💰 {profileMetrics.hourly_rate}
                                    </span>
                                )}
                            </div>
                            <div className={styles.locationGroup}>
                                {profileMetrics.country && <span>📍 {profileMetrics.country}</span>}
                                {profileMetrics.member_since && <span>🕒 Membro {profileMetrics.member_since}</span>}
                            </div>
                            {profileMetrics.profile_url && (
                                <div style={{ marginTop: '1rem' }}>
                                    <a href={profileMetrics.profile_url} target="_blank" rel="noopener noreferrer" className={styles.viewLink}>
                                        Ver Perfil Público ↗
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className={`m3-card ${styles.statusCard}`}>
                        <h4>Status de Atividade</h4>
                        <div className={styles.statusItem}>
                            <span className={styles.statusValue}>{profileMetrics.last_login}</span>
                            <span className={styles.statusLabel}>Último Login</span>
                        </div>
                        <div className={styles.statusItem}>
                            <span className={styles.statusValue}>
                                {profileMetrics.last_sync ? new Date(profileMetrics.last_sync).toLocaleString('pt-BR') : 'Nunca'}
                            </span>
                            <span className={styles.statusLabel}>Última Sincronização</span>
                        </div>
                    </div>
                </div>

                {/* Lado Direito: Métricas e Skills */}
                <div className={styles.mainContent}>
                    <div className={styles.statsGrid}>
                        <div className={`m3-card ${styles.statBox}`}>
                            <span className={styles.statIcon}>⭐</span>
                            <span className={styles.statLarge}>{profileMetrics.average_rating?.toFixed(2) || '0.00'}</span>
                            <span className={styles.statLabel}>{profileMetrics.total_reviews} Avaliações</span>
                        </div>
                        <div className={`m3-card ${styles.statBox}`}>
                            <span className={styles.statIcon}>✅</span>
                            <span className={styles.statLarge}>{profileMetrics.projects_completed}</span>
                            <span className={styles.statLabel}>Projetos Realizados</span>
                        </div>
                        <div className={`m3-card ${styles.statBox}`}>
                            <span className={styles.statIcon}>🔄</span>
                            <span className={styles.statLarge}>{profileMetrics.projects_in_progress}</span>
                            <span className={styles.statLabel}>Em Andamento</span>
                        </div>
                        <div className={`m3-card ${styles.statBox}`}>
                            <span className={styles.statIcon}>⏱️</span>
                            <span className={styles.statLarge}>{profileMetrics.hours_worked}</span>
                            <span className={styles.statLabel}>Horas Trabalhadas</span>
                        </div>
                    </div>

                    {profileMetrics.skills && profileMetrics.skills.length > 0 && (
                        <div className={`m3-card ${styles.skillsCard}`}>
                            <h3>Habilidades e Expertises</h3>
                            <div className={styles.skillsContainer}>
                                {profileMetrics.skills.map((skill, idx) => (
                                    <span key={idx} className={styles.skillTag}>{skill}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
