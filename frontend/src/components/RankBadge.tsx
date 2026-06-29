import React from 'react';
import styles from './RankBadge.module.css';

interface RankBadgeProps {
  tier: string;
  division: string;
  lp?: number;
  showLp?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const TIER_COLORS: Record<string, string> = {
  Ferro: '#a19d94',
  Bronze: '#cd7f32',
  Prata: '#c0c0c0',
  Ouro: '#ffd700',
  Platina: '#e5e4e2',
  Esmeralda: '#50c878',
  Diamante: '#b9f2ff',
  Mestre: '#9d32a8',
  'Grão-Mestre': '#ef4444',
  Desafiante: '#fbbf24',
};

export default function RankBadge({ tier, division, lp = 0, showLp = true, size = 'md' }: RankBadgeProps) {
  const color = TIER_COLORS[tier] || '#fff';

  return (
    <div className={`${styles.badgeContainer} ${styles[size]}`} style={{ '--tier-color': color } as any}>
      <div className={styles.iconWrapper}>
        <svg viewBox="0 0 100 100" className={styles.svg}>
          {/* Hexagonal Base */}
          <path
            d="M50 5 L90 25 L90 75 L50 95 L10 75 L10 25 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={styles.base}
          />
          {/* Inner Glow */}
          <path
            d="M50 15 L80 30 L80 70 L50 85 L20 70 L20 30 Z"
            fill={color}
            fillOpacity="0.2"
            stroke={color}
            strokeWidth="1"
          />
          {/* Rank Symbol (Simplified) */}
          <circle cx="50" cy="50" r="15" fill="none" stroke={color} strokeWidth="4" />
          <path d="M50 35 L50 65 M35 50 L65 50" stroke={color} strokeWidth="4" />
        </svg>
      </div>
      <div className={styles.info}>
        <div className={styles.tierName}>{tier} {division}</div>
        {showLp && <div className={styles.lpText}>{lp} LP</div>}
      </div>
    </div>
  );
}
