import React from 'react';
import { AnalysisResult } from '../../services/api';
import styles from '../../pages/Projects.module.css';

const CONTRACT_LABELS: Record<string, string> = {
  project_fixed: 'Preço Fixo',
  project_hourly: 'Por Hora',
  unknown: 'Não Especificado',
};

export interface ProjectCardItem {
  id: string;
  title: string;
  description: string;
  budget: string | null;
  skills: string[];
  contract_type?: string | null;
  posted_at: string | null;
  proposals_count: number | null;
  proposals_delta?: number | null;
  url: string;
  analysis?: AnalysisResult | null;
}

interface ProjectCardProps {
  project: ProjectCardItem;
  index: number;
  isSelected: boolean;
  isBatchSelected: boolean;
  matchScore: number;
  isNew: boolean;
  analysis: AnalysisResult | null;
  onSelectProject: (project: ProjectCardItem) => void;
  onToggleBatchSelection: (projectId: string) => void;
  onOpenBidsHistory: (project: ProjectCardItem) => void;
  onGenerateAiProposal: (projectId: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  index,
  isSelected,
  isBatchSelected,
  matchScore,
  isNew,
  analysis,
  onSelectProject,
  onToggleBatchSelection,
  onOpenBidsHistory,
  onGenerateAiProposal,
}) => {
  const recommendation = analysis?.recommendation;
  const badgeClass =
    recommendation === 'send'
      ? 'badge-success'
      : recommendation === 'review'
        ? 'badge-warning'
        : recommendation === 'discard'
          ? 'badge-error'
          : 'badge-info';

  const formatDelta = (delta?: number | null) => {
    if (!delta || delta === 0) return null;
    return delta > 0 ? `+${delta}` : `${delta}`;
  };

  return (
    <div
      className={`${styles.holoCard} ${isSelected ? styles.active : ''} ${isBatchSelected ? styles.batchSelected : ''} reveal-item`}
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className={`${styles.cornerMarker} ${styles.cornerTL}`}></div>
      <div className={`${styles.cornerMarker} ${styles.cornerTR}`}></div>
      <div className={`${styles.cornerMarker} ${styles.cornerBL}`}></div>
      <div className={`${styles.cornerMarker} ${styles.cornerBR}`}></div>

      {isNew && <div className={styles.newBadge}>NOVO</div>}

      <div className={styles.cardHeader} onClick={() => onSelectProject(project)}>
        <label
          className="checkbox-container"
          style={{ background: 'transparent', border: 'none', padding: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={isBatchSelected}
            onChange={() => onToggleBatchSelection(project.id)}
            aria-label={`Selecionar ${project.title}`}
          />
        </label>
        <h3 className={styles.cardTitle} title="Clique para ver Detalhes">
          {project.title}
        </h3>
        {analysis && (
          <span className={`badge ${badgeClass}`} title={analysis.justification}>
            {Math.round(analysis.score)} • {recommendation}
          </span>
        )}
        <div className={styles.rewardBadge}>{project.budget || 'A Combinar'}</div>
      </div>

      <div className={styles.cardBody} onClick={() => onSelectProject(project)}>
        <div className={styles.techStack}>
          {project.skills.slice(0, 4).map((skill) => (
            <span key={skill} className={styles.techTag}>
              {skill}
            </span>
          ))}
          {project.skills.length > 4 && (
            <span className={styles.techTag}>+{project.skills.length - 4}</span>
          )}
        </div>
        <p className={styles.description}>{project.description}</p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            Compatibilidade: {matchScore}%
          </span>
          <div className={styles.matchIndicator}>
            <div
              className={styles.matchBar}
              style={{
                width: `${matchScore}%`,
                background:
                  matchScore > 80
                    ? 'var(--gradient-success)'
                    : matchScore > 50
                      ? 'var(--color-warning)'
                      : 'var(--color-error)',
              }}
            ></div>
          </div>
        </div>
      </div>

      <div className={styles.cardFooter}>
        <div className={styles.metaInfo}>
          {project.contract_type && (
            <span className={styles.contractBadge}>
              {CONTRACT_LABELS[project.contract_type] || project.contract_type}
            </span>
          )}
          <div className={styles.metaItem}>
            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {project.posted_at}
          </div>
        </div>
        <button
          type="button"
          className={styles.proposalCount}
          title="Ver histórico de propostas"
          onClick={(e) => {
            e.stopPropagation();
            onOpenBidsHistory(project);
          }}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <span>{project.proposals_count ?? 0} propostas</span>
          {formatDelta(project.proposals_delta) && (
            <span
              className={styles.deltaChip}
              style={{
                color: (project.proposals_delta ?? 0) > 0 ? '#6ee7b7' : '#fca5a5',
                background:
                  (project.proposals_delta ?? 0) > 0
                    ? 'rgba(16,185,129,0.12)'
                    : 'rgba(239,68,68,0.12)',
              }}
            >
              {formatDelta(project.proposals_delta)}
            </span>
          )}
        </button>
      </div>

      {/* Quick Actions Toolbar */}
      <div className={styles.quickActions}>
        <button
          type="button"
          className={styles.actionBtn}
          onClick={(e) => {
            e.stopPropagation();
            onSelectProject(project);
          }}
        >
          <span>👁️</span> BRIEFING
        </button>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.primary}`}
          onClick={(e) => {
            e.stopPropagation();
            onGenerateAiProposal(project.id);
          }}
        >
          <span>⚡</span> IA STRATEGY
        </button>
        <a
          href={project.url}
          target="_blank"
          rel="noreferrer"
          className={styles.actionBtn}
          onClick={(e) => e.stopPropagation()}
        >
          <span>🔗</span> LINK
        </a>
      </div>
    </div>
  );
};
