import React, { useState, useEffect } from 'react';
import { DollarSign, Copy, Check, X, Calculator } from 'lucide-react';
import { api, type InvestmentCalculationResponse } from '../services/api';
import { useToast } from '../context/ToastContext';
import styles from './InvestmentCalculatorModal.module.css';

interface InvestmentCalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const QUICK_AMOUNTS = [3000, 5000, 8000, 12000, 20000];

export default function InvestmentCalculatorModal({
  isOpen,
  onClose,
}: InvestmentCalculatorModalProps) {
  const { toast } = useToast();
  const [totalValue, setTotalValue] = useState<number>(5000);
  const [inputValue, setInputValue] = useState<string>('5000');
  const [breakdown, setBreakdown] = useState<InvestmentCalculationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const calculate = async (val: number) => {
    if (val <= 0) return;
    setLoading(true);
    try {
      const res = await api.calculateInvestment({ total_value: val });
      setBreakdown(res);
    } catch {
      toast.error('Erro ao calcular investimento.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      calculate(totalValue);
    }
  }, [isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '');
    setInputValue(raw);
    const num = Number(raw);
    if (num > 0) {
      setTotalValue(num);
      calculate(num);
    }
  };

  const handleQuickSelect = (amt: number) => {
    setTotalValue(amt);
    setInputValue(String(amt));
    calculate(amt);
  };

  const handleCopyText = async () => {
    if (!breakdown?.breakdown_text) return;
    try {
      await navigator.clipboard.writeText(breakdown.breakdown_text);
      setCopied(true);
      toast.success('Detalhamento copiado para a área de transferência!');
      setTimeout(() => setCopied(false), 2500);
    } catch {
      toast.error('Não foi possível copiar o texto.');
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <div className={styles.iconBadge}>
              <Calculator size={20} />
            </div>
            <div>
              <h3 className={styles.title}>Calculadora de Investimento MVP</h3>
              <p className={styles.subtitle}>
                Decomposição proporcional de etapas de desenvolvimento
              </p>
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            <X size={20} />
          </button>
        </div>

        <div className={styles.body}>
          {/* Input de Valor */}
          <div className={styles.inputGroup}>
            <label className={styles.label}>Valor Total do Projeto (BRL)</label>
            <div className={styles.inputWrapper}>
              <span className={styles.currencyPrefix}>R$</span>
              <input
                type="text"
                className={styles.inputField}
                value={Number(inputValue || 0).toLocaleString('pt-BR')}
                onChange={handleInputChange}
                placeholder="5.000"
              />
            </div>
            <div className={styles.quickPills}>
              {QUICK_AMOUNTS.map((amt) => (
                <button
                  key={amt}
                  type="button"
                  className={styles.pillBtn}
                  onClick={() => handleQuickSelect(amt)}
                >
                  R$ {amt.toLocaleString('pt-BR')}
                </button>
              ))}
            </div>
          </div>

          {/* Cards de Etapas */}
          <div className={styles.stagesContainer}>
            {breakdown?.stages.map((stage, idx) => (
              <div key={idx} className={styles.stageCard}>
                <div className={styles.stageLeft}>
                  <div className={styles.stagePercentBadge}>{stage.percentage}%</div>
                  <div className={styles.stageInfo}>
                    <div className={styles.stageTitle}>{stage.title}</div>
                    <div className={styles.stageDesc}>{stage.description}</div>
                  </div>
                </div>
                <div className={styles.stageAmount}>{stage.amount_formatted}</div>
              </div>
            ))}
          </div>

          {/* Preview do Texto Formatado */}
          {breakdown?.breakdown_text && (
            <div className={styles.inputGroup}>
              <label className={styles.label}>Texto Gerado para Proposta:</label>
              <div className={styles.previewTextCard}>{breakdown.breakdown_text}</div>
            </div>
          )}
        </div>

        <div className={styles.footer}>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Fechar
          </button>
          <button
            className={`btn btn-primary btn-sm ${styles.copyBtn}`}
            onClick={handleCopyText}
            disabled={!breakdown?.breakdown_text}
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            {copied ? 'Copiado!' : 'Copiar para Proposta'}
          </button>
        </div>
      </div>
    </div>
  );
}
