interface SkeletonProps {
    className?: string;
    width?: string | number;
    height?: string | number;
    borderRadius?: string;
}

export default function Skeleton({ className = "", width, height, borderRadius }: SkeletonProps) {
    const style: React.CSSProperties = {
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius: borderRadius || '8px',
        backgroundColor: 'var(--m3-surface-2)',
        position: 'relative',
        overflow: 'hidden',
    };

    return (
        <div 
            style={style} 
            className={`animate-shimmer ${className}`}
        />
    );
}
