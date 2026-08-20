import React, { useState, useEffect, useRef } from 'react';

interface Log {
    id: number;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
    timestamp: string;
}

const OPERATIONAL_LOGS = [
    { message: "AUTH_SERVICE: Sessão do usuário autenticada via Supabase", type: 'success' as const },
    { message: "PROPOSAL_ENGINE: Template de proposta compilado com sucesso", type: 'success' as const },
    { message: "SCRAPE_COORDINATOR: Sincronização periódica de catálogo executada", type: 'info' as const },
    { message: "MATCH_SCORER: Cálculo de compatibilidade de perfil concluído", type: 'info' as const },
    { message: "CATALOG_SYNC: Novas oportunidades importadas do Workana", type: 'success' as const },
    { message: "CLIENT_ANALYSIS: Histórico de contratações do cliente validado", type: 'success' as const },
    { message: "SKILL_MATCHER: Mapeamento de competências técnicas concluído", type: 'info' as const },
    { message: "WORKANA_API_PULSE: Latência de resposta da API normal", type: 'info' as const },
    { message: "BROWSER_RUNNER: Instância de automação iniciada com sucesso", type: 'info' as const },
    { message: "PROPOSAL_DISPATCHER: Proposta processada e pronta para envio", type: 'success' as const },
    { message: "SESSION_MANAGER: Sincronizando estado persistente com banco de dados", type: 'info' as const },
    { message: "METRICS_CALCULATOR: Estatísticas do painel atualizadas", type: 'success' as const },
    { message: "WORKER_HEARTBEAT: Heartbeat de processo registrado em /tmp", type: 'info' as const },
    { message: "AI_GENERATOR: Contexto profissional injetado no modelo Gemini", type: 'info' as const },
    { message: "NOTIFICATION_SERVICE: Verificação de alertas de novos projetos", type: 'info' as const },
    { message: "SYSTEM_READY: Workana Accelerator v2.0 operacional", type: 'success' as const },
    { message: "LEAD_SCORING: Oportunidade com alta compatibilidade identificada", type: 'success' as const },
    { message: "PROFILE_SYNC: Métricas do perfil sincronizadas", type: 'info' as const },
    { message: "JOB_FILTER: Filtros de exclusão aplicados na busca", type: 'success' as const }
];

// --- Optimized Log Item Component ---
const LogItem = React.memo(({ log, color }: { log: Log, color: string }) => (
    <div style={{ display: 'flex', gap: '8px', opacity: 0.9 }}>
        <span style={{ color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>[{log.timestamp}]</span>
        <span style={{ color }}>{log.message}</span>
    </div>
));

export default function SystemLog() {
    const [logs, setLogs] = useState<Log[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);
    const logCounter = useRef(0);

    // Optimized Local auto-scroll without affecting parent
    useEffect(() => {
        if (containerRef.current) {
            const container = containerRef.current;
            requestAnimationFrame(() => {
                container.scrollTop = container.scrollHeight;
            });
        }
    }, [logs]);

    // Initial and continuous log simulation
    useEffect(() => {
        const createLog = (data: { message: string, type: any }) => {
            logCounter.current += 1;
            const newLog: Log = {
                id: Date.now() + logCounter.current, // Stable and unique
                message: data.message,
                type: data.type,
                timestamp: new Date().toLocaleTimeString('pt-BR', { hour12: false })
            };
            setLogs(prev => {
                const next = [...prev, newLog];
                return next.length > 50 ? next.slice(-50) : next;
            });
        };

        // Add initial batch faster
        OPERATIONAL_LOGS.slice(0, 5).forEach((log, i) => {
            setTimeout(() => createLog(log), i * 150);
        });

        // Continuous loop every 3s
        const interval = setInterval(() => {
            const randomIndex = Math.floor(Math.random() * OPERATIONAL_LOGS.length);
            createLog(OPERATIONAL_LOGS[randomIndex]);
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'success': return 'var(--color-success)';
            case 'warning': return 'var(--color-warning)';
            case 'error': return 'var(--color-error)';
            default: return 'var(--color-text-secondary)';
        }
    };

    return (
        <div className="system-log-container" style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            contain: 'content', // Performance: isolates layout and paint
        }}>
            <div style={{ 
                borderBottom: '1px solid var(--color-border)', 
                paddingBottom: '4px', 
                marginBottom: '8px',
                color: 'var(--color-text-muted)',
                fontWeight: 'bold',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                <span>&gt;_ ATIVIDADE DO SISTEMA</span>
                <span style={{ fontSize: '0.65rem', opacity: 0.6 }}>ONLINE</span>
            </div>
            
            <div 
                ref={containerRef}
                style={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '4px', 
                    overflowY: 'auto',
                    flex: 1,
                    paddingRight: '8px',
                    scrollbarWidth: 'thin',
                    scrollbarColor: 'var(--color-primary) transparent',
                    willChange: 'scroll-position' // Optimization hint for browsers
                }}
                className="custom-scrollbar"
            >
                {logs.map((log) => (
                    <LogItem key={log.id} log={log} color={getTypeColor(log.type)} />
                ))}
            </div>
        </div>
    );
}

