import React, { useState } from "react";
import styles from "../../pages/Projects.module.css";

interface SaveFilterModalProps {
    isOpen: boolean;
    currentFiltersCount: number;
    onClose: () => void;
    onSave: (filterName: string) => Promise<void>;
}

export const SaveFilterModal: React.FC<SaveFilterModalProps> = ({
    isOpen,
    currentFiltersCount,
    onClose,
    onSave,
}) => {
    const [name, setName] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;
        setIsSaving(true);
        try {
            await onSave(name.trim());
            setName("");
            onClose();
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className={styles.dossierOverlay} onClick={onClose}>
            <div
                className={styles.dossierContainer}
                style={{ maxWidth: "480px" }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className={styles.dossierHeader}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                            <span style={{ color: "var(--color-primary)", fontSize: "0.8rem", letterSpacing: "2px", fontWeight: "bold" }}>
                                PRESET // FILTRO RÁPIDO
                            </span>
                            <h3 style={{ fontSize: "1.2rem", marginTop: "4px", color: "var(--color-text-bright)" }}>
                                Salvar Filtro Atual
                            </h3>
                        </div>
                        <button className={styles.closeButton} onClick={onClose} aria-label="Fechar">
                            ×
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit} style={{ padding: "1.5rem" }}>
                    <p style={{ fontSize: "0.9rem", color: "var(--color-text-muted)", marginBottom: "1rem" }}>
                        Salve esta combinação de filtros para aplicá-la em um único clique no futuro.
                    </p>

                    <div style={{ marginBottom: "1.5rem" }}>
                        <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "6px", color: "var(--color-text-bright)" }}>
                            Nome do Filtro:
                        </label>
                        <input
                            type="text"
                            className="input"
                            style={{ width: "100%" }}
                            placeholder="Ex: TI / Remoto / Pagamento Verificado"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            autoFocus
                            required
                        />
                    </div>

                    <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onClose}
                            disabled={isSaving}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={isSaving || !name.trim()}
                        >
                            {isSaving ? "Salvando..." : "Salvar Filtro"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
