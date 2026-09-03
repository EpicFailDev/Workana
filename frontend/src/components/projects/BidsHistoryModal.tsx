import React from "react";
import { BidsHistoryResponse } from "../../services/api";
import styles from "../../pages/Projects.module.css";

interface BidsHistoryModalProps {
    data: BidsHistoryResponse | null;
    isLoading: boolean;
    onClose: () => void;
}

export const BidsHistoryModal: React.FC<BidsHistoryModalProps> = ({
    data,
    isLoading,
    onClose,
}) => {
    if (!data && !isLoading) return null;

    const points = data?.points || [];
    const maxCount = Math.max(...points.map((p) => p.proposals_count), 1);

    return (
        <div className={styles.dossierOverlay} onClick={onClose}>
            <div
                className={styles.dossierContainer}
                style={{ maxWidth: "680px" }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className={styles.dossierHeader}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                            <span style={{ color: "var(--color-primary)", fontSize: "0.8rem", letterSpacing: "2px", fontWeight: "bold" }}>
                                HISTÓRICO DE PROPOSTAS // EVOLUÇÃO
                            </span>
                            <h3 style={{ fontSize: "1.2rem", marginTop: "4px", color: "var(--color-text-bright)" }}>
                                {data?.title || `Projeto #${data?.workana_id}`}
                            </h3>
                        </div>
                        <button className={styles.closeButton} onClick={onClose} aria-label="Fechar">
                            ×
                        </button>
                    </div>
                </div>

                <div className={styles.dossierBody} style={{ padding: "1.5rem" }}>
                    {isLoading ? (
                        <div style={{ textAlign: "center", padding: "2rem", color: "var(--color-text-muted)" }}>
                            Carregando histórico de candidaturas...
                        </div>
                    ) : points.length === 0 ? (
                        <div style={{ textAlign: "center", padding: "2rem", color: "var(--color-text-muted)" }}>
                            Nenhum snapshot de candidaturas registrado para este projeto ainda.
                        </div>
                    ) : (
                        <div>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem", fontSize: "0.85rem", color: "var(--color-text-muted)" }}>
                                <span>Contagem atual: <strong style={{ color: "var(--color-primary)" }}>{data?.current_count ?? points[0]?.proposals_count ?? 0} propostas</strong></span>
                                <span>Total de snapshots: <strong>{points.length}</strong></span>
                            </div>

                            {/* Mini visual bar timeline */}
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "320px", overflowY: "auto", paddingRight: "8px" }}>
                                {points.map((p, idx) => {
                                    const pct = Math.round((p.proposals_count / maxCount) * 100);
                                    const dateStr = p.captured_at ? new Date(p.captured_at).toLocaleString("pt-BR") : "Recent";
                                    return (
                                        <div key={idx} style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.8rem" }}>
                                            <span style={{ width: "140px", color: "var(--color-text-muted)", flexShrink: 0, fontFamily: "monospace" }}>
                                                {dateStr}
                                            </span>
                                            <div style={{ flex: 1, background: "rgba(255,255,255,0.05)", borderRadius: "4px", height: "20px", overflow: "hidden", position: "relative" }}>
                                                <div
                                                    style={{
                                                        width: `${Math.max(pct, 5)}%`,
                                                        height: "100%",
                                                        background: "var(--gradient-primary)",
                                                        borderRadius: "4px",
                                                        transition: "width 0.3s ease",
                                                    }}
                                                />
                                                <span style={{ position: "absolute", left: "8px", top: "2px", fontSize: "0.75rem", fontWeight: "bold", color: "#fff" }}>
                                                    {p.proposals_count}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
