/**
 * Constantes de categorias e tipos de contrato do Workana.
 */

export interface WorkanaCategory {
    id: string;
    name: string;
    subcategories: string[];
}

export const WORKANA_CATEGORIES: WorkanaCategory[] = [
    {
        id: "ti-programacao",
        name: "TI e Programação",
        subcategories: [
            "Web Development",
            "WordPress",
            "Mobile Apps",
            "E-commerce",
            "Data Science & IA",
            "DevOps & SysAdmin",
            "Game Development",
            "Desktop Apps",
            "Segurança & QA",
        ],
    },
    {
        id: "design-multimidia",
        name: "Design e Multimídia",
        subcategories: [
            "Logo & Identidade Visual",
            "UI/UX Design",
            "Edição de Vídeo",
            "Modelagem 3D",
            "Ilustração",
            "Banners & Social Media",
            "Animação & Motion",
        ],
    },
    {
        id: "traducao-conteudos",
        name: "Tradução e Conteúdos",
        subcategories: [
            "Redação de Artigos",
            "Copywriting",
            "Tradução EN/PT/ES",
            "Revisão de Textos",
            "Ebooks & Ghostwriting",
        ],
    },
    {
        id: "marketing-vendas",
        name: "Marketing e Vendas",
        subcategories: [
            "Gestão de Tráfego (Google/Meta Ads)",
            "SEO & Posicionamento",
            "Social Media Management",
            "Email Marketing",
            "Funil de Vendas",
        ],
    },
    {
        id: "suporte-administrativo",
        name: "Suporte Administrativo",
        subcategories: [
            "Assistência Virtual",
            "Atendimento ao Cliente",
            "Data Entry",
            "Pesquisa de Mercado",
        ],
    },
    {
        id: "juridico-financas",
        name: "Finanças e Jurídico",
        subcategories: [
            "Contabilidade",
            "Consultoria Financeira",
            "Contratos & Termos de Uso",
        ],
    },
    {
        id: "engenharia-manufatura",
        name: "Engenharia e Arquitetura",
        subcategories: [
            "Projetos Arquitetônicos & CAD",
            "Engenharia Civil/Elétrica",
        ],
    },
];

export const CONTRACT_TYPES = [
    { id: "project_fixed", label: "Projeto Fechado (Preço Fixo)" },
    { id: "project_hourly", label: "Por Hora" },
    { id: "unknown", label: "Não Especificado" },
] as const;

export const PROJECT_STATUS_LABELS: Record<string, { label: string; color: string }> = {
    active: { label: "Ativo", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
    gone: { label: "Ausente", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
    closed: { label: "Encerrado", color: "text-zinc-400 border-zinc-500/30 bg-zinc-500/10" },
};
