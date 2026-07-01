import { useState, useEffect } from "react";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import {
    Plus, Trash2, Copy, MoveUp, MoveDown, Eye, Play, Sparkles, Check, CheckSquare,
    AlertTriangle, FileText, Settings, X, ChevronRight, Info, Award, ArrowLeft, Save
} from "lucide-react";
import { api, TemplateBlock, ProposalTemplate as Template } from "../services/api";
import { useToast } from "../context/ToastContext";
import styles from "./Templates.module.css";
import Loader from "../components/Loader";

const BLOCK_CATALOG = [
    { type: "abertura", label: "Abertura", description: "Saudação inicial e introdução", icon: FileText, defaultContent: "Olá {nome_cliente}! Vi o seu projeto e me interessei." },
    { type: "tom_de_voz", label: "Tom de Voz", description: "Orientações sobre a postura da IA", icon: Sparkles, defaultContent: "Adote um tom profissional, amigável e confiante. Destaque-se sem ser arrogante." },
    { type: "entendimento_projeto", label: "Entendimento do Projeto", description: "Demonstração de que leu o briefing", icon: Info, defaultContent: "Mostre que compreendeu que o objetivo do projeto é {titulo_projeto}." },
    { type: "solucao", label: "Solução Proposta", description: "Como pretende resolver o problema", icon: CheckSquare, defaultContent: "Proponha uma solução modular com foco em escalabilidade, código limpo e arquitetura moderna." },
    { type: "experiencia", label: "Experiência/Portfolio", description: "Sua bagagem e relevância", icon: Award, defaultContent: "Mencione experiência sólida de {anos_experiencia} anos em desenvolvimento." },
    { type: "entregas", label: "Entregas", description: "Fases ou marcos do projeto", icon: Check, defaultContent: "O projeto será entregue em etapas claras com acompanhamento contínuo." },
    { type: "diferenciais", label: "Diferenciais", description: "Por que escolher você?", icon: Sparkles, defaultContent: "Garantia de suporte pós-entrega e comprometimento com prazos." },
    { type: "preco_prazo", label: "Preço/Prazo", description: "Alinhamento de valores e tempo", icon: Info, defaultContent: "Valor proposto: R$ {valor} com prazo de entrega estimado em {prazo} dias." },
    { type: "cta", label: "Chamada para Ação (CTA)", description: "Passo seguinte (agendar conversa)", icon: ChevronRight, defaultContent: "Podemos agendar uma breve conversa para detalhar o escopo?" },
    { type: "assinatura", label: "Assinatura", description: "Encerramento formal", icon: FileText, defaultContent: "Atenciosamente,\n[Seu Nome]" },
    { type: "instrucao_personalizada", label: "Instrução Personalizada", description: "Texto ou orientação livre", icon: Settings, defaultContent: "Oriente a IA a incluir detalhes sobre..." }
] as const;

