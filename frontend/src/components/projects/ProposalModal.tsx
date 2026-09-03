import React, { useState } from 'react';
import Loader from '../Loader';
import { ProposalTemplate, InvestmentBreakdown, ProposalVersion } from '../../services/api';

export type PriceLevel = 'budget' | 'standard' | 'premium';

export interface PriceLevelOption {
  value: PriceLevel;
  label: string;
  icon: string;
  description: string;
  color: string;
}

export const PRICE_LEVELS: PriceLevelOption[] = [
  {
    value: 'budget',
    label: 'Barato',
    icon: '💰',
    description: 'Foco no essencial (MVP)',
    color: 'rgba(34, 197, 94, 0.15)',
  },
  {
    value: 'standard',
    label: 'Médio',
    icon: '💎',
    description: 'Equilíbrio ideal (Padrão)',
    color: 'rgba(59, 130, 246, 0.15)',
  },
  {
    value: 'premium',
    label: 'Caro',
    icon: '👑',
    description: 'Máxima qualidade (High-Ticket)',
    color: 'rgba(168, 85, 247, 0.15)',
  },
];

export interface ProposalData {
  id?: number;
  proposal?: string;
  suggested_price?: string;
  justification?: string;
  status?: string;
  sent_at?: string;
  is_cached?: boolean;
  investment_breakdown?: InvestmentBreakdown;
  template_id?: any;
  template_slug?: string;
}

interface ProposalModalProps {
  isOpen: boolean;
  templates: ProposalTemplate[];
  selectedTemplateId: string | null;
  priceLevel: PriceLevel;
  versions: ProposalVersion[];
  activeVersionId: number | null;
  isGenerating: boolean;
  isSubmitting: boolean;
  isSaving?: boolean;
  error: string | null;
  proposalData: ProposalData | null;
  budget: string;
  deadline: string;
  onClose: () => void;
  onTemplateChange: (templateRef: string | null) => void;
  onPriceLevelChange: (level: PriceLevel) => void;
  onSelectVersion: (version: ProposalVersion) => void;
  onDeleteVersion?: (versionId: number) => void;
  onGenerateNewVersion: () => void;
  onProposalChange?: (text: string) => void;
  onInvestmentChange?: (text: string) => void;
  onBudgetChange: (val: string) => void;
  onDeadlineChange: (val: string) => void;
  onCopy: () => void;
  onSubmit: () => void;
  onSaveDraft?: () => void;
}

