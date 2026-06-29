import Skeleton from "./Skeleton";
import styles from "../pages/Projects.module.css";

export default function ProjectSkeleton() {
    return (
        <div className={`m3-card ${styles.projectCard}`} style={{ opacity: 0.7 }}>
            <div className={styles.projectHeader}>
                <Skeleton width="60%" height={24} />
                <Skeleton width="20%" height={24} />
            </div>

            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Skeleton width="100%" height={16} />
                <Skeleton width="90%" height={16} />
                <Skeleton width="40%" height={16} />
            </div>

            <div className={styles.projectSkills} style={{ marginTop: '1.5rem' }}>
                <Skeleton width={60} height={24} borderRadius="12px" />
                <Skeleton width={80} height={24} borderRadius="12px" />
                <Skeleton width={70} height={24} borderRadius="12px" />
            </div>

            <div className={styles.projectFooter}>
                <div className={styles.projectMeta}>
                    <Skeleton width={100} height={14} />
                    <Skeleton width={80} height={14} />
                </div>

                <div className={styles.projectActions}>
                    <Skeleton width={100} height={32} />
                    <Skeleton width={120} height={32} />
                </div>
            </div>
        </div>
    );
}

export function ProjectSkeletonList({ count = 3 }: { count?: number }) {
    return (
        <div className="reveal-grid">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="reveal-item">
                    <ProjectSkeleton />
                </div>
            ))}
        </div>
    );
}
