import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  FolderSearch,
  Layers,
  FileText,
  User,
  History,
  Settings,
  Calculator,
  Shield,
  RefreshCw,
  Download,
  Ban,
  ArrowRight,
} from 'lucide-react';
import styles from './CommandPalette.module.css';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenCalculator: () => void;
  onOpenHealth: () => void;
  onRefreshCatalog: () => void;
  onDownloadCsv: () => void;
}

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  category: 'Navegação' | 'Ações do Sistema';
  icon: React.ReactNode;
  action: () => void;
  shortcut?: string;
}

export default function CommandPalette({
  isOpen,
  onClose,
  onOpenCalculator,
  onOpenHealth,
  onRefreshCatalog,
  onDownloadCsv,
}: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = [
    {
      id: 'nav-dashboard',
      title: 'Dashboard',
      subtitle: 'Visão geral e métricas de desempenho',
      category: 'Navegação',
      icon: <LayoutDashboard size={18} />,
      action: () => navigate('/'),
      shortcut: 'G D',
    },
    {
      id: 'nav-projects',
      title: 'Projetos do Catálogo',
      subtitle: 'Buscar oportunidades e gerar propostas',
      category: 'Navegação',
      icon: <FolderSearch size={18} />,
      action: () => navigate('/projects'),
      shortcut: 'G P',
    },
    {
      id: 'nav-batches',
      title: 'Lotes de Propostas',
      subtitle: 'Fila de disparo em massa e rascunhos',
      category: 'Navegação',
      icon: <Layers size={18} />,
      action: () => navigate('/batches'),
      shortcut: 'G B',
    },
    {
      id: 'nav-templates',
      title: 'Modelos de Proposta',
      subtitle: 'Editor visual de blocos e blueprints com IA',
      category: 'Navegação',
      icon: <FileText size={18} />,
      action: () => navigate('/templates'),
      shortcut: 'G T',
    },
    {
      id: 'nav-profile',
      title: 'Meu Perfil Workana',
      subtitle: 'Métricas públicas, reputação e ganhos',
      category: 'Navegação',
      icon: <User size={18} />,
      action: () => navigate('/profile'),
      shortcut: 'G U',
    },
    {
      id: 'nav-history',
      title: 'Histórico & Kanban',
      subtitle: 'Status de propostas enviadas e visualizadas',
      category: 'Navegação',
      icon: <History size={18} />,
      action: () => navigate('/history'),
      shortcut: 'G H',
    },
    {
      id: 'nav-settings',
      title: 'Configurações',
      subtitle: 'Credenciais, parâmetros de automação e temas',
      category: 'Navegação',
      icon: <Settings size={18} />,
      action: () => navigate('/settings'),
      shortcut: 'G S',
    },
    {
      id: 'action-refresh',
      title: 'Sincronizar Catálogo Agora',
      subtitle: 'Coletar novas oportunidades do Workana',
      category: 'Ações do Sistema',
      icon: <RefreshCw size={18} />,
      action: onRefreshCatalog,
    },
    {
      id: 'action-calc',
      title: 'Calculadora de Investimento MVP',
      subtitle: 'Decomposição em 4 etapas para propostas',
      category: 'Ações do Sistema',
      icon: <Calculator size={18} />,
      action: onOpenCalculator,
    },
    {
      id: 'action-health',
      title: 'Verificar Saúde do Sistema',
      subtitle: 'Diagnóstico de cookies, anti-ban e gateways',
      category: 'Ações do Sistema',
      icon: <Shield size={18} />,
      action: onOpenHealth,
    },
    {
      id: 'action-blacklist',
      title: 'Gerenciar Lista Negra de Clientes',
      subtitle: 'Bloquear clientes indesejados ou abusivos',
      category: 'Ações do Sistema',
      icon: <Ban size={18} />,
      action: () => navigate('/settings?tab=blacklist'),
    },
    {
      id: 'action-csv',
      title: 'Exportar Catálogo em CSV',
      subtitle: 'Download sanitizado com compatibilidade Excel',
      category: 'Ações do Sistema',
      icon: <Download size={18} />,
      action: onDownloadCsv,
    },
  ];

  const filtered = commands.filter((cmd) => {
    const q = query.toLowerCase().trim();
    return (
      cmd.title.toLowerCase().includes(q) ||
      (cmd.subtitle && cmd.subtitle.toLowerCase().includes(q)) ||
      cmd.category.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        onClose();
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.palette} onClick={(e) => e.stopPropagation()}>
        <div className={styles.searchHeader}>
          <Search size={18} className={styles.searchIcon} />
          <input
            ref={inputRef}
            type="text"
            className={styles.searchInput}
            placeholder="O que você deseja fazer? Digite um comando ou página..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
          />
          <span className={styles.kbdHint}>ESC para sair</span>
        </div>

        <div className={styles.resultsList}>
          {filtered.length === 0 ? (
            <div className={styles.emptyState}>
              Nenhum comando ou página encontrado para "{query}".
            </div>
          ) : (
            filtered.map((cmd, idx) => (
              <div
                key={cmd.id}
                className={`${styles.item} ${idx === selectedIndex ? styles.itemSelected : ''}`}
                onClick={() => {
                  cmd.action();
                  onClose();
                }}
                onMouseEnter={() => setSelectedIndex(idx)}
              >
                <div className={styles.itemLeft}>
                  <div className={styles.itemIcon}>{cmd.icon}</div>
                  <div className={styles.itemText}>
                    <span className={styles.itemTitle}>{cmd.title}</span>
                    {cmd.subtitle && <span className={styles.itemSubtitle}>{cmd.subtitle}</span>}
                  </div>
                </div>
                {cmd.shortcut ? (
                  <span className={styles.itemTag}>{cmd.shortcut}</span>
                ) : (
                  <ArrowRight size={14} style={{ opacity: 0.4 }} />
                )}
              </div>
            ))
          )}
        </div>

        <div className={styles.footer}>
          <div className={styles.footerShortcuts}>
            <span className={styles.shortcutItem}>
              <kbd className={styles.kbdHint}>↑</kbd>
              <kbd className={styles.kbdHint}>↓</kbd> navegar
            </span>
            <span className={styles.shortcutItem}>
              <kbd className={styles.kbdHint}>↵</kbd> selecionar
            </span>
            <span className={styles.shortcutItem}>
              <kbd className={styles.kbdHint}>Esc</kbd> fechar
            </span>
          </div>
          <span>Workana Accelerator Quick Switcher</span>
        </div>
      </div>
    </div>
  );
}