export const ProposalModal: React.FC<ProposalModalProps> = ({
  isOpen,
  templates,
  selectedTemplateId,
  priceLevel = 'standard',
  versions = [],
  activeVersionId,
  isGenerating,
  isSubmitting,
  isSaving = false,
  error,
  proposalData,
  budget,
  deadline,
  onClose,
  onTemplateChange,
  onPriceLevelChange,
  onSelectVersion,
  onDeleteVersion,
  onGenerateNewVersion,
  onProposalChange,
  onInvestmentChange,
  onBudgetChange,
  onDeadlineChange,
  onCopy,
  onSubmit,
  onSaveDraft,
}) => {
  const [copied, setCopied] = useState(false);
  const [showConfigDrawer, setShowConfigDrawer] = useState(false);

  if (!isOpen) return null;

  const isSent = proposalData?.status === 'sent';

  const handleCopyClick = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const text = proposalData?.proposal || '';
  const investmentText = proposalData?.investment_breakdown?.breakdown_text || '';
  const fullProposal = investmentText ? `${text}\n\n${investmentText}` : text;
  const charCount = fullProposal.length;
  const wordCount = fullProposal.trim() ? fullProposal.trim().split(/\s+/).length : 0;

  const formatVersionTime = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const hasProposalLoaded = Boolean(
    proposalData?.proposal && proposalData.proposal.trim().length > 0
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{
          maxWidth: '960px',
          width: '95vw',
          maxHeight: '92vh',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), 0 0 35px rgba(99, 102, 241, 0.25)',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header do Modal */}
        <div
          className="modal-header"
          style={{ padding: '1.1rem 1.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h3
              className="modal-title"
              style={{
                margin: 0,
                fontSize: '1.25rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>✨</span> Estratégia Comercial & Proposta IA
            </h3>

            {isSent ? (
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(16, 185, 129, 0.2)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  fontWeight: 600,
                }}
              >
                🚀 Proposta Enviada
              </span>
            ) : proposalData?.is_cached ? (
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(59, 130, 246, 0.2)',
                  color: '#60a5fa',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  fontWeight: 600,
                }}
              >
                📝 Rascunho Salvo
              </span>
            ) : null}

            {versions.length > 0 && (
              <span
                style={{
                  fontSize: '0.72rem',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(99, 102, 241, 0.15)',
                  color: '#c7d2fe',
                  border: '1px solid rgba(99, 102, 241, 0.35)',
                  fontWeight: 600,
                }}
              >
                🗂️ {versions.length} {versions.length === 1 ? 'Versão' : 'Versões'}
              </span>
            )}
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div
          className="modal-body"
          style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', flex: 1 }}
        >
          {/* Barra de Navegação de Versões */}
          {versions.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    color: 'var(--color-primary-light)',
                  }}
                >
                  Histórico de Versões Geradas
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                  Navegue entre versões sem perder nenhuma resposta
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: '0.5rem',
                  overflowX: 'auto',
                  paddingBottom: '4px',
                  alignItems: 'center',
                }}
              >
                {versions.map((ver, idx) => {
                  const isSelected = activeVersionId === ver.id || (!activeVersionId && idx === 0);
                  const versionNumber = versions.length - idx;
                  const timeStr = formatVersionTime(ver.sent_at);
                  const isSentStatus = ver.status === 'sent';

                  return (
                    <div
                      key={ver.id || idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        backgroundColor: isSelected
                          ? 'rgba(99, 102, 241, 0.2)'
                          : 'rgba(15, 23, 42, 0.7)',
                        border: `1.5px solid ${isSelected ? 'var(--color-primary)' : 'rgba(255, 255, 255, 0.1)'}`,
                        borderRadius: '8px',
                        padding: '4px 8px 4px 10px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: isSelected ? '0 0 12px rgba(99, 102, 241, 0.3)' : 'none',
                        gap: '6px',
                        flexShrink: 0,
                      }}
                      onClick={() => onSelectVersion(ver)}
                      title={`Versão ${versionNumber} - ${ver.status || 'gerada'}`}
                    >
                      <span style={{ fontSize: '0.85rem' }}>{isSentStatus ? '🚀' : '⚡'}</span>
                      <span
                        style={{
                          fontSize: '0.8rem',
                          fontWeight: isSelected ? 700 : 500,
                          color: isSelected ? '#fff' : '#cbd5e1',
                        }}
                      >
                        Versão {versionNumber}
                      </span>
                      {timeStr && (
                        <span style={{ fontSize: '0.7rem', color: '#94a3b8', opacity: 0.8 }}>
                          ({timeStr})
                        </span>
                      )}
                      {ver.budget && (
                        <span style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 600 }}>
                          R$ {ver.budget}
                        </span>
                      )}

                      {onDeleteVersion && versions.length > 1 && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`Excluir Versão ${versionNumber}?`)) {
                              onDeleteVersion(ver.id);
                            }
                          }}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#ef4444',
                            padding: '0 2px',
                            marginLeft: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem',
                            opacity: 0.6,
                          }}
                          title="Excluir esta versão"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  );
                })}

                <button
                  type="button"
                  onClick={() => setShowConfigDrawer(!showConfigDrawer)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '5px 10px',
                    borderRadius: '8px',
                    border: '1px dashed rgba(99, 102, 241, 0.4)',
                    backgroundColor: showConfigDrawer
                      ? 'rgba(99, 102, 241, 0.2)'
                      : 'rgba(99, 102, 241, 0.08)',
                    color: 'var(--color-primary-light)',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  <span>{showConfigDrawer ? '▲' : '➕'}</span>
                  <span>{showConfigDrawer ? 'Ocultar Painel IA' : 'Nova Geração'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Painel de Configuração da Geração (Exibido sempre se não tiver proposta gerada, ou toggle se já tiver) */}
          {(!hasProposalLoaded || showConfigDrawer) && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '1.25rem',
                boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    color: 'var(--color-primary-light)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span>🎯</span> Parâmetros da IA para{' '}
                  {hasProposalLoaded ? 'Nova Versão' : 'Gerar Proposta'}
                </h4>
                {hasProposalLoaded && (
                  <button
                    type="button"
                    onClick={() => setShowConfigDrawer(false)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#94a3b8',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                    }}
                  >
                    Fechar Painel ✕
                  </button>
                )}
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1.2fr',
                  gap: '1rem',
                  marginBottom: '1rem',
                }}
              >
                {/* Seletor de Modelo / Template */}
                <div>
                  <label
                    className="form-label"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      marginBottom: '0.35rem',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                    }}
                  >
                    <span>Modelo de Proposta</span>
                  </label>
                  <select
                    className="form-input"
                    value={selectedTemplateId || ''}
                    onChange={(e) => onTemplateChange(e.target.value || null)}
                    disabled={isGenerating}
                    style={{
                      width: '100%',
                      padding: '0.6rem 0.75rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg-secondary)',
                      color: 'var(--color-text)',
                      outline: 'none',
                      fontSize: '0.88rem',
                    }}
                  >
                    <option value="">Padrão do Sistema (Proposta Master MVP)</option>
                    {templates.map((t) => (
                      <option key={t.template_ref || t.id} value={t.template_ref || String(t.id)}>
                        {t.name} {t.is_system ? '🛡️ (Oficial)' : ''}{' '}
                        {t.is_default ? '⭐ (Padrão)' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Seletor de Modalidade de Investimento */}
                <div>
                  <label
                    className="form-label"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      marginBottom: '0.35rem',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                    }}
                  >
                    <span>Modalidade de Valor</span>
                  </label>
                  <div
                    style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}
                  >
                    {PRICE_LEVELS.map((level) => {
                      const isSelected = priceLevel === level.value;
                      return (
                        <button
                          key={level.value}
                          type="button"
                          onClick={() => onPriceLevelChange(level.value)}
                          disabled={isGenerating}
                          style={{
                            padding: '0.5rem 0.4rem',
                            borderRadius: 'var(--radius-md)',
                            border: `1.5px solid ${isSelected ? 'rgba(99, 102, 241, 0.9)' : 'rgba(255,255,255,0.08)'}`,
                            backgroundColor: isSelected ? level.color : 'rgba(0,0,0,0.25)',
                            cursor: isGenerating ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s ease',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '2px',
                          }}
                        >
                          <span style={{ fontSize: '1.1rem' }}>{level.icon}</span>
                          <span
                            style={{
                              fontWeight: 700,
                              fontSize: '0.78rem',
                              color: isSelected ? '#fff' : '#cbd5e1',
                            }}
                          >
                            {level.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              <button
                type="button"
                className="btn btn-primary w-full"
                onClick={() => {
                  onGenerateNewVersion();
                  setShowConfigDrawer(false);
                }}
                disabled={isGenerating}
                style={{
                  padding: '0.75rem 1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.6rem',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
                }}
              >
                <span>⚡</span>
                <span>
                  {hasProposalLoaded
                    ? `Gerar Nova Versão (v${versions.length + 1}) com IA`
                    : 'Gerar Proposta Estruturada com IA'}
                </span>
              </button>
            </div>
          )}

          {/* Estado de Carregamento */}
          {isGenerating ? (
            <div style={{ padding: '50px 0', textAlign: 'center' }}>
              <Loader
                type="scanning"
                message="Arquitetando proposta de elite, escopo modular e fatiamento do investimento..."
              />
            </div>
          ) : error ? (
            <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
              {error}
            </div>
          ) : hasProposalLoaded ? (
            <div>
              {/* Destaques de Investimento e Justificativa */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 2fr',
                  gap: '1rem',
                  marginBottom: '1.25rem',
                }}
              >
                <div
                  className="card text-center p-3"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    backgroundColor: 'rgba(99, 102, 241, 0.05)',
                  }}
                >
                  <div
                    className="text-xs text-muted"
                    style={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}
                  >
                    Valor Sugerido
                  </div>
                  <div className="text-2xl font-bold text-primary" style={{ marginTop: '0.25rem' }}>
                    {proposalData?.suggested_price || '—'}
                  </div>
                </div>
                <div className="card p-3" style={{ border: '1px solid var(--color-border)' }}>
                  <div
                    className="text-xs text-muted mb-1"
                    style={{ fontWeight: 600, textTransform: 'uppercase' }}
                  >
                    Justificativa Técnica
                  </div>
                  <div className="text-xs" style={{ lineHeight: 1.5, opacity: 0.9 }}>
                    {proposalData?.justification ||
                      'Proposta estruturada com Padrão Master MVP, escopo modular fatiado e garantia de entrega validável.'}
                  </div>
                </div>
              </div>

              {/* Inputs de Preço e Prazo para Submissão */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '1rem',
                  marginBottom: '1.25rem',
                }}
              >
                <div className="form-group" style={{ margin: 0 }}>
                  <label
                    className="form-label"
                    style={{ fontWeight: 600, marginBottom: '0.35rem', fontSize: '0.85rem' }}
                  >
                    Valor da Proposta (R$)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={budget}
                    onChange={(e) => onBudgetChange(e.target.value)}
                    placeholder="Ex: 4500"
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg-secondary)',
                      color: 'var(--color-text)',
                      outline: 'none',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                    }}
                  />
                </div>
                <div className="form-group" style={{ margin: 0 }}>
                  <label
                    className="form-label"
                    style={{ fontWeight: 600, marginBottom: '0.35rem', fontSize: '0.85rem' }}
                  >
                    Prazo de Entrega (Dias)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={deadline}
                    onChange={(e) => onDeadlineChange(e.target.value)}
                    placeholder="Ex: 20"
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg-secondary)',
                      color: 'var(--color-text)',
                      outline: 'none',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                    }}
                  />
                </div>
              </div>

              {/* Editor de Texto da Proposta */}
              <div className="form-group" style={{ margin: 0 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '0.4rem',
                  }}
                >
                  <label
                    className="form-label"
                    style={{ fontWeight: 600, margin: 0, fontSize: '0.9rem' }}
                  >
                    Texto da Proposta Comercial (Editável)
                  </label>
                  <span style={{ fontSize: '0.75rem', opacity: 0.75, fontFamily: 'monospace' }}>
                    {charCount.toLocaleString('pt-BR')} caracteres • {wordCount} palavras
                  </span>
                </div>
                <textarea
                  className="form-input"
                  rows={15}
                  value={fullProposal}
                  onChange={(e) => {
                    const newFullText = e.target.value;
                    const investmentMarker = '💰 Detalhamento do Investimento';
                    const investmentIdx = newFullText.indexOf(investmentMarker);
                    if (investmentIdx > -1) {
                      const proposalPart = newFullText.substring(0, investmentIdx).trim();
                      const investmentPart = newFullText.substring(investmentIdx).trim();
                      onProposalChange?.(proposalPart);
                      onInvestmentChange?.(investmentPart);
                    } else {
                      onProposalChange?.(newFullText);
                    }
                  }}
                  placeholder="A proposta estruturada aparecerá aqui..."
                  style={{
                    width: '100%',
                    minHeight: '360px',
                    maxHeight: '500px',
                    padding: '1rem',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-bg-secondary)',
                    color: 'var(--color-text)',
                    lineHeight: 1.65,
                    fontSize: '0.925rem',
                    fontFamily: 'inherit',
                    resize: 'vertical',
                    whiteSpace: 'pre-wrap',
                  }}
                />
              </div>

              {/* Barra de Ações Inferior */}
              <div
                style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', flexWrap: 'wrap' }}
              >
                <button
                  type="button"
                  className="btn"
                  style={{
                    flex: 1,
                    minWidth: '140px',
                    backgroundColor: copied
                      ? 'rgba(16, 185, 129, 0.2)'
                      : 'var(--color-bg-tertiary)',
                    borderColor: copied ? '#10b981' : 'var(--color-border)',
                    color: copied ? '#10b981' : 'var(--color-text)',
                    fontWeight: 600,
                    transition: 'all 0.2s ease',
                  }}
                  onClick={handleCopyClick}
                >
                  {copied ? '✓ Copiado!' : '📋 Copiar Proposta'}
                </button>

                {onSaveDraft && (
                  <button
                    type="button"
                    className="btn"
                    style={{
                      flex: 1.2,
                      minWidth: '180px',
                      backgroundColor: 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      color: '#60a5fa',
                      fontWeight: 600,
                    }}
                    onClick={onSaveDraft}
                    disabled={isSaving || !proposalData?.proposal}
                  >
                    {isSaving ? 'Salvando...' : '💾 Salvar Rascunho'}
                  </button>
                )}

                <button
                  type="button"
                  className="btn btn-primary"
                  style={{
                    flex: 1.6,
                    minWidth: '220px',
                    fontWeight: 700,
                    boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                  }}
                  onClick={onSubmit}
                  disabled={isSubmitting || !proposalData?.proposal}
                >
                  {isSubmitting
                    ? 'Enviando...'
                    : isSent
                      ? '🚀 Reenviar Proposta'
                      : '🚀 Enviar Proposta'}
                </button>
              </div>
            </div>
          ) : (
            <div
              style={{ padding: '30px 0', textAlign: 'center', color: 'var(--color-text-muted)' }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🤖</div>
              <h4 style={{ color: '#fff', marginBottom: '0.5rem' }}>
                Nenhuma proposta gerada ainda
              </h4>
              <p style={{ maxWidth: '420px', margin: '0 auto 1.5rem', fontSize: '0.85rem' }}>
                Escolha o modelo e a modalidade de valor acima e clique no botão para gerar uma
                proposta técnica altamente persuasiva.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
