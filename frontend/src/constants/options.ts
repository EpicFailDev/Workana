/**
 * Opções de filtros, ordenação e intervalos reutilizáveis na aplicação.
 */

export interface SelectOption {
    value: string;
    label: string;
}

export const SORT_OPTIONS: SelectOption[] = [
    { value: "newest", label: "Mais Recentes (Publicação)" },
    { value: "oldest", label: "Mais Antigos" },
    { value: "ranking", label: "Maior Ranking / Score IA" },
    { value: "budget_desc", label: "Maior Orçamento" },
    { value: "budget_asc", label: "Menor Orçamento" },
    { value: "bids_asc", label: "Menos Propostas (Menor Concorrência)" },
    { value: "bids_desc", label: "Mais Propostas" },
];

export const PUBLICATION_OPTIONS: SelectOption[] = [
    { value: "all", label: "Qualquer Período" },
    { value: "1h", label: "Última 1 hora" },
    { value: "24h", label: "Últimas 24 horas" },
    { value: "3d", label: "Últimos 3 dias" },
    { value: "7d", label: "Última semana" },
    { value: "30d", label: "Último mês" },
];

export const LANGUAGE_OPTIONS: SelectOption[] = [
    { value: "all", label: "Todos os Idiomas" },
    { value: "pt", label: "Português" },
    { value: "es", label: "Espanhol" },
    { value: "en", label: "Inglês" },
];

export const PROPOSALS_COUNT_OPTIONS: SelectOption[] = [
    { value: "all", label: "Qualquer Quantidade" },
    { value: "less_than_5", label: "Menos de 5 propostas (Oportunidade)" },
    { value: "5_to_15", label: "5 a 15 propostas" },
    { value: "15_plus", label: "Mais de 15 propostas" },
];

export const BATCH_STATUS_OPTIONS: Record<string, { label: string; color: string }> = {
    queued: { label: "Na Fila", color: "text-amber-400 bg-amber-500/10 border-amber-500/30" },
    running: { label: "Processando", color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30" },
    completed: { label: "Concluído", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" },
    cancelled: { label: "Cancelado", color: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30" },
    failed: { label: "Com Falhas", color: "text-rose-400 bg-rose-500/10 border-rose-500/30" },
};

export interface NumberSelectOption {
    value: number;
    label: string;
}

export const SCRAPING_PAGES_OPTIONS: NumberSelectOption[] = [
    { value: 1, label: "1 página" },
    { value: 2, label: "2 páginas" },
    { value: 3, label: "3 páginas" },
    { value: 5, label: "5 páginas" },
    { value: 10, label: "10 páginas" },
    { value: 20, label: "20 páginas" },
    { value: 50, label: "50 páginas" },
    { value: 100, label: "Todas as páginas" },
];
