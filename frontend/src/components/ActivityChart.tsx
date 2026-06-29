import React from 'react';

interface ActivityChartProps {
    data: number[];
    labels: string[];
    color?: string;
    height?: number;
}

export default function ActivityChart({ 
    data, 
    labels, 
    color = 'var(--color-primary)', 
    height = 150 
}: ActivityChartProps) {
    const maxVal = Math.max(...data, 1); // Avoid division by zero
    
    return (
        <div style={{ 
            display: 'flex', 
            alignItems: 'flex-end', 
            justifyContent: 'space-between',
            height: `${height}px`,
            width: '100%',
            padding: '10px 0'
        }}>
            {data.map((value, index) => {
                const heightPercentage = (value / maxVal) * 100;
                
                return (
                    <div key={index} style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center',
                        flex: 1,
                        height: '100%',
                        justifyContent: 'flex-end',
                        gap: '8px'
                    }}>
                        <div 
                            className="chart-bar"
                            style={{ 
                                height: `${heightPercentage}%`,
                                width: '60%',
                                minWidth: '8px',
                                maxWidth: '24px',
                                background: color,
                                borderRadius: '4px',
                                opacity: 0.8,
                                transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                                position: 'relative',
                                cursor: 'crosshair'
                            }}
                            title={`${labels[index]}: ${value}`}
                        >
                             {/* Tooltip on hover could go here via CSS if needed */}
                        </div>
                        <span style={{ 
                            fontSize: '0.75rem', 
                            color: 'var(--color-text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            width: '100%',
                            textAlign: 'center'
                        }}>
                            {labels[index]}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}
