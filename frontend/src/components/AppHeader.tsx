import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Menu,
  ChevronRight,
  RefreshCw,
  Calculator,
  Search,
  LogOut,
  User,
  ShieldCheck,
  AlertCircle,
  LayoutDashboard,
  FolderSearch,
  Layers,
  FileText,
  History,
  Settings,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api, type SessionHealthResponse, type AntibanStatus } from '../services/api';
import styles from './AppHeader.module.css';

interface AppHeaderProps {
  onToggleSidebar: () => void;
  onOpenSearch: () => void;
  onOpenCalculator: () => void;
  onOpenHealth: () => void;
  onRefreshCatalog: () => void;
  isSyncingCatalog?: boolean;
}

const ROUTE_INFO: Record<string, { label: string; icon: React.ReactNode }> = {
  '/': { label: 'Dashboard', icon: <LayoutDashboard size={14} /> },
  '/projects': { label: 'Projetos do Catálogo', icon: <FolderSearch size={14} /> },
  '/batches': { label: 'Lotes de Propostas', icon: <Layers size={14} /> },
  '/templates': { label: 'Modelos de Proposta', icon: <FileText size={14} /> },
  '/profile': { label: 'Meu Perfil', icon: <User size={14} /> },
  '/history': { label: 'Histórico & Kanban', icon: <History size={14} /> },
  '/settings': { label: 'Configurações', icon: <Settings size={14} /> },
};

export default function AppHeader({
  onToggleSidebar,
  onOpenSearch,
  onOpenCalculator,
  onOpenHealth,
  onRefreshCatalog,
  isSyncingCatalog = false,
}: AppHeaderProps) {
  const location = useLocation();
  const { user, signOut } = useAuth();
  const [sessionHealth, setSessionHealth] = useState<SessionHealthResponse | null>(null);
  const [antiban, setAntiban] = useState<AntibanStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [healthRes, antibanRes] = await Promise.allSettled([
          api.getSessionHealth(),
          api.getAntibanStatus(),
        ]);
        if (healthRes.status === 'fulfilled') setSessionHealth(healthRes.value);
        if (antibanRes.status === 'fulfilled') setAntiban(antibanRes.value);
      } catch {
        // Silencioso em polling de header
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 45000);
    return () => clearInterval(interval);
  }, []);

  const routeInfo = ROUTE_INFO[location.pathname] || {
    label: 'Visão Geral',
    icon: <LayoutDashboard size={14} />,
  };

  const isWarning = sessionHealth && sessionHealth.status !== 'healthy';
  const isError =
    sessionHealth &&
    (sessionHealth.status === 'expired' || sessionHealth.status === 'disconnected');

  let pillClass = styles.statusPill;
  let pillText = 'Sistema Pronto';
  if (isError) {
    pillClass = `${styles.statusPill} ${styles.statusPillError}`;
    pillText = 'Sessão Offline';
  } else if (isWarning || antiban?.in_cooldown) {
    pillClass = `${styles.statusPill} ${styles.statusPillWarning}`;
    pillText = antiban?.in_cooldown ? 'Anti-Ban Cooldown' : 'Verificar Sessão';
  }

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'U';

  return (
    <header className={styles.header}>
      {/* Lado Esquerdo: Hamburger + Breadcrumb */}
      <div className={styles.leftSection}>
        <button
          className={styles.toggleBtn}
          onClick={onToggleSidebar}
          aria-label="Alternar Menu Lateral"
          title="Alternar Menu Lateral"
        >
          <Menu size={18} />
        </button>

        <nav className={styles.breadcrumb} aria-label="Navegação Estrutural">
          <Link to="/" className={styles.breadcrumbHome} title="Início">
            Workana
          </Link>
          <ChevronRight size={14} className={styles.breadcrumbSeparator} />
          <span className={styles.breadcrumbCurrent}>
            {routeInfo.icon}
            {routeInfo.label}
          </span>
        </nav>
      </div>

      {/* Lado Direito: Ações Globais + Status + Usuário */}
      <div className={styles.rightSection}>
        {/* Pílula de Status / Telemetria */}
        <button
          className={pillClass}
          onClick={onOpenHealth}
          title="Clique para ver o diagnóstico completo dos serviços"
        >
          <span className={styles.pulseDot} />
          <span>{pillText}</span>
        </button>

        {/* Botão de Busca Rápida (Ctrl+K) */}
        <button
          className={styles.searchBtn}
          onClick={onOpenSearch}
          title="Busca rápida e comandos (Ctrl+K)"
        >
          <Search size={15} />
          <span>Buscar</span>
          <kbd className={styles.kbdPill}>Ctrl+K</kbd>
        </button>

        {/* Botão Calculadora de Investimento */}
        <button
          className={styles.actionBtn}
          onClick={onOpenCalculator}
          title="Calculadora de Investimento MVP"
        >
          <Calculator size={15} />
          <span>Investimento</span>
        </button>

        {/* Botão Sincronizar Catálogo */}
        <button
          className={styles.actionBtn}
          onClick={onRefreshCatalog}
          disabled={isSyncingCatalog}
          title="Sincronizar catálogo com o Workana"
        >
          <RefreshCw size={15} className={isSyncingCatalog ? 'animate-spin' : ''} />
          <span>{isSyncingCatalog ? 'Sincronizando...' : 'Catálogo'}</span>
        </button>

        {/* Avatar e Perfil */}
        <div className={styles.userMenu}>
          <Link to="/profile" className={styles.userBtn} title="Ver Meu Perfil">
            <div className={styles.avatar}>{userInitial}</div>
            <span className={styles.userEmail}>{user?.email?.split('@')[0] || 'Usuário'}</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
