import React, { useState, useEffect } from 'react';
import styles from '../../pages/Projects.module.css';
import { ProposalTemplate } from '../../services/api';

const CONTRACT_LABELS: Record<string, string> = {
  project_fixed: 'Preço Fixo',
  project_hourly: 'Por Hora',
  unknown: 'Não Especificado',
};

type PriceLevel = 'budget' | 'standard' | 'premium';

interface ProjectDetail {
  id: string;
  title: string;
  description: string;
  budget: string | null;
  category?: string | null;
  subcategory?: string | null;
  deadline?: string | null;
  details?: Record<string, string>;
  skills: string[];
  client_name?: string | null;
  client_country?: string | null;
  client_rating?: number | null;
  client_plan?: string | null;
  client_projects_posted?: number | null;
  client_projects_paid?: number | null;
  client_member_since?: string | null;
  proposals_count: number | null;
  posted_at: string | null;
  published_at?: string | null;
  payment_verified?: boolean | null;
  last_client_activity?: string | null;
  is_urgent?: boolean;
  is_featured?: boolean;
  proposals_delta?: number | null;
  contract_type?: string | null;
  project_type?: string | null;
  url: string;
}

interface ProjectDetailModalProps {
  project: ProjectDetail | null;
  templates?: ProposalTemplate[];
  selectedTemplateId?: string | null;
  priceLevel?: PriceLevel;
  onClose: () => void;
  onGenerateProposal: (
    projectId: string,
    templateRef?: string | null,
    priceLevel?: PriceLevel
  ) => void;
}

