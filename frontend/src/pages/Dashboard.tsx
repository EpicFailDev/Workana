import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import styles from "./Dashboard.module.css";
import { api } from "../services/api";
import Loader from "../components/Loader";
import ActivityChart from "../components/ActivityChart";
import { useToast } from "../context/ToastContext";
import CyberHeader from "../components/CyberHeader";
import SystemLog from "../components/SystemLog";
import { useCounter } from "../hooks/useCounter";

// --- Gamification Helper ---
const calculateNextLevelXp = (level: number) => Math.pow(level, 2) * 100;

import RankBadge from "../components/RankBadge";

const DAILY_MISSIONS = [
    { id: 1, title: 'Postar 5 Propostas', target: 5, current: 2, xp: 50, icon: '📝' },
    { id: 2, title: 'Pesquisar Projetos', target: 1, current: 1, xp: 20, icon: '🔍' },
    { id: 3, title: 'Manter Streak (3 dias)', target: 1, current: 1, xp: 100, icon: '🔥' },
];

// Garante que a URL base sempre termine com /api
const rawBaseUrl = import.meta.env.VITE_API_URL || "";
const API_BASE = rawBaseUrl 
    ? (rawBaseUrl.endsWith("/api") ? rawBaseUrl : `${rawBaseUrl}/api`)
    : "/api";

interface DashboardStats {
    total_proposals_sent: number;
    proposals_today: number;
    proposals_this_week: number;
    proposals_this_month: number;
    response_rate: number;
    accepted_proposals: number;
    pending_proposals: number;
    last_activity: string | null;
    active_projects?: number;
    earnings_simulated?: number;
    success_rate?: number;
    xp: number;
    lp: number;
    rank_tier: string;
    rank_division: string;
}

interface AutomationStatus {
    is_running: boolean;
    current_action: string | null;
    proposals_sent_today: number;
    max_proposals_per_day: number;
    last_error: string | null;
}

