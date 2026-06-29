import { useState } from "react";
import styles from "./Templates.module.css";

interface Template {
    id: number;
    name: string;
    content: string;
    default_budget: number | null;
    default_deadline_days: number | null;
    is_default: boolean;
}

const defaultTemplates: Template[] = [
    {
        id: 1,
        name: "Proposta Geral",
        content: `Olá {nome_cliente}!

Vi o seu projeto "{titulo_projeto}" e fiquei muito interessado em participar.

Tenho {anos_experiencia} anos de experiência em desenvolvimento de software e já trabalhei em projetos similares. Posso entregar um trabalho de qualidade dentro do prazo estabelecido.

Minha proposta:
- Valor: R$ {valor}
- Prazo: {prazo} dias
- Entregas parciais para acompanhamento do progresso

Estou à disposição para discutir os detalhes do projeto.

Atenciosamente!`,
        default_budget: 2000,
        default_deadline_days: 15,
        is_default: true,
    },
    {
        id: 2,
        name: "Desenvolvimento Web",
        content: `Olá!

Sou desenvolvedor web full-stack com experiência em React, Node.js, Python e outras tecnologias modernas.

Para o projeto "{titulo_projeto}", posso oferecer:
✅ Código limpo e bem documentado
✅ Testes automatizados
✅ Deploy em produção
✅ Suporte pós-entrega

Prazo estimado: {prazo} dias
Investimento: R$ {valor}

Podemos agendar uma call para discutir os detalhes?`,
        default_budget: 3000,
        default_deadline_days: 20,
        is_default: false,
    },
];

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>(defaultTemplates);
    const [showNewForm, setShowNewForm] = useState(false);
    const [newTemplate, setNewTemplate] = useState<Partial<Template>>({
        name: "",
        content: "",
        default_budget: null,
        default_deadline_days: null,
        is_default: false,
    });

    const handleSave = () => {
        if (newTemplate.name && newTemplate.content) {
            const template: Template = {
                id: Date.now(),
                name: newTemplate.name,
                content: newTemplate.content,
                default_budget: newTemplate.default_budget || null,
                default_deadline_days: newTemplate.default_deadline_days || null,
                is_default: newTemplate.is_default || false,
            };
            setTemplates([...templates, template]);
            setNewTemplate({
                name: "",
                content: "",
                default_budget: null,
                default_deadline_days: null,
                is_default: false,
            });
            setShowNewForm(false);
        }
    };

    const handleDelete = (id: number) => {
        setTemplates(templates.filter(t => t.id !== id));
    };

    const handleSetDefault = (id: number) => {
        setTemplates(templates.map(t => ({
            ...t,
            is_default: t.id === id,
        })));
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className="page-header">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="page-title">
                            <span className="text-gradient">Propostas Inteligentes</span>
                        </h1>
                        <p className="page-subtitle">
                            Crie e gerencie propostas inteligentes para enviar mais rapidamente
                        </p>
                    </div>
                    <button
                        className="btn btn-primary"
                        onClick={() => setShowNewForm(true)}
                    >
                        <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 5v14M5 12h14" />
                        </svg>
                        Nova Proposta
                    </button>
                </div>
            </div>

            {/* Variáveis disponíveis */}
            <div className={`card ${styles.variablesCard}`}>
                <h3 className="card-title">Variáveis Disponíveis</h3>
                <p className={styles.variablesDescription}>
                    Use estas variáveis nas suas propostas. Elas serão substituídas automaticamente ao preencher a proposta.
                </p>
                <div className={styles.variablesList}>
                    <code>{"{nome_cliente}"}</code>
                    <code>{"{titulo_projeto}"}</code>
                    <code>{"{valor}"}</code>
                    <code>{"{prazo}"}</code>
                    <code>{"{anos_experiencia}"}</code>
                    <code>{"{data_atual}"}</code>
                </div>
            </div>

            {/* Novo Template Form */}
            {showNewForm && (
                <div className={`card ${styles.newTemplateCard}`}>
                    <div className="card-header">
                        <h3 className="card-title">Nova Proposta</h3>
                        <button
                            className="btn btn-ghost btn-icon"
                            onClick={() => setShowNewForm(false)}
                        >
                            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M18 6L6 18M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    <div className={styles.formGrid}>
                        <div className="form-group">
                            <label className="form-label">Nome da Proposta *</label>
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Ex: Proposta para E-commerce"
                                value={newTemplate.name}
                                onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Orçamento Padrão (R$)</label>
                            <input
                                type="number"
                                className="form-input"
                                placeholder="2000"
                                value={newTemplate.default_budget || ""}
                                onChange={(e) => setNewTemplate({ ...newTemplate, default_budget: Number(e.target.value) || null })}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Prazo Padrão (dias)</label>
                            <input
                                type="number"
                                className="form-input"
                                placeholder="15"
                                value={newTemplate.default_deadline_days || ""}
                                onChange={(e) => setNewTemplate({ ...newTemplate, default_deadline_days: Number(e.target.value) || null })}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Conteúdo da Proposta *</label>
                        <textarea
                            className="form-textarea"
                            rows={10}
                            placeholder="Digite sua proposta aqui. Use as variáveis disponíveis..."
                            value={newTemplate.content}
                            onChange={(e) => setNewTemplate({ ...newTemplate, content: e.target.value })}
                        />
                    </div>

                    <div className={styles.formActions}>
                        <button className="btn btn-secondary" onClick={() => setShowNewForm(false)}>
                            Cancelar
                        </button>
                        <button className="btn btn-primary" onClick={handleSave}>
                            Salvar Proposta
                        </button>
                    </div>
                </div>
            )}

            {/* Lista de Templates */}
            <div className={styles.templatesList}>
                {templates.map((template) => (
                    <div
                        key={template.id}
                        className={`card ${styles.templateCard} ${template.is_default ? styles.defaultTemplate : ""}`}
                    >
                        <div className={styles.templateHeader}>
                            <div>
                                <h3 className={styles.templateName}>
                                    {template.name}
                                    {template.is_default && (
                                        <span className="badge badge-success">Padrão</span>
                                    )}
                                </h3>
                                <div className={styles.templateMeta}>
                                    {template.default_budget && (
                                        <span>R$ {template.default_budget.toLocaleString()}</span>
                                    )}
                                    {template.default_deadline_days && (
                                        <span>{template.default_deadline_days} dias</span>
                                    )}
                                </div>
                            </div>
                            <div className={styles.templateActions}>
                                {!template.is_default && (
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => handleSetDefault(template.id)}
                                    >
                                        Definir Padrão
                                    </button>
                                )}
                                <button className="btn btn-ghost btn-sm">
                                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                    </svg>
                                    Editar
                                </button>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => handleDelete(template.id)}
                                    style={{ color: 'var(--color-error)' }}
                                >
                                    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polyline points="3 6 5 6 21 6" />
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <pre className={styles.templateContent}>{template.content}</pre>
                    </div>
                ))}
            </div>

            {templates.length === 0 && !showNewForm && (
                <div className="card">
                    <div className="empty-state">
                        <svg className="empty-state-icon" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                            <path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2" />
                        </svg>
                        <h3 className="empty-state-title">Nenhum template criado</h3>
                        <p className="empty-state-description">
                            Crie templates para agilizar o envio de propostas
                        </p>
                        <button
                            className="btn btn-primary mt-lg"
                            onClick={() => setShowNewForm(true)}
                        >
                            Criar Primeiro Template
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
