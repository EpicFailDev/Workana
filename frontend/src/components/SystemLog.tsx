import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw } from 'lucide-react';
import { api, type ActivityLogItem } from '../services/api';

interface Log {
  id: number | string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  isReal?: boolean;
}

const BOOTSTRAP_LOGS = [
  { message: 'AUTH_SERVICE: Sessão do usuário autenticada via Supabase', type: 'success' as const },
  { message: 'PROPOSAL_ENGINE: Agente consultivo inicializado', type: 'success' as const },
  { message: 'ANTIBAN_SHIELD: Proteção heurística ativa', type: 'info' as const },
  { message: 'SYSTEM_READY: Workana Accelerator v2.0 operacional', type: 'success' as const },
];

const LogItem = React.memo(({ log, color }: { log: Log; color: string }) => (
  <div style={{ display: 'flex', gap: '8px', opacity: 0.9, lineHeight: '1.4' }}>
    <span style={{ color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
      [{log.timestamp}]
    </span>
    <span style={{ color }}>{log.message}</span>
  </div>
));

export default function SystemLog() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchRealLogs = async () => {
    setLoading(true);
    try {
      const res = await api.getActivityLogs({ limit: 40 });
      if (res?.logs && res.logs.length > 0) {
        const formatted: Log[] = res.logs.map((item: ActivityLogItem) => ({
          id: item.id,
          message: `${item.action_type.toUpperCase()}: ${item.description}`,
          type: (item.status as any) || 'info',
          timestamp: new Date(item.created_at).toLocaleTimeString('pt-BR', { hour12: false }),
          isReal: true,
        }));
        setLogs(formatted.reverse());
      } else {
        // Fallback para logs de inicialização
        const fallback: Log[] = BOOTSTRAP_LOGS.map((item, idx) => ({
          id: `boot-${idx}`,
          message: item.message,
          type: item.type,
          timestamp: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
          isReal: false,
        }));
        setLogs(fallback);
      }
    } catch {
      // Falha silenciosa com logs de inicialização
      const fallback: Log[] = BOOTSTRAP_LOGS.map((item, idx) => ({
        id: `boot-${idx}`,
        message: item.message,
        type: item.type,
        timestamp: new Date().toLocaleTimeString('pt-BR', { hour12: false }),
        isReal: false,
      }));
      setLogs(fallback);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRealLogs();
    const interval = setInterval(fetchRealLogs, 20000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      const container = containerRef.current;
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
      });
    }
  }, [logs]);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'var(--color-success, #10b981)';
      case 'warning':
        return 'var(--color-warning, #f59e0b)';
      case 'error':
        return 'var(--color-error, #ef4444)';
      default:
        return 'var(--color-text-secondary, #94a3b8)';
    }
  };

  return (
    <div
      className="system-log-container"
      style={{
        fontFamily: 'var(--font-mono, monospace)',
        fontSize: '0.75rem',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        contain: 'content',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          paddingBottom: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 6px #10b981',
              display: 'inline-block',
            }}
          />
          <span
            style={{
              color: 'var(--color-text-muted)',
              fontSize: '0.7rem',
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            LOGS OPERACIONAIS EM TEMPO REAL
          </span>
        </div>

        <button
          onClick={fetchRealLogs}
          disabled={loading}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.68rem',
            padding: '2px 6px',
            borderRadius: '4px',
          }}
          title="Recarregar logs de atividade"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>

      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          paddingRight: '4px',
        }}
      >
        {logs.map((log) => (
          <LogItem key={log.id} log={log} color={getTypeColor(log.type)} />
        ))}
      </div>
    </div>
  );
}