export default function Dashboard() {
    const { toast } = useToast();
    // Temporary mock until AuthContext is fully implemented
    const user = { name: 'Comandante' };
    
    // Gamification State (Now from API)
    const [xp, setXp] = useState(0); 
    const [lp, setLp] = useState(0);
    const [rankTier, setRankTier] = useState("Ferro");
    const [rankDivision, setRankDivision] = useState("IV");

    // Stats / Metrics State
    const [metrics, setMetrics] = useState<DashboardStats>({
        total_proposals_sent: 0,
        proposals_today: 0,
        proposals_this_week: 0,
        proposals_this_month: 0,
        response_rate: 0,
        accepted_proposals: 0,
        pending_proposals: 0,
        last_activity: null,
        active_projects: 3, 
        earnings_simulated: 1250, 
        success_rate: 15,
        xp: 0,
        lp: 0,
        rank_tier: 'Ferro',
        rank_division: 'IV'
    });

    const [automationStatus, setAutomationStatus] = useState<AutomationStatus>({
        is_running: false,
        current_action: null,
        proposals_sent_today: 0,
        max_proposals_per_day: 10,
        last_error: null,
    });

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Animated Counters
    const animatedTotalProposals = useCounter(metrics.total_proposals_sent);
    const animatedActiveProjects = useCounter(metrics.active_projects || 0);
    const animatedResponseRate = useCounter(metrics.response_rate);
    const animatedEarnings = useCounter(metrics.earnings_simulated || 0);
    const animatedXp = useCounter(xp);
    const animatedLp = useCounter(lp);

    useEffect(() => {
        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchDashboardData = async () => {
        try {
            const statusData = await api.getAutomationStatus();
            setAutomationStatus(statusData);

            const statsData = await api.getDashboardStats();
            setMetrics(prev => ({
                ...prev,
                ...statsData,
                active_projects: prev.active_projects,
                earnings_simulated: prev.earnings_simulated,
                success_rate: statsData.response_rate || prev.success_rate
            }));
            
            // Update Rank State
            setXp(statsData.xp);
            setLp(statsData.lp);
            setRankTier(statsData.rank_tier);
            setRankDivision(statsData.rank_division);

            setError(null);
        } catch (err: any) {
            if (isLoading) {
                 setError(`Não foi possível conectar ao backend (${API_BASE}).`);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const levelProgress = lp; // Use LP for progress bar directly (0-100)
    const progressPercent = Math.max(0, Math.min(100, levelProgress)); 

    if (isLoading) {
        return <Loader type="overlay" message="Sincronizando seu dashboard..." />;
    }

    return (
        <div className={styles.container}>
            <CyberHeader 
                title="MISSION CONTROL" 
                subtitle="SYSTEM_READY // INITIATE_SEARCH"
                description={`Bem-vindo de volta, Agente ${user?.name || 'Guest'}. Identifique e capture as melhores oportunidades do mercado.`}
            />

            {/* --- COMMAND CENTER (GAMIFICATION) --- */}
            <div className={styles.commandCenter}>
                {/* Profile & Level Card */}
                <div className={`${styles.profileCard} holo-card`}>
                    <div className={styles.avatarContainer}>
                        <div className={styles.avatar} /> 
                    </div>
                    
                    <RankBadge 
                        tier={rankTier} 
                        division={rankDivision} 
                        lp={animatedLp}
                        size="md"
                    />

                    <div className={styles.xpContainer} style={{ marginTop: '1rem' }}>
                        <div className={styles.xpHeader}>
                            <span>Total XP: {animatedXp}</span>
                            <span>PDL para Promo: 100</span>
                        </div>
                        <div className={styles.xpTrack}>
                            <div className={styles.xpFill} style={{ width: `${progressPercent}%` }}></div>
                        </div>
                    </div>
                    
                    <button className="btn btn-outline btn-sm w-full" style={{ marginTop: 'auto' }}>
                        Ver Perfil Completo
                    </button>
                </div>

                {/* Daily Missions & Quick Stats */}
                <div className={`${styles.missionsCard} holo-card`}>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>🎯</span> Objetivos do Dia
                    </h3>
                    
                    <div className={styles.missionList}>
                        {DAILY_MISSIONS.map(mission => (
                            <div key={mission.id} className={`${styles.missionItem} ${mission.current >= mission.target ? styles.completed : ''}`}>
                                <div className={styles.missionIcon}>{mission.icon}</div>
                                <div className={styles.missionInfo}>
                                    <div className={styles.missionTitle}>{mission.title}</div>
                                    <div className={styles.missionProgress}>
                                        Progresso: {mission.current} / {mission.target}
                                    </div>
                                </div>
                                {mission.current >= mission.target ? (
                                    <div className={styles.xpReward} style={{ background: 'var(--color-success)', color: 'white' }}>COMPLETO</div>
                                ) : (
                                    <div className={styles.xpReward}>+{mission.xp} XP</div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Standard Metrics Grid */}
            <div className={styles.grid}>
                <div className={`${styles.card} holo-card`}>
                    <div className={styles.cardIcon}>📊</div>
                    <div className="stat-value-big">{animatedTotalProposals}</div>
                    <div className={styles.cardLabel}>Propostas Enviadas</div>
                </div>
                
                <div className={`${styles.card} holo-card`}>
                    <div className={styles.cardIcon}>⚡</div>
                    <div className="stat-value-big">{animatedActiveProjects}</div>
                    <div className={styles.cardLabel}>Projetos Ativos</div>
                </div>
                
                <div className={`${styles.card} holo-card`}>
                    <div className={styles.cardIcon}>🎯</div>
                    <div className="stat-value-big">{animatedResponseRate}%</div>
                    <div className={styles.cardLabel}>Taxa de Resposta</div>
                </div>
                
                <div className={`${styles.card} holo-card`}>
                    <div className={styles.cardIcon}>💰</div>
                    <div className="stat-value-big">R$ {animatedEarnings}</div>
                    <div className={styles.cardLabel}>Ganhos Estimados</div>
                </div>
            </div>

            <div className={styles.chartSection} style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 'var(--spacing-lg)', marginTop: 'var(--spacing-lg)' }}>
                <div className="holo-card" style={{ padding: 'var(--spacing-lg)', height: '320px' }}>
                    <h2 className={styles.chartTitle}>Atividade Recente</h2>
                    <ActivityChart 
                        data={[4, 7, 5, 2, 8, 8, metrics.proposals_today || 0]} 
                        labels={['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Hoje']}
                        height={180}
                    />
                </div>
                
                <div className="holo-card" style={{ padding: 'var(--spacing-lg)', height: '320px' }}>
                    <SystemLog />
                </div>
            </div>

            {/* --- AUTOMATION STATUS & QUICK ACTIONS GRID --- */}
            <div className={styles.grid} style={{ marginBottom: 'var(--spacing-xl)', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', marginTop: 'var(--spacing-lg)' }}>
                <div className={`${styles.consoleCard} holo-card`}>
                    <div className={styles.consoleContent}>
                        <div className={styles.consoleSection}>
                            <div className={`${styles.statusDot} ${automationStatus.is_running ? styles.online : styles.offline}`}></div>
                            <div className={styles.consoleInfo}>
                                <span className={styles.consoleLabel}>Estado Operacional</span>
                                <span className={styles.consoleValue}>
                                    {automationStatus.is_running ? 'SISTEMAS ONLINE' : 'EM ESPERA'}
                                </span>
                            </div>
                        </div>

                        <div className={styles.consoleSection}>
                             {automationStatus.current_action ? (
                                <div className={styles.consoleInfo}>
                                    <span className={styles.consoleLabel}>Atividade Atual</span>
                                    <span className={styles.consoleValue} style={{ fontSize: '0.9rem', color: 'var(--color-primary)' }}>
                                        {automationStatus.current_action}
                                    </span>
                                </div>
                             ) : (
                                <div className={styles.consoleInfo}>
                                    <span className={styles.consoleLabel}>Capacidade Diária</span>
                                    <span className={styles.consoleValue}>
                                    {automationStatus.proposals_sent_today} <span style={{ opacity: 0.4 }}>/ {automationStatus.max_proposals_per_day}</span>
                                    </span>
                                </div>
                             )}
                        </div>

                        <div className={styles.consoleAction}>
                             <Link to="/projects" className="btn btn-primary btn-sm" style={{ padding: '8px 24px', fontWeight: 600 }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '8px' }}>
                                    <path d="M5 12h14" />
                                    <path d="M12 5l7 7-7 7" />
                                </svg>
                                Iniciar Busca
                            </Link>
                        </div>
                    </div>

                    <div className={styles.consoleProgress}>
                        <div 
                            className={styles.consoleProgressFill}
                            style={{ width: `${(automationStatus.proposals_sent_today / automationStatus.max_proposals_per_day) * 100}%` }}
                        />
                    </div>
                </div>

                {error && (
                    <div className={styles.errorBanner}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        <span>{error}</span>
                        <button onClick={() => setError(null)} className="btn btn-ghost btn-sm">✕</button>
                    </div>
                )}
            </div>

            {/* Quick Actions */}
            <div className={`holo-card ${styles.quickActions}`} style={{ padding: 'var(--spacing-lg)' }}>
                <h3 className="card-title">Ações Rápidas</h3>
                <div className={styles.actionsGrid}>
                    <Link to="/projects" className={styles.actionCard}>
                        <div className={styles.actionIcon} style={{ background: 'var(--gradient-primary)' }}>
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                        </div>
                        <div className={styles.actionText}>
                            <h4>Buscar Projetos</h4>
                            <p>Encontre novos projetos</p>
                        </div>
                    </Link>

                    <Link to="/templates" className={styles.actionCard}>
                        <div className={styles.actionIcon} style={{ background: 'var(--gradient-secondary)' }}>
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="16" y1="13" x2="8" y2="13" />
                                <line x1="16" y1="17" x2="8" y2="17" />
                                <polyline points="10 9 9 9 8 9" />
                            </svg>
                        </div>
                        <div className={styles.actionText}>
                            <h4>Propostas Inteligentes</h4>
                            <p>Gerencie suas propostas geradas</p>
                        </div>
                    </Link>

                    <Link to="/history" className={styles.actionCard}>
                        <div className={styles.actionIcon} style={{ background: 'var(--gradient-success)' }}>
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 8v4l3 3" />
                                <circle cx="12" cy="12" r="10" />
                            </svg>
                        </div>
                        <div className={styles.actionText}>
                            <h4>Histórico</h4>
                            <p>Veja atividades recentes</p>
                        </div>
                    </Link>

                    <Link to="/settings" className={styles.actionCard}>
                        <div className={styles.actionIcon} style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="3" />
                                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                                </svg>
                        </div>
                        <div className={styles.actionText}>
                            <h4>Configurações</h4>
                            <p>Ajuste suas preferências</p>
                        </div>
                    </Link>
                </div>
            </div>
        </div>
    );
}