export const ProjectDetailModal: React.FC<ProjectDetailModalProps> = ({
  project,
  templates = [],
  selectedTemplateId = null,
  priceLevel = 'standard',
  onClose,
  onGenerateProposal,
}) => {
  const [localTemplateId, setLocalTemplateId] = useState<string | null>(selectedTemplateId);
  const [localPriceLevel, setLocalPriceLevel] = useState<PriceLevel>(priceLevel);

  useEffect(() => {
    setLocalTemplateId(selectedTemplateId);
  }, [selectedTemplateId]);

  useEffect(() => {
    setLocalPriceLevel(priceLevel);
  }, [priceLevel]);

  if (!project) return null;

  const formatDelta = (delta?: number | null) => {
    if (!delta || delta === 0) return null;
    return delta > 0 ? `+${delta}` : `${delta}`;
  };

  return (
    <div className={styles.dossierOverlay} onClick={onClose}>
      <div className={styles.dossierContainer} onClick={(e) => e.stopPropagation()}>
        <div
          className={styles.dossierHeader}
          style={{ display: 'block', position: 'relative', paddingRight: '60px' }}
        >
          <div style={{ textAlign: 'center', marginBottom: '16px' }}>
            <span
              style={{
                color: 'var(--color-primary)',
                fontSize: '0.85rem',
                letterSpacing: '4px',
                fontWeight: '600',
                textShadow: '0 0 10px rgba(99, 102, 241, 0.5)',
              }}
            >
              TOP SECRET // MISSION FILE
            </span>
          </div>

          <button
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Fechar Detalhes"
            style={{ position: 'absolute', top: '24px', right: '24px' }}
          >
            ×
          </button>

          <div>
            <div
              style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap',
                marginBottom: '8px',
                alignItems: 'center',
              }}
            >
              {project.is_urgent && (
                <span
                  style={{
                    background: '#ef4444',
                    color: '#fff',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    letterSpacing: '1px',
                  }}
                >
                  ⚡ URGENTE
                </span>
              )}
              {project.is_featured && (
                <span
                  style={{
                    background: '#f59e0b',
                    color: '#000',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    letterSpacing: '1px',
                  }}
                >
                  ⭐ DESTAQUE
                </span>
              )}
              {project.client_plan && (
                <span
                  style={{
                    background: 'rgba(99, 102, 241, 0.15)',
                    color: '#818cf8',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    padding: '2px 8px',
                    borderRadius: '4px',
                  }}
                >
                  👑 {project.client_plan.toUpperCase()}
                </span>
              )}
              {project.category && (
                <span
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--color-text-muted)',
                    fontSize: '0.7rem',
                    padding: '2px 8px',
                    borderRadius: '4px',
                  }}
                >
                  📁 {project.category}
                  {project.subcategory ? ` / ${project.subcategory}` : ''}
                </span>
              )}
            </div>
            <h2
              style={{
                fontSize: '1.8rem',
                fontWeight: 'bold',
                lineHeight: '1.2',
                marginBottom: '8px',
              }}
            >
              {project.title}
            </h2>
            <div
              style={{
                fontSize: '1.1rem',
                color: '#34d399',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span
                style={{
                  opacity: 0.7,
                  fontSize: '0.9rem',
                  fontWeight: 'normal',
                  color: 'var(--color-text-muted)',
                }}
              >
                ORÇAMENTO DO PROJETO:
              </span>
              {project.budget || 'NEGOCIÁVEL'}
            </div>
          </div>
        </div>

        <div className={styles.dossierBody} style={{ padding: 0, overflow: 'hidden' }}>
          <div className={styles.dossierContentGrid}>
            <div className={styles.dossierMain} style={{ padding: '2rem' }}>
              <h4
                style={{
                  color: 'var(--color-text-muted)',
                  fontSize: '0.9rem',
                  marginBottom: '1rem',
                  textTransform: 'uppercase',
                }}
              >
                &gt; Descrição da Missão (Decoded)
              </h4>
              <div className={styles.decryptText}>
                {project.description?.trim() ? (
                  project.description
                ) : (
                  <div
                    style={{
                      color: 'var(--color-text-muted)',
                      fontStyle: 'italic',
                      padding: '1.2rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      border: '1px dashed rgba(255, 255, 255, 0.1)',
                    }}
                  >
                    <span
                      style={{
                        display: 'block',
                        color: 'var(--color-primary)',
                        fontWeight: 'bold',
                        marginBottom: '6px',
                      }}
                    >
                      ℹ️ NENHUM TEXTO LIVRE INFORMADO
                    </span>
                    O contratante não incluiu uma descrição textual avulsa. Verifique o{' '}
                    <strong>Arsenal (Skills)</strong> e o <strong>Briefing Estruturado</strong> no
                    painel ao lado para as especificações técnicas da oportunidade.
                  </div>
                )}
              </div>
            </div>

            <div className={styles.dossierSidebar}>
              <div>
                <h4
                  style={{
                    color: 'var(--color-text-muted)',
                    fontSize: '0.8rem',
                    marginBottom: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                  }}
                >
                  &gt; Arsenal (Skills)
                </h4>
                <div className={styles.techStack} style={{ flexWrap: 'wrap' }}>
                  {project.skills?.length > 0 ? (
                    project.skills.map((skill) => (
                      <span
                        key={skill}
                        className={styles.techTag}
                        style={{ marginBottom: '6px', fontSize: '0.75rem' }}
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span
                      style={{
                        color: 'var(--color-text-muted)',
                        fontSize: '0.75rem',
                        fontStyle: 'italic',
                      }}
                    >
                      Nenhuma skill explícita listada
                    </span>
                  )}
                </div>
              </div>

              <div>
                <h4
                  style={{
                    color: 'var(--color-text-muted)',
                    fontSize: '0.8rem',
                    marginBottom: '0.75rem',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                  }}
                >
                  &gt; Dados de Inteligência
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div
                    className="card p-3 bg-glass"
                    style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                  >
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.7rem',
                        color: '#64748b',
                        marginBottom: '4px',
                      }}
                    >
                      DATA DE PUBLICAÇÃO
                    </span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {project.posted_at || project.published_at || 'Recente'}
                    </span>
                  </div>
                  <div
                    className="card p-3 bg-glass"
                    style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                  >
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.7rem',
                        color: '#64748b',
                        marginBottom: '4px',
                      }}
                    >
                      CONCORRÊNCIA
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {project.proposals_count ?? 0} Candidatos
                      </span>
                      {formatDelta(project.proposals_delta) && (
                        <span
                          className={styles.deltaChip}
                          style={{
                            color: (project.proposals_delta ?? 0) > 0 ? '#6ee7b7' : '#fca5a5',
                            background:
                              (project.proposals_delta ?? 0) > 0
                                ? 'rgba(16,185,129,0.12)'
                                : 'rgba(239,68,68,0.12)',
                            fontSize: '0.75rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                          }}
                        >
                          {formatDelta(project.proposals_delta)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div
                    className="card p-3 bg-glass"
                    style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                  >
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.7rem',
                        color: '#64748b',
                        marginBottom: '4px',
                      }}
                    >
                      CLIENTE
                    </span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {project.client_name || 'Não informado'}
                      {project.client_country ? ` · ${project.client_country}` : ''}
                    </span>
                    {project.client_plan && (
                      <small
                        style={{
                          display: 'block',
                          marginTop: '2px',
                          color: '#818cf8',
                          fontWeight: '600',
                        }}
                      >
                        Plano: {project.client_plan}
                      </small>
                    )}
                  </div>
                  {project.last_client_activity && (
                    <div
                      className="card p-3 bg-glass"
                      style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                    >
                      <span
                        style={{
                          display: 'block',
                          fontSize: '0.7rem',
                          color: '#64748b',
                          marginBottom: '4px',
                        }}
                      >
                        ÚLTIMA ATIVIDADE DO CLIENTE
                      </span>
                      <span
                        style={{ fontFamily: 'monospace', fontWeight: 'bold', fontSize: '0.85rem' }}
                      >
                        {project.last_client_activity}
                      </span>
                    </div>
                  )}
                  <div
                    className="card p-3 bg-glass"
                    style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                  >
                    <span
                      style={{
                        display: 'block',
                        fontSize: '0.7rem',
                        color: '#64748b',
                        marginBottom: '4px',
                      }}
                    >
                      CONFIABILIDADE
                    </span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {project.payment_verified
                        ? '✓ Pagamento verificado'
                        : 'Pagamento não verificado'}
                      {project.client_rating != null
                        ? ` · ★ ${project.client_rating.toFixed(1)}`
                        : ''}
                    </span>
                  </div>
                  {(project.project_type || project.deadline || project.contract_type) && (
                    <div
                      className="card p-3 bg-glass"
                      style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                    >
                      <span
                        style={{
                          display: 'block',
                          fontSize: '0.7rem',
                          color: '#64748b',
                          marginBottom: '4px',
                        }}
                      >
                        CONTRATO
                      </span>
                      <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {project.contract_type
                          ? CONTRACT_LABELS[project.contract_type] || project.contract_type
                          : project.project_type === 'hourly'
                            ? 'Por hora'
                            : 'Preço fixo'}
                        {project.deadline ? ` · ${project.deadline}` : ''}
                      </span>
                    </div>
                  )}
                  {(project.client_projects_posted != null ||
                    project.client_projects_paid != null) && (
                    <div
                      className="card p-3 bg-glass"
                      style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                    >
                      <span
                        style={{
                          display: 'block',
                          fontSize: '0.7rem',
                          color: '#64748b',
                          marginBottom: '4px',
                        }}
                      >
                        HISTÓRICO DO CLIENTE
                      </span>
                      <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {project.client_projects_posted ?? 0} publicados ·{' '}
                        {project.client_projects_paid ?? 0} pagos
                      </span>
                      {project.client_member_since && (
                        <small style={{ display: 'block' }}>
                          Desde {project.client_member_since}
                        </small>
                      )}
                    </div>
                  )}
                  {project.details && Object.keys(project.details).length > 0 && (
                    <div
                      className="card p-3 bg-glass"
                      style={{ border: '1px solid rgba(255,255,255,0.05)' }}
                    >
                      <span
                        style={{
                          display: 'block',
                          fontSize: '0.7rem',
                          color: '#64748b',
                          marginBottom: '6px',
                        }}
                      >
                        BRIEFING ESTRUTURADO
                      </span>
                      {Object.entries(project.details)
                        .filter(([key]) => !['category', 'subcategory'].includes(key))
                        .map(([key, value]) => (
                          <small key={key} style={{ display: 'block', marginBottom: '2px' }}>
                            <strong style={{ color: 'var(--color-primary)' }}>
                              {key.replace(/_/g, ' ')}:
                            </strong>{' '}
                            {value}
                          </small>
                        ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Card de Configuração Prévia da Proposta */}
              <div
                className="card p-3 bg-glass"
                style={{
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  backgroundColor: 'rgba(99, 102, 241, 0.05)',
                  borderRadius: '10px',
                }}
              >
                <h4
                  style={{
                    color: 'var(--color-primary-light)',
                    fontSize: '0.8rem',
                    marginBottom: '0.6rem',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span>⚙️</span> Estratégia da Proposta
                </h4>

                <div style={{ marginBottom: '0.6rem' }}>
                  <label
                    style={{
                      fontSize: '0.7rem',
                      color: '#94a3b8',
                      display: 'block',
                      marginBottom: '4px',
                    }}
                  >
                    Modelo / Template
                  </label>
                  <select
                    value={localTemplateId || ''}
                    onChange={(e) => setLocalTemplateId(e.target.value || null)}
                    style={{
                      width: '100%',
                      padding: '6px 8px',
                      fontSize: '0.75rem',
                      borderRadius: '6px',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      background: 'rgba(15, 23, 42, 0.8)',
                      color: '#fff',
                    }}
                  >
                    <option value="">Padrão (Master MVP)</option>
                    {templates.map((t) => (
                      <option key={t.template_ref || t.id} value={t.template_ref || String(t.id)}>
                        {t.name} {t.is_system ? '🛡️' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    style={{
                      fontSize: '0.7rem',
                      color: '#94a3b8',
                      display: 'block',
                      marginBottom: '4px',
                    }}
                  >
                    Modalidade de Valor
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '4px' }}>
                    {(['budget', 'standard', 'premium'] as PriceLevel[]).map((lvl) => {
                      const labels: Record<PriceLevel, { icon: string; title: string }> = {
                        budget: { icon: '💰', title: 'Barato' },
                        standard: { icon: '💎', title: 'Médio' },
                        premium: { icon: '👑', title: 'Caro' },
                      };
                      const isSelected = localPriceLevel === lvl;
                      return (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setLocalPriceLevel(lvl)}
                          style={{
                            padding: '4px 2px',
                            fontSize: '0.7rem',
                            borderRadius: '4px',
                            border: `1px solid ${isSelected ? 'var(--color-primary)' : 'rgba(255,255,255,0.1)'}`,
                            background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(0,0,0,0.2)',
                            color: isSelected ? '#fff' : '#94a3b8',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '3px',
                          }}
                        >
                          <span>{labels[lvl].icon}</span>
                          <span>{labels[lvl].title}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div
                style={{
                  marginTop: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <button
                  className="btn btn-primary w-full"
                  onClick={() => onGenerateProposal(project.id, localTemplateId, localPriceLevel)}
                  style={{
                    height: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontWeight: 700,
                  }}
                >
                  <span>⚡</span> Abrir & Gerar Proposta
                </button>
                <a
                  href={project.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary w-full"
                  style={{
                    textAlign: 'center',
                    height: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  Abrir no Workana ↗
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
