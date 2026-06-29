import React from 'react';
import styles from './CyberHeader.module.css';

interface CyberHeaderProps {
    title: string;
    subtitle: string;
    description?: string;
}

export default function CyberHeader({ title, subtitle, description }: CyberHeaderProps) {
    return (
        <div className={styles.headerContainer}>
            <div className={styles.subtitle}>{subtitle}</div>
            <h1 className={styles.title}>{title}</h1>
            {description && <p className={styles.description}>{description}</p>}
            <div className={styles.decorativeLine} />
        </div>
    );
}