export default function TemplatesPage() {
    const { toast } = useToast();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
    const [activeTab, setActiveTab] = useState<"list" | "edit">("list");
    
    // Abas de edição mobile
    const [mobileTab, setMobileTab] = useState<"general" | "catalog" | "canvas" | "preview">("canvas");
    
    // Abas do painel lateral (Desktop)
    const [rightPanelTab, setRightPanelTab] = useState<"block-config" | "preview" | "simulate">("block-config");
    
    // Bloco selecionado para edição no painel lateral
    const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
    
    // Dados para compilação/simulação
    const [compiledPrompt, setCompiledPrompt] = useState<string>("");
    const [isCompiling, setIsCompiling] = useState(false);
    
    // Estado para teste IA
    const [mockProject, setMockProject] = useState({
        title: "E-commerce Completo com Next.js",
        description: "Preciso de um desenvolvedor para criar um e-commerce integrado com meios de pagamento, painel administrativo e sistema de estoque.",
        skills: "React, Next.js, Node.js, PostgreSQL",
        budget: "R$ 4.000 - 8.000",
        client_name: "Guilherme"
    });
    const [isSimulatingAi, setIsSimulatingAi] = useState(false);
    const [simulatedResult, setSimulatedResult] = useState<{
        success: boolean;
        proposal?: string;
        suggested_price?: string;
        justification?: string;
        error?: string;
    } | null>(null);

    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

    // Carregar templates
    const loadTemplates = async () => {
        setIsLoading(true);
        try {
            const res = await api.getTemplates();
            // Garantir que cada template venha com blueprint estruturado
            const parsed = res.map((t: any) => ({
                ...t,
                blueprint: t.blueprint || []
            }));
            setTemplates(parsed);
        } catch (error: any) {
            toast.error("Erro ao carregar templates.");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadTemplates();
    }, []);

    // Confirmar saída se houver alterações não salvas
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = "Você tem alterações não salvas. Deseja realmente sair?";
            }
        };
        window.addEventListener("beforeunload", handleBeforeUnload);
        return () => window.removeEventListener("beforeunload", handleBeforeUnload);
    }, [hasUnsavedChanges]);

    const handleCreateNewTemplate = () => {
        const newTemp: Template = {
            id: 0,
            name: "Novo Blueprint de Template",
            content: "",
            blueprint: [
                { id: `block_${Date.now()}_1`, type: "abertura", mode: "literal", enabled: true, content: "Olá {nome_cliente}!" },
                { id: `block_${Date.now()}_2`, type: "solucao", mode: "instruction", enabled: true, content: "Proponha soluções baseadas em tecnologia moderna." },
                { id: `block_${Date.now()}_3`, type: "cta", mode: "literal", enabled: true, content: "Vamos conversar?" }
            ],
            schema_version: 1,
            default_budget: null,
            default_deadline_days: null,
            is_default: false
        };
        setEditingTemplate(newTemp);
        setSelectedBlockId(newTemp.blueprint[0]?.id || null);
        setActiveTab("edit");
        setHasUnsavedChanges(true);
    };

    const handleEditTemplate = (template: Template) => {
        setEditingTemplate(JSON.parse(JSON.stringify(template))); // Deep clone
        setSelectedBlockId(template.blueprint[0]?.id || null);
        setActiveTab("edit");
        setHasUnsavedChanges(false);
    };

    const handleDeleteTemplate = async (template: Template) => {
        if (template.id === null) return;
        if (template.is_default) {
            toast.warning("Você não pode excluir o template padrão diretamente. Defina outro template como padrão primeiro.");
            return;
        }
        if (!window.confirm(`Deseja realmente excluir o template "${template.name}"?`)) {
            return;
        }
        try {
            await api.deleteTemplate(template.id);
            toast.success("Template removido com sucesso!");
            loadTemplates();
        } catch (error: any) {
            toast.error("Erro ao excluir template.");
        }
    };

    const handleViewSystemTemplate = (template: Template) => {
        setEditingTemplate(template);
        setActiveTab("edit");
    };

    const handleDuplicateSystemTemplate = async (template: Template) => {
        try {
            const slug = template.template_ref?.split(":")[1] || "workana-consultivo";
            const response = await api.duplicateTemplate(slug);
            toast.success("Template oficial duplicado com sucesso!");
            loadTemplates();
            setEditingTemplate(response);
            setActiveTab("edit");
        } catch (error) {
            toast.error("Erro ao duplicar template.");
        }
    };

    const handleSetDefaultTemplate = async (id: number | null) => {
        if (id === null) return;
        // Encontrar o template
        const target = templates.find(t => t.id === id);
        if (!target) return;
        try {
            const updated = { ...target, is_default: true };
            await api.updateTemplate(id, updated);
            toast.success(`"${target.name}" definido como padrão!`);
            loadTemplates();
        } catch (error) {
            toast.error("Erro ao definir template padrão.");
        }
    };

    // Salvar template
    const handleSaveTemplate = async () => {
        if (!editingTemplate) return;
        if (editingTemplate.is_system) {
            toast.error("Templates oficiais do sistema não podem ser editados.");
            return;
        }
        if (!editingTemplate.name.trim()) {
            toast.error("O nome do template é obrigatório.");
            return;
        }
        try {
            const payload = {
                name: editingTemplate.name,
                blueprint: editingTemplate.blueprint,
                default_budget: editingTemplate.default_budget,
                default_deadline_days: editingTemplate.default_deadline_days,
                is_default: editingTemplate.is_default,
                schema_version: 1
            };
            if (editingTemplate.id === 0) {
                await api.createTemplate(payload);
                toast.success("Template criado com sucesso!");
            } else {
                await api.updateTemplate(editingTemplate.id!, payload);
                toast.success("Template atualizado com sucesso!");
            }
            setHasUnsavedChanges(false);
            setActiveTab("list");
            loadTemplates();
        } catch (error: any) {
            toast.error("Erro ao salvar o template.");
        }
    };

    const handleAddBlock = (catalogBlock: typeof BLOCK_CATALOG[number]) => {
        if (!editingTemplate || editingTemplate.is_system) return;
        const newBlock: TemplateBlock = {
            id: `block_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
            type: catalogBlock.type,
            mode: "instruction",
            enabled: true,
            content: catalogBlock.defaultContent
        };
        const updatedBlueprint = [...editingTemplate.blueprint, newBlock];
        setEditingTemplate({
            ...editingTemplate,
            blueprint: updatedBlueprint
        });
        setSelectedBlockId(newBlock.id);
        setHasUnsavedChanges(true);
        toast.success(`Bloco "${catalogBlock.label}" adicionado ao canvas.`);
    };

    const handleDuplicateBlock = (block: TemplateBlock) => {
        if (!editingTemplate) return;
        const index = editingTemplate.blueprint.findIndex(b => b.id === block.id);
        if (index === -1) return;
        const newBlock: TemplateBlock = {
            ...block,
            id: `block_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        };
        const updatedBlueprint = [...editingTemplate.blueprint];
        updatedBlueprint.splice(index + 1, 0, newBlock);
        setEditingTemplate({
            ...editingTemplate,
            blueprint: updatedBlueprint
        });
        setSelectedBlockId(newBlock.id);
        setHasUnsavedChanges(true);
        toast.success("Bloco duplicado com sucesso.");
    };

    const handleRemoveBlock = (blockId: string) => {
        if (!editingTemplate) return;
        const updatedBlueprint = editingTemplate.blueprint.filter(b => b.id !== blockId);
        setEditingTemplate({
            ...editingTemplate,
            blueprint: updatedBlueprint
        });
        if (selectedBlockId === blockId) {
            setSelectedBlockId(updatedBlueprint[0]?.id || null);
        }
        setHasUnsavedChanges(true);
        toast.success("Bloco removido.");
    };

    const handleMoveBlock = (blockId: string, direction: "up" | "down") => {
        if (!editingTemplate) return;
        const index = editingTemplate.blueprint.findIndex(b => b.id === blockId);
        if (index === -1) return;
        if (direction === "up" && index === 0) return;
        if (direction === "down" && index === editingTemplate.blueprint.length - 1) return;

        const updatedBlueprint = [...editingTemplate.blueprint];
        const targetIndex = direction === "up" ? index - 1 : index + 1;
        const temp = updatedBlueprint[index];
        updatedBlueprint[index] = updatedBlueprint[targetIndex];
        updatedBlueprint[targetIndex] = temp;

        setEditingTemplate({
            ...editingTemplate,
            blueprint: updatedBlueprint
        });
        setHasUnsavedChanges(true);
    };

    // Drag and drop reordering
    const onDragEnd = (result: DropResult) => {
        if (!result.destination || !editingTemplate || editingTemplate.is_system) return;
        const reordered = Array.from(editingTemplate.blueprint);
        const [removed] = reordered.splice(result.source.index, 1);
        reordered.splice(result.destination.index, 0, removed);

        setEditingTemplate({
            ...editingTemplate,
            blueprint: reordered
        });
        setHasUnsavedChanges(true);
    };

    // Compilar blueprint
    const handleUpdatePreview = async () => {
        if (!editingTemplate) return;
        setIsCompiling(true);
        try {
            const skillsArr = mockProject.skills.split(",").map(s => s.trim());
            const projectPayload = {
                title: mockProject.title,
                description: mockProject.description,
                skills: skillsArr,
                budget: mockProject.budget,
                client_name: mockProject.client_name
            };
            const response = await api.testBlueprint({
                blueprint: editingTemplate.blueprint,
                project: projectPayload,
                run_ai: false
            });
            if (response.success) {
                setCompiledPrompt(response.compiled_prompt);
            } else {
                toast.error("Erro ao compilar blueprint.");
            }
        } catch (error) {
            toast.error("Erro de conexão ao gerar prévia.");
        } finally {
            setIsCompiling(false);
        }
    };

    // Simular com IA
    const handleSimulateAi = async () => {
        if (!editingTemplate) return;
        setIsSimulatingAi(true);
        setSimulatedResult(null);
        try {
            const skillsArr = mockProject.skills.split(",").map(s => s.trim());
            const projectPayload = {
                title: mockProject.title,
                description: mockProject.description,
                skills: skillsArr,
                budget: mockProject.budget,
                client_name: mockProject.client_name
            };
            const response = await api.testBlueprint({
                blueprint: editingTemplate.blueprint,
                project: projectPayload,
                run_ai: true
            });
            setSimulatedResult(response.ai_result || { success: false, error: response.error || "Erro desconhecido" });
        } catch (error: any) {
            setSimulatedResult({ success: false, error: error.message || "Erro de conexão ao simular." });
        } finally {
            setIsSimulatingAi(false);
        }
    };

    // Trigger preview when right panel tab or editing template updates
    useEffect(() => {
        if (editingTemplate && (rightPanelTab === "preview" || mobileTab === "preview")) {
            handleUpdatePreview();
        }
    }, [rightPanelTab, mobileTab]);

    const activeBlock = editingTemplate?.blueprint.find(b => b.id === selectedBlockId);

    const getIconComponent = (type: string) => {
        const item = BLOCK_CATALOG.find(c => c.type === type);
        return item ? item.icon : FileText;
    };

    const getBlockLabel = (type: string) => {
        const item = BLOCK_CATALOG.find(c => c.type === type);
        return item ? item.label : type;
    };

    return (
        <div className={styles.container}>
            {activeTab === "list" ? (
                <>
                    {/* List View Header */}
                    <div className="page-header flex justify-between items-center mb-lg">
                        <div>
                            <h1 className="page-title">
                                <span className="text-gradient">Editor de Blueprints</span>
                            </h1>
                            <p className="page-subtitle">
                                Monte e organize peças inteligentes para estruturar suas propostas de IA
                            </p>
                        </div>
                        <button className="btn btn-primary" onClick={handleCreateNewTemplate}>
                            <Plus size={16} style={{ marginRight: '8px' }} />
                            Criar Blueprint
                        </button>
                    </div>

                    {isLoading ? (
                        <div style={{ padding: '60px' }}>
                            <Loader type="scanning" message="Carregando seus blueprints..." />
                        </div>
                    ) : templates.length === 0 ? (
                        <div className="card">
                            <div className="empty-state">
                                <FileText className="empty-state-icon" />
                                <h3 className="empty-state-title">Nenhum blueprint de template</h3>
                                <p className="empty-state-description">
                                    Crie seu primeiro blueprint para estruturar propostas inteligentes sob medida.
                                </p>
                                <button className="btn btn-primary mt-lg" onClick={handleCreateNewTemplate}>
                                    Criar Primeiro Blueprint
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.templatesGrid}>
                            {templates.map(template => (
                                <div
                                    key={template.id}
                                    className={`card ${styles.templateCard} ${template.is_default ? styles.defaultTemplate : ""}`}
                                >
                                    <div className={styles.templateHeader}>
                                        <div>
                                            <h3 className={styles.templateName}>
                                                {template.name}
                                                {template.is_system && (
                                                    <span className="badge badge-primary" style={{ marginLeft: '8px', background: 'var(--color-primary)', color: 'white', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px' }}>Oficial</span>
                                                )}
                                                {template.is_default && (
                                                    <span className="badge badge-success">Padrão da Automação</span>
                                                )}
                                            </h3>
                                            <div className={styles.templateMeta}>
                                                {template.default_budget && (
                                                    <span>Min Budget: R$ {template.default_budget}</span>
                                                )}
                                                {template.default_deadline_days && (
                                                    <span>Prazo: {template.default_deadline_days} dias</span>
                                                )}
                                                <span>Peças: {template.blueprint.length}</span>
                                            </div>
                                        </div>
                                        <div className={styles.templateActions}>
                                            {!template.is_default && !template.is_system && (
                                                <button
                                                    className="btn btn-ghost btn-sm"
                                                    onClick={() => handleSetDefaultTemplate(template.id)}
                                                >
                                                    Definir Padrão
                                                </button>
                                            )}
                                            {template.is_system ? (
                                                <>
                                                    <button
                                                        className="btn btn-ghost btn-sm"
                                                        onClick={() => handleViewSystemTemplate(template)}
                                                    >
                                                        Visualizar
                                                    </button>
                                                    <button
                                                        className="btn btn-ghost btn-sm"
                                                        onClick={() => handleDuplicateSystemTemplate(template)}
                                                    >
                                                        Duplicar
                                                    </button>
                                                </>
                                            ) : (
                                                <>
                                                    <button
                                                        className="btn btn-ghost btn-sm"
                                                        onClick={() => handleEditTemplate(template)}
                                                    >
                                                        Editar Blueprint
                                                    </button>
                                                    <button
                                                        className="btn btn-ghost btn-sm"
                                                        onClick={() => handleDeleteTemplate(template)}
                                                        style={{ color: 'var(--color-error)' }}
                                                    >
                                                        Excluir
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <div className={styles.blueprintFlowPreview}>
                                        {template.blueprint.map((b, i) => {
                                            const Icon = getIconComponent(b.type);
                                            return (
                                                <div key={b.id} className={styles.previewFlowBlock}>
                                                    <Icon size={14} />
                                                    <span>{getBlockLabel(b.type)}</span>
                                                    {i < template.blueprint.length - 1 && <ChevronRight size={12} className={styles.arrow} />}
                                                </div>
                                            );
                                        })}
                                        {template.blueprint.length === 0 && (
                                            <span style={{ color: 'var(--color-text-muted)' }}>Blueprint vazio</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            ) : (
                /* Editor View */
                <div className={styles.editorContainer}>
                    {/* Header */}
                    <div className={styles.editorHeader}>
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => {
                                if (hasUnsavedChanges && !window.confirm("Deseja sair sem salvar as alterações?")) {
                                    return;
                                }
                                setHasUnsavedChanges(false);
                                setActiveTab("list");
                            }}
                            style={{ paddingLeft: 0 }}
                        >
                            <ArrowLeft size={16} style={{ marginRight: '8px' }} />
                            Voltar para Lista
                        </button>
                        <div className="flex justify-between items-center w-full mt-sm">
                            <div className="flex items-center gap-sm">
                                <input
                                    type="text"
                                    className={`${styles.templateNameInput}`}
                                    value={editingTemplate?.name || ""}
                                    onChange={e => {
                                        if (editingTemplate) {
                                            setEditingTemplate({ ...editingTemplate, name: e.target.value });
                                            setHasUnsavedChanges(true);
                                        }
                                    }}
                                    placeholder="Nome do Template Blueprint"
                                    disabled={editingTemplate?.is_system}
                                />
                                {hasUnsavedChanges && (
                                    <span className={styles.unsavedBadge}>
                                        <AlertTriangle size={14} />
                                        Alterações Não Salvas
                                    </span>
                                )}
                            </div>
                            {editingTemplate?.is_system ? (
                                <button className="btn btn-primary" onClick={() => handleDuplicateSystemTemplate(editingTemplate)}>
                                    <Copy size={16} style={{ marginRight: '8px' }} />
                                    Duplicar para Editar
                                </button>
                            ) : (
                                <button className="btn btn-primary" onClick={handleSaveTemplate}>
                                    <Save size={16} style={{ marginRight: '8px' }} />
                                    Salvar Blueprint
                                </button>
                            )}
                        </div>
                    </div>

                    {editingTemplate?.is_system && (
                        <div style={{
                            background: 'rgba(99, 102, 241, 0.1)',
                            border: '1px solid var(--color-primary)',
                            color: 'var(--color-primary)',
                            padding: '12px 16px',
                            borderRadius: '8px',
                            marginBottom: '16px',
                            fontSize: '0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                        }}>
                            <Info size={16} />
                            <span>Você está visualizando o template oficial de alta conversão. Ele é protegido e não pode ser editado. Para fazer alterações, clique em "Duplicar para Editar".</span>
                        </div>
                    )}

                    {/* Mobile Tabs */}
                    <div className={styles.mobileTabs}>
                        <button
                            className={mobileTab === "general" ? styles.activeMobileTab : ""}
                            onClick={() => setMobileTab("general")}
                        >
                            Geral
                        </button>
                        <button
                            className={mobileTab === "catalog" ? styles.activeMobileTab : ""}
                            onClick={() => setMobileTab("catalog")}
                        >
                            Catálogo
                        </button>
                        <button
                            className={mobileTab === "canvas" ? styles.activeMobileTab : ""}
                            onClick={() => setMobileTab("canvas")}
                        >
                            Canvas ({editingTemplate?.blueprint.length})
                        </button>
                        <button
                            className={mobileTab === "preview" ? styles.activeMobileTab : ""}
                            onClick={() => {
                                setMobileTab("preview");
                                if (rightPanelTab === "block-config") {
                                    setRightPanelTab("preview");
                                }
                            }}
                        >
                            Prévia/Simular
                        </button>
                    </div>

                    {/* Desktop Three-Column Workspace */}
                    <div className={styles.workspaceGrid}>
                        {/* Section 1: General Info & Catalog */}
                        <div className={`${styles.workspaceColumn} ${mobileTab === "catalog" || mobileTab === "general" ? styles.columnVisibleMobile : ""}`}>
                            
                            {/* General Parameters */}
                            <div className={`card mb-md ${mobileTab === "general" ? "" : styles.hideMobile}`}>
                                <h3 className={styles.columnTitle}>Parâmetros Gerais</h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                                    <div className="form-group">
                                        <label className="form-label">Orçamento Mínimo Padrão (R$)</label>
                                        <input
                                            type="number"
                                            className="form-input"
                                            placeholder="Ex: 2000"
                                            value={editingTemplate?.default_budget || ""}
                                            onChange={e => {
                                                if (editingTemplate) {
                                                    setEditingTemplate({
                                                        ...editingTemplate,
                                                        default_budget: e.target.value ? Number(e.target.value) : null
                                                    });
                                                    setHasUnsavedChanges(true);
                                                }
                                            }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Prazo Padrão (Dias)</label>
                                        <input
                                            type="number"
                                            className="form-input"
                                            placeholder="Ex: 15"
                                            value={editingTemplate?.default_deadline_days || ""}
                                            onChange={e => {
                                                if (editingTemplate) {
                                                    setEditingTemplate({
                                                        ...editingTemplate,
                                                        default_deadline_days: e.target.value ? Number(e.target.value) : null
                                                    });
                                                    setHasUnsavedChanges(true);
                                                }
                                            }}
                                        />
                                    </div>
                                    <label className="checkbox-container">
                                        <input
                                            type="checkbox"
                                            checked={editingTemplate?.is_default || false}
                                            onChange={e => {
                                                if (editingTemplate) {
                                                    setEditingTemplate({
                                                        ...editingTemplate,
                                                        is_default: e.target.checked
                                                    });
                                                    setHasUnsavedChanges(true);
                                                }
                                            }}
                                        />
                                        <span className="checkbox-label">Definir como padrão da Automação</span>
                                    </label>
                                </div>
                            </div>

                            {/* Catalog */}
                            <div className={`card ${mobileTab === "catalog" ? "" : styles.hideMobile}`}>
                                <h3 className={styles.columnTitle}>Catálogo de Peças</h3>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
                                    Clique nas peças abaixo para adicioná-las ao seu blueprint de propostas.
                                </p>
                                <div className={styles.catalogList}>
                                    {BLOCK_CATALOG.map(c => {
                                        const Icon = c.icon;
                                        return (
                                            <button
                                                key={c.type}
                                                className={styles.catalogItem}
                                                onClick={() => handleAddBlock(c)}
                                            >
                                                <div className={styles.catalogIconWrapper}>
                                                    <Icon size={16} />
                                                </div>
                                                <div style={{ textAlign: 'left' }}>
                                                    <div className={styles.catalogLabel}>{c.label}</div>
                                                    <div className={styles.catalogDesc}>{c.description}</div>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Section 2: Canvas (Drag and Drop List) */}
                        <div className={`${styles.workspaceColumn} ${styles.canvasColumn} ${mobileTab === "canvas" ? styles.columnVisibleMobile : ""}`}>
                            <div className="card h-full flex flex-col">
                                <div className="flex justify-between items-center mb-md">
                                    <h3 className={styles.columnTitle}>Canvas de Montagem</h3>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                                        {editingTemplate?.blueprint.length} peças ativas
                                    </span>
                                </div>
                                <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
                                    Arraste para reordenar a estrutura ou selecione para configurar.
                                </p>

                                <DragDropContext onDragEnd={onDragEnd}>
                                    <Droppable droppableId="blueprint-canvas" isDropDisabled={editingTemplate?.is_system}>
                                        {(provided, snapshot) => (
                                            <div
                                                ref={provided.innerRef}
                                                {...provided.droppableProps}
                                                className={`${styles.canvasDropzone} ${snapshot.isDraggingOver ? styles.dragOver : ""}`}
                                            >
                                                {editingTemplate?.blueprint.map((block, index) => {
                                                    const Icon = getIconComponent(block.type);
                                                    const isSelected = selectedBlockId === block.id;

                                                    return (
                                                        <Draggable key={block.id} draggableId={block.id} index={index} isDragDisabled={editingTemplate?.is_system}>
                                                            {(providedDrag, snapshotDrag) => (
                                                                <div
                                                                    ref={providedDrag.innerRef}
                                                                    {...providedDrag.draggableProps}
                                                                    {...providedDrag.dragHandleProps}
                                                                    style={providedDrag.draggableProps.style as React.CSSProperties}
                                                                    onClick={() => {
                                                                        setSelectedBlockId(block.id);
                                                                        setMobileTab("preview");
                                                                        setRightPanelTab("block-config");
                                                                    }}
                                                                    className={`${styles.canvasBlock} ${isSelected ? styles.blockSelected : ""} ${!block.enabled ? styles.blockDisabled : ""} ${snapshotDrag.isDragging ? styles.draggingBlock : ""}`}
                                                                >
                                                                    <div className={styles.blockDragHandle}>
                                                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                                                            <circle cx="9" cy="5" r="2" />
                                                                            <circle cx="9" cy="12" r="2" />
                                                                            <circle cx="9" cy="19" r="2" />
                                                                            <circle cx="15" cy="5" r="2" />
                                                                            <circle cx="15" cy="12" r="2" />
                                                                            <circle cx="15" cy="19" r="2" />
                                                                        </svg>
                                                                    </div>

                                                                    <div className={styles.blockBody}>
                                                                        <div className="flex justify-between items-center">
                                                                            <div className="flex items-center gap-xs">
                                                                                <Icon size={14} className={styles.blockTypeIcon} />
                                                                                <span className={styles.blockTitle}>{getBlockLabel(block.type)}</span>
                                                                                <span className={styles.blockModeBadge}>
                                                                                    {block.mode === "literal" ? "Literal" : "Instrução"}
                                                                                </span>
                                                                            </div>
                                                                            {!editingTemplate?.is_system && (
                                                                                <div className={styles.blockControls}>
                                                                                    <button
                                                                                        title="Mover para Cima"
                                                                                        onClick={(e) => { e.stopPropagation(); handleMoveBlock(block.id, "up"); }}
                                                                                        disabled={index === 0}
                                                                                        className={styles.controlBtn}
                                                                                    >
                                                                                        <MoveUp size={12} />
                                                                                    </button>
                                                                                    <button
                                                                                        title="Mover para Baixo"
                                                                                        onClick={(e) => { e.stopPropagation(); handleMoveBlock(block.id, "down"); }}
                                                                                        disabled={index === (editingTemplate?.blueprint.length || 0) - 1}
                                                                                        className={styles.controlBtn}
                                                                                    >
                                                                                        <MoveDown size={12} />
                                                                                    </button>
                                                                                    <button
                                                                                        title="Duplicar"
                                                                                        onClick={(e) => { e.stopPropagation(); handleDuplicateBlock(block); }}
                                                                                        className={styles.controlBtn}
                                                                                    >
                                                                                        <Copy size={12} />
                                                                                    </button>
                                                                                    <button
                                                                                        title="Remover"
                                                                                        onClick={(e) => { e.stopPropagation(); handleRemoveBlock(block.id); }}
                                                                                        className={`${styles.controlBtn} ${styles.danger}`}
                                                                                    >
                                                                                        <Trash2 size={12} />
                                                                                    </button>
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                        <div className={styles.blockContentPreview}>
                                                                            {block.content || <span style={{ fontStyle: 'italic', opacity: 0.5 }}>Sem conteúdo</span>}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </Draggable>
                                                    );
                                                })}
                                                {provided.placeholder}
                                                {editingTemplate?.blueprint.length === 0 && (
                                                    <div className={styles.canvasEmptyState}>
                                                        Canvas Vazio. Adicione peças a partir do catálogo lateral.
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </Droppable>
                                </DragDropContext>
                            </div>
                        </div>

                        {/* Section 3: Configuration, Live Preview & Test */}
                        <div className={`${styles.workspaceColumn} ${mobileTab === "preview" ? styles.columnVisibleMobile : ""}`}>
                            
                            {/* Panel Tab Selector */}
                            <div className={styles.rightTabs}>
                                <button
                                    className={rightPanelTab === "block-config" ? styles.activeRightTab : ""}
                                    onClick={() => setRightPanelTab("block-config")}
                                >
                                    Ajustes
                                </button>
                                <button
                                    className={rightPanelTab === "preview" ? styles.activeRightTab : ""}
                                    onClick={() => setRightPanelTab("preview")}
                                >
                                    Prévia Prompt
                                </button>
                                <button
                                    className={rightPanelTab === "simulate" ? styles.activeRightTab : ""}
                                    onClick={() => setRightPanelTab("simulate")}
                                >
                                    Testar IA
                                </button>
                            </div>

                            {/* Panel Tab Contents */}
                            <div className="card h-full">
                                {rightPanelTab === "block-config" && (
                                    <div className={styles.tabContent}>
                                        <h3 className={styles.columnTitle}>Configuração da Peça</h3>
                                        {activeBlock ? (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                                                <div className="form-group">
                                                    <label className="form-label">Nome/Tipo</label>
                                                    <input
                                                        type="text"
                                                        className="form-input"
                                                        value={getBlockLabel(activeBlock.type)}
                                                        disabled
                                                    />
                                                </div>

                                                <div className="form-group">
                                                    <label className="form-label">Modo de Operação</label>
                                                    <div className="flex gap-sm">
                                                        <button
                                                            className={`btn w-full ${activeBlock.mode === "instruction" ? "btn-primary" : "btn-secondary"}`}
                                                            style={{ border: '1px solid var(--color-border)' }}
                                                            disabled={editingTemplate?.is_system}
                                                            onClick={() => {
                                                                if (editingTemplate) {
                                                                    const bp = editingTemplate.blueprint.map(b =>
                                                                        b.id === activeBlock.id ? { ...b, mode: "instruction" as const } : b
                                                                    );
                                                                    setEditingTemplate({ ...editingTemplate, blueprint: bp });
                                                                    setHasUnsavedChanges(true);
                                                                }
                                                            }}
                                                        >
                                                            Instrução
                                                        </button>
                                                        <button
                                                            className={`btn w-full ${activeBlock.mode === "literal" ? "btn-primary" : "btn-secondary"}`}
                                                            style={{ border: '1px solid var(--color-border)' }}
                                                            disabled={editingTemplate?.is_system}
                                                            onClick={() => {
                                                                if (editingTemplate) {
                                                                    const bp = editingTemplate.blueprint.map(b =>
                                                                        b.id === activeBlock.id ? { ...b, mode: "literal" as const } : b
                                                                    );
                                                                    setEditingTemplate({ ...editingTemplate, blueprint: bp });
                                                                    setHasUnsavedChanges(true);
                                                                }
                                                            }}
                                                        >
                                                            Texto Literal
                                                        </button>
                                                    </div>
                                                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem', display: 'block' }}>
                                                        {activeBlock.mode === "instruction"
                                                            ? "A IA recebe o texto como comando para orientar sua redação."
                                                            : "A IA é orientada a injetar esta parte literalmente na proposta."}
                                                    </span>
                                                </div>

                                                <label className="checkbox-container">
                                                    <input
                                                        type="checkbox"
                                                        checked={activeBlock.enabled}
                                                        disabled={editingTemplate?.is_system}
                                                        onChange={(e) => {
                                                            if (editingTemplate) {
                                                                const bp = editingTemplate.blueprint.map(b =>
                                                                    b.id === activeBlock.id ? { ...b, enabled: e.target.checked } : b
                                                                );
                                                                setEditingTemplate({ ...editingTemplate, blueprint: bp });
                                                                setHasUnsavedChanges(true);
                                                            }
                                                        }}
                                                    />
                                                    <span className="checkbox-label">Peça Ativa</span>
                                                </label>

                                                <div className="form-group">
                                                    <label className="form-label">Conteúdo do Bloco</label>
                                                    <textarea
                                                        className="form-textarea"
                                                        rows={12}
                                                        value={activeBlock.content || ""}
                                                        disabled={editingTemplate?.is_system}
                                                        onChange={(e) => {
                                                            if (editingTemplate) {
                                                                const bp = editingTemplate.blueprint.map(b =>
                                                                    b.id === activeBlock.id ? { ...b, content: e.target.value } : b
                                                                );
                                                                setEditingTemplate({ ...editingTemplate, blueprint: bp });
                                                                setHasUnsavedChanges(true);
                                                            }
                                                        }}
                                                        placeholder="Escreva as instruções ou texto literal..."
                                                    />
                                                </div>
                                            </div>
                                        ) : (
                                            <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', padding: '40px 0' }}>
                                                Selecione um bloco no canvas para configurar.
                                            </div>
                                        )}
                                    </div>
                                )}

                                {rightPanelTab === "preview" && (
                                    <div className={styles.tabContent}>
                                        <div className="flex justify-between items-center mb-md">
                                            <h3 className={styles.columnTitle}>Prompt Compilado</h3>
                                            <button className="btn btn-ghost btn-sm" onClick={handleUpdatePreview} disabled={isCompiling}>
                                                Atualizar
                                            </button>
                                        </div>
                                        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
                                            Veja como as peças configuradas acima ficam dispostas e estruturadas no prompt enviado para a IA.
                                        </p>
                                        {isCompiling ? (
                                            <Loader type="scanning" message="Compilando prompt..." />
                                        ) : (
                                            <pre className={styles.promptPreviewContainer}>{compiledPrompt || "Nenhuma prévia gerada."}</pre>
                                        )}
                                    </div>
                                )}

                                {rightPanelTab === "simulate" && (
                                    <div className={styles.tabContent}>
                                        <h3 className={styles.columnTitle}>Simulador de Propostas</h3>
                                        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 'var(--spacing-md)' }}>
                                            Alimente com dados de teste rápidos para ver a IA em ação com o seu blueprint atual.
                                        </p>

                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
                                            <div className="form-group">
                                                <label className="form-label" style={{ fontSize: '0.75rem' }}>Título do Projeto</label>
                                                <input
                                                    type="text"
                                                    className="form-input"
                                                    style={{ padding: '0.4rem' }}
                                                    value={mockProject.title}
                                                    onChange={e => setMockProject({ ...mockProject, title: e.target.value })}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label" style={{ fontSize: '0.75rem' }}>Habilidades Demandadas</label>
                                                <input
                                                    type="text"
                                                    className="form-input"
                                                    style={{ padding: '0.4rem' }}
                                                    value={mockProject.skills}
                                                    onChange={e => setMockProject({ ...mockProject, skills: e.target.value })}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label" style={{ fontSize: '0.75rem' }}>Descrição do Job</label>
                                                <textarea
                                                    className="form-textarea"
                                                    rows={3}
                                                    value={mockProject.description}
                                                    onChange={e => setMockProject({ ...mockProject, description: e.target.value })}
                                                />
                                            </div>
                                        </div>

                                        <button
                                            className="btn btn-primary w-full"
                                            onClick={handleSimulateAi}
                                            disabled={isSimulatingAi}
                                            style={{ gap: '8px' }}
                                        >
                                            {isSimulatingAi ? (
                                                <>
                                                    <span className="spinner spinner-sm"></span>
                                                    Gerando Proposta...
                                                </>
                                            ) : (
                                                <>
                                                    <Play size={14} />
                                                    Simular Geração com IA
                                                </>
                                            )}
                                        </button>

                                        {simulatedResult && (
                                            <div className="mt-md pt-md" style={{ borderTop: '1px solid var(--color-border)', maxHeight: '300px', overflowY: 'auto' }}>
                                                {simulatedResult.success ? (
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
                                                        <div className="card p-3 bg-glass text-center">
                                                            <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>PREÇO SUGERIDO</span>
                                                            <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--color-success)' }}>
                                                                {simulatedResult.suggested_price}
                                                            </div>
                                                        </div>
                                                        <div className="form-group">
                                                            <label className="form-label" style={{ fontSize: '0.75rem' }}>Justificativa do Preço</label>
                                                            <div className={styles.simulationText} style={{ fontSize: '0.8rem' }}>
                                                                {simulatedResult.justification}
                                                            </div>
                                                        </div>
                                                        <div className="form-group">
                                                            <label className="form-label" style={{ fontSize: '0.75rem' }}>Proposta Final da IA</label>
                                                            <textarea
                                                                className="form-textarea"
                                                                rows={8}
                                                                style={{ fontSize: '0.8rem' }}
                                                                value={simulatedResult.proposal}
                                                                readOnly
                                                            />
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="alert alert-error">
                                                        {simulatedResult.error || "Erro de simulação."}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
