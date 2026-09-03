/**
 * Serviços de API para a Calculadora de Investimento e Decomposição de MVP.
 */
import { apiRequest } from './client';

export interface StageDetail {
  title: string;
  description: string;
  percentage: number;
  amount: number;
  amount_formatted: string;
}

export interface InvestmentCalculationResponse {
  total_value: number;
  total_formatted: string;
  stages: StageDetail[];
  breakdown_text: string;
}

export interface InvestmentPreviewResponse {
  total_value: number;
  total_formatted: string;
  breakdown_text: string;
  stages_summary: string[];
}

export const investmentApi = {
  async calculateInvestment(data: {
    total_value: number;
    custom_percentages?: Record<string, number>;
  }) {
    return apiRequest<InvestmentCalculationResponse>('/investment/calculate', {
      method: 'POST',
      body: data,
    });
  },

  async previewInvestment(totalValue: number) {
    return apiRequest<InvestmentPreviewResponse>(`/investment/preview/${totalValue}`);
  },
};
