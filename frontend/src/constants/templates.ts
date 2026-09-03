/**
 * Definições e constantes para o sistema de Templates e Blueprints.
 */

export interface BlockCatalogItem {
  type: string;
  label: string;
  description: string;
  defaultContent: string;
}

export const BLOCK_CATALOG: BlockCatalogItem[] = [
  {
    type: 'abertura',
    label: 'Abertura & Diagnóstico',
    description: 'Saudação calorosa e diagnóstico técnico de alto nível',
    defaultContent:
      "Cumprimente cordialmente ({nome_cliente}, ou 'Olá, tudo bem?' se não houver nome informado ou for sigla). Demonstre análise minuciosa do escopo ({titulo_projeto}) e estabeleça o objetivo de entregar um MVP funcional, validável e escalável.",
  },
  {
    type: 'entendimento_projeto',
    label: 'Visão do Projeto (🧠)',
    description: 'Objetivo central e pilares de valor do sistema',
    defaultContent:
      "Apresente a seção '🧠 Visão do Projeto' com tópicos objetivos destacando a proposta central de valor, recursos em tempo real, fluidez, segurança e base de crescimento.",
  },
  {
    type: 'solucao',
    label: 'Arquitetura da Solução (📱/⚙️)',
    description: 'Camadas técnicas, stack e decisões de engenharia',
    defaultContent:
      "Apresente a seção '📱 Arquitetura da Solução' dividida em camadas (Frontend/Mobile Multiplataforma e Backend/API com persistência e comunicação em tempo real).",
  },
  {
    type: 'entregas',
    label: 'Escopo de Desenvolvimento (📋)',
    description: 'Módulos temáticos práticos com ícones e bullets',
    defaultContent:
      "Apresente a seção '📋 Escopo de Desenvolvimento' decomposta em 3 a 5 módulos práticos com ícones representativos e 2 a 4 funcionalidades concretas com bullets (•).",
  },
  {
    type: 'preco_prazo',
    label: 'Detalhamento do Investimento (💰)',
    description: 'Fatiamento em 4 etapas lógicas e investimento total',
    defaultContent:
      "Apresente a seção '💰 Detalhamento do Investimento' fatiando em 4 etapas (Planejamento, Frontend, Backend/Integrações, Testes/Entrega) com seus valores proporcionais e '💵 Investimento Total do Projeto' somando exatamente o valor total ({valor}).",
  },
  {
    type: 'diferenciais',
    label: 'Condições (🔄)',
    description: 'Garantias, rodadas de ajustes e segurança',
    defaultContent:
      '🔄 Condições\n\n• MVP focado em validação de mercado\n• Até 2 rodadas de ajustes inclusas\n• Comunicação constante durante o desenvolvimento\n• Código preparado para evolução futura\n• Suporte inicial pós-entrega',
  },
  {
    type: 'cta',
    label: 'Considerações Finais (🎯)',
    description: 'Fechamento executivo e chamada para alinhamento',
    defaultContent:
      '🎯 Considerações Finais\n\nEsta proposta foi pensada para entregar um MVP realista, funcional e tecnicamente sólido, capaz de testar o modelo de negócio com segurança e permitir evolução rápida após a validação.\n\nFico à disposição para alinharmos detalhes técnicos, prazos e próximos passos.',
  },
  {
    type: 'assinatura',
    label: 'Assinatura',
    description: 'Encerramento profissional com seu nome',
    defaultContent: 'Atenciosamente,\n{nome_usuario}',
  },
  {
    type: 'tom_de_voz',
    label: 'Tom de Voz',
    description: 'Orientações sobre a postura consultiva da IA',
    defaultContent:
      'Adote tom de Arquiteto de Software Sênior e parceiro de negócios, claro, objetivo e focado em valor prático.',
  },
  {
    type: 'experiencia',
    label: 'Experiência / Portfolio',
    description: 'Destaque de solidez técnica e boas práticas',
    defaultContent:
      'Destaque foco em código limpo, documentado, arquitetura escalável e comunicação transparente.',
  },
  {
    type: 'instrucao_personalizada',
    label: 'Instrução Personalizada',
    description: 'Diretriz ou texto livre sob medida',
    defaultContent: 'Oriente a IA com requisitos adicionais específicos...',
  },
];

export const TEMPLATE_VARIABLES = [
  {
    tag: '{nome_cliente}',
    label: 'Nome do Cliente',
    description: "Nome público do contratante ou 'Cliente'",
  },
  { tag: '{titulo_projeto}', label: 'Título do Projeto', description: 'Título completo da vaga' },
  { tag: '{descricao_projeto}', label: 'Descrição', description: 'Texto completo do briefing' },
  {
    tag: '{habilidades}',
    label: 'Habilidades',
    description: 'Lista de tags e tecnologias exigidas',
  },
  { tag: '{valor}', label: 'Valor / Orçamento', description: 'Orçamento informado pelo cliente' },
  { tag: '{prazo}', label: 'Prazo', description: 'Prazo estipulado em dias' },
  {
    tag: '{anos_experiencia}',
    label: 'Anos de Experiência',
    description: 'Substituído com sua bagagem profissional',
  },
];
