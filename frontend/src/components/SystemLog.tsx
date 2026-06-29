import React, { useState, useEffect, useRef } from 'react';

interface Log {
    id: number;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
    timestamp: string;
}

const HACKER_LOGS = [
    { message: "WORKANA_AUTH_BYPASS: Simulando handshake TLS em workana.com", type: 'warning' },
    { message: "PROPOSAL_ENGINE: Gerando hash SHA-256 para proposta #88219", type: 'success' },
    { message: "SCRAPE_COORDINATOR: Rotacionando user-agent para evitar detecção", type: 'info' },
    { message: "BID_WAR_PROTOCOL: Ajustando lances competitivos em tempo real", type: 'warning' },
    { message: "PROJECT_FETCH_QUEUE: 12 novas oportunidades em /pt/jobs", type: 'success' },
    { message: "CLIENT_DNA_ANALYSIS: Analisando histórico de pagamentos... [OK]", type: 'success' },
    { message: "SKILL_OVERRIDE: Forçando match para competências 'React+Node'", type: 'info' },
    { message: "WORKANA_API_PULSE: Latência detectada em nodes/sa-east-1", type: 'error' },
    { message: "STEALTH_CRAWLER: Mimetizando padrões de rolagem humana", type: 'info' },
    { message: "AUTO_BID_DAEMON: Proposta enviada para 'Projeto de E-commerce'", type: 'success' },
    { message: "COOKIE_INJECTION: Sincronizando sessão persistente com backend", type: 'warning' },
    { message: "PROFIT_MAXIMIZER: ROI estimado de 14.5% para este bid", type: 'success' },
    { message: "FREELANCER_RANK_SPOOF: Simulando status TOP_RATED", type: 'warning' },
    { message: "PAYMENT_GATEWAY_PING: Verificando disponibilidade de saque", type: 'info' },
    { message: "VULNERABILITY_SCAN: Porta 443 aberta na CDN da Workana", type: 'error' },
    { message: "MESSAGE_BOT: Automatizando follow-up para lead pendente", type: 'success' },
    { message: "BID_LIMIT_BREACH: Tentando burlar limite de 2 propostas/hora", type: 'error' },
    { message: "AI_PROPOSAL_GEN: Injetando contexto de especialista em TI", type: 'info' },
    { message: "NETWORK_TUNNEL: Roteando tráfego via proxy residenciais", type: 'info' },
    { message: "SYSTEM_READY: Workana Accelerator v2.0 carregado", type: 'success' },
    { message: "LEAD_SCORING: Identificado cliente com potencial high-ticket", type: 'success' },
    { message: "AVATAR_SYNC: Atualizando imagem de perfil via IPFS", type: 'info' },
    { message: "DEADLINE_WATCHER: Monitorando expiração de propostas ativas", type: 'warning' },
    { message: "W_GATEKEEPER_BYPASS: Transpondo o Cloudflare CAPTCHA...", type: 'info' },
    { message: "JOB_FILTER_HEURISTICS: Removendo spam da fila de busca", type: 'success' }
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
        HACKER_LOGS.slice(0, 5).forEach((log, i) => {
            setTimeout(() => createLog(log), i * 150);
        });

        // Continuous loop every 3s
        const interval = setInterval(() => {
            const randomIndex = Math.floor(Math.random() * HACKER_LOGS.length);
            createLog(HACKER_LOGS[randomIndex]);
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
                <span>&gt;_ SYSTEM_LOGS</span>
                <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>TERMINAL_ACTIVE</span>
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

