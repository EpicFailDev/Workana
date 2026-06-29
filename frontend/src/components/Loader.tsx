import styles from "./Loader.module.css";

interface LoaderProps {
    message?: string;
    type?: "spinner" | "scanning" | "overlay";
}

export default function Loader({ message, type = "spinner" }: LoaderProps) {
    if (type === "overlay") {
        return (
            <div className={styles.loaderOverlay}>
                <div className={styles.liquidSpinner}>
                    <div className={styles.liquidCircle}></div>
                    <div className={styles.liquidCircle}></div>
                    <div className={styles.liquidCircle}></div>
                </div>
                {message && <p className={styles.loaderText}>{message}</p>}
            </div>
        );
    }

    if (type === "scanning") {
        const dummyData = Array(20).fill(0).map(() => Math.random().toString(16).substring(2, 8)).join(' ');

        return (
            <div className={styles.loaderContainer}>
                <div className={styles.scanningContainer}>
                    <div className={styles.scanningGrid}></div>
                    <div className={styles.dataStream}>{dummyData} {dummyData} {dummyData}</div>
                    
                    <div className={styles.radarSweep}></div>
                    <div className={styles.radarCenter}></div>
                    
                    <div className={styles.scanningBar}></div>
                    
                    <div className={styles.targetReticle}>
                        <div className={styles.targetReticleCorner}></div>
                    </div>

                    <div className={styles.scanningContent}>
                        <div className={styles.scanningLine}></div>
                        <div className={styles.scanningLine}></div>
                        <div className={styles.scanningLine}></div>
                    </div>
                </div>
                {message && <p className={styles.loaderText} style={{ letterSpacing: '2px', textTransform: 'uppercase', fontSize: '0.8rem' }}>{message}</p>}
            </div>
        );
    }

    return (
        <div className={styles.loaderContainer}>
            <div className={styles.liquidSpinner}>
                <div className={styles.liquidCircle}></div>
                <div className={styles.liquidCircle}></div>
                <div className={styles.liquidCircle}></div>
            </div>
            {message && <p className={styles.loaderText}>{message}</p>}
        </div>
    );
}
