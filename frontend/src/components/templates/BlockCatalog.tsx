import React from "react";
import { Plus } from "lucide-react";
import { BLOCK_CATALOG, BlockCatalogItem } from "../../constants/templates";
import styles from "../../pages/Templates.module.css";

interface BlockCatalogProps {
    isSystem: boolean;
    onAddBlock: (block: BlockCatalogItem) => void;
}

export const BlockCatalog: React.FC<BlockCatalogProps> = ({
    isSystem,
    onAddBlock,
}) => {
    return (
        <div className={styles.catalogPanel}>
            <div className={styles.catalogHeader}>
                <h4>Catálogo de Peças</h4>
                <p>Clique em uma peça para adicioná-la ao seu blueprint</p>
            </div>
            <div className={styles.catalogList}>
                {BLOCK_CATALOG.map((block) => (
                    <div
                        key={block.type}
                        className={`${styles.catalogItem} ${isSystem ? styles.catalogItemDisabled : ""}`}
                        onClick={() => !isSystem && onAddBlock(block)}
                    >
                        <div className={styles.catalogItemContent}>
                            <span className={styles.catalogItemTitle}>{block.label}</span>
                            <span className={styles.catalogItemDesc}>{block.description}</span>
                        </div>
                        <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            disabled={isSystem}
                            aria-label={`Adicionar ${block.label}`}
                        >
                            <Plus size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};
