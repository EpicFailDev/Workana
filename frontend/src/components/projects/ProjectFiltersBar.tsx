import React from 'react';
import styles from '../../pages/Projects.module.css';
import { WORKANA_CATEGORIES } from '../../constants/categories';
import {
  PUBLICATION_OPTIONS,
  LANGUAGE_OPTIONS,
  SCRAPING_PAGES_OPTIONS,
} from '../../constants/options';

export interface SearchFilters {
  keywords: string;
  category: string;
  min_budget: string;
  max_budget: string;
  project_type: string;
  sort: string;
  publication: string;
  language: string;
  proposals: string;
  payment_verified: boolean;
  pages_to_fetch: number;
  favorites_only: boolean;
  hidden_only: boolean;
}

interface ProjectFiltersBarProps {
  filters: SearchFilters;
  isSearching: boolean;
  isSyncing: boolean;
  showAdvanced: boolean;
  onFiltersChange: (newFilters: SearchFilters) => void;
  onToggleAdvanced: () => void;
  onSearch: () => void;
  onSyncLive: () => void;
}

export const ProjectFiltersBar: React.FC<ProjectFiltersBarProps> = ({
  filters,
  isSearching,
  isSyncing,
  showAdvanced,
  onFiltersChange,
  onToggleAdvanced,
  onSearch,
  onSyncLive,
}) => {
  return (
    <div className={styles.controlDeck}>
      <div className={styles.searchRow}>
        <div style={{ flex: 1, position: 'relative' }}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{
              position: 'absolute',
              left: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--color-text-muted)',
            }}
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className={styles.controlInput}
            style={{ paddingLeft: '48px' }}
            placeholder="Buscar palavras-chave (ex: React, Python)..."
            value={filters.keywords}
            onChange={(e) => onFiltersChange({ ...filters, keywords: e.target.value })}
            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
          />
        </div>
        <button
          type="button"
          className="btn btn-primary"
          style={{ minWidth: '120px' }}
          onClick={onSearch}
          disabled={isSearching || isSyncing}
          title="Busca empregos salvos no banco de dados"
        >
          {isSearching ? <span className="spinner spinner-sm"></span> : 'BUSCAR'}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ minWidth: '135px', gap: '8px' }}
          onClick={onSyncLive}
          disabled={isSearching || isSyncing}
          title="Busca projetos diretamente no Workana e salva/atualiza o banco de dados"
        >
          {isSyncing ? (
            <>
              <span className="spinner spinner-sm"></span>
              <span>SCANEANDO...</span>
            </>
          ) : (
            <>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ marginRight: '4px' }}
              >
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              <span>SCANEAR</span>
            </>
          )}
        </button>
        <button
          type="button"
          className={`btn ${showAdvanced ? 'btn-secondary' : 'btn-ghost'}`}
          onClick={onToggleAdvanced}
          style={{ border: '1px solid var(--color-border)' }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ marginRight: '8px' }}
          >
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
          </svg>
          {showAdvanced ? 'Ocultar Filtros' : 'Filtros Avançados'}
        </button>
      </div>

      <div className={`${styles.filterGrid} ${showAdvanced ? styles.expanded : ''}`}>
        <div className="form-group">
          <label className="form-label">Categoria</label>
          <select
            className={styles.controlInput}
            value={filters.category}
            onChange={(e) => onFiltersChange({ ...filters, category: e.target.value })}
          >
            <option value="">Todas as categorias</option>
            {WORKANA_CATEGORIES.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Orçamento (Mín - Máx)</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="number"
              className={styles.controlInput}
              placeholder="Min"
              value={filters.min_budget}
              onChange={(e) => onFiltersChange({ ...filters, min_budget: e.target.value })}
            />
            <input
              type="number"
              className={styles.controlInput}
              placeholder="Max"
              value={filters.max_budget}
              onChange={(e) => onFiltersChange({ ...filters, max_budget: e.target.value })}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Publicação</label>
          <select
            className={styles.controlInput}
            value={filters.publication}
            onChange={(e) => onFiltersChange({ ...filters, publication: e.target.value })}
          >
            {PUBLICATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Idioma</label>
          <select
            className={styles.controlInput}
            value={filters.language}
            onChange={(e) => onFiltersChange({ ...filters, language: e.target.value })}
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Quick Filters Row */}
        <div
          style={{
            gridColumn: '1 / -1',
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
            marginTop: '8px',
            borderTop: '1px solid rgba(255,255,255,0.05)',
            paddingTop: '16px',
          }}
        >
          <label
            className="checkbox-container"
            style={{ background: 'transparent', border: 'none', padding: 0 }}
          >
            <input
              type="checkbox"
              checked={filters.payment_verified}
              onChange={(e) => onFiltersChange({ ...filters, payment_verified: e.target.checked })}
            />
            <span className="checkbox-label" style={{ color: 'var(--color-text-secondary)' }}>
              Pagamento Verificado
            </span>
          </label>
          <label
            className="checkbox-container"
            style={{ background: 'transparent', border: 'none', padding: 0 }}
          >
            <input
              type="checkbox"
              checked={filters.favorites_only}
              onChange={(e) => onFiltersChange({ ...filters, favorites_only: e.target.checked })}
            />
            <span className="checkbox-label" style={{ color: 'var(--color-text-secondary)' }}>
              Favoritos
            </span>
          </label>
          <label
            className="checkbox-container"
            style={{ background: 'transparent', border: 'none', padding: 0 }}
          >
            <input
              type="checkbox"
              checked={filters.hidden_only}
              onChange={(e) => onFiltersChange({ ...filters, hidden_only: e.target.checked })}
            />
            <span className="checkbox-label" style={{ color: 'var(--color-text-secondary)' }}>
              Ocultos
            </span>
          </label>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="text-sm text-muted">Páginas de Scraping:</span>
            <select
              className={styles.controlInput}
              style={{ width: 'auto', minWidth: '135px', padding: '4px 8px' }}
              value={filters.pages_to_fetch}
              onChange={(e) =>
                onFiltersChange({ ...filters, pages_to_fetch: Number(e.target.value) })
              }
              title="Quantidade de páginas do Workana a serem pesquisadas no scraping"
            >
              {SCRAPING_PAGES_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
