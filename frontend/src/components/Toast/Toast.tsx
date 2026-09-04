import React, { useEffect, useState } from 'react';
import styles from './Toast.module.css';
import { MaterialIcon } from '../ui/MaterialIcon';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

export default function Toast({ id, type, title, message, duration = 3000, onClose }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration]);

  const handleClose = () => {
    setIsExiting(true);
    // Espera a animação terminar antes de remover do DOM
    setTimeout(() => {
      onClose(id);
    }, 300);
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <MaterialIcon name="check_circle" size={20} />;
      case 'error':
        return <MaterialIcon name="error" size={20} />;
      case 'warning':
        return <MaterialIcon name="warning" size={20} />;
      case 'info':
      default:
        return <MaterialIcon name="info" size={20} />;
    }
  };

  return (
    <div className={`${styles.toast} ${styles[type]} ${isExiting ? styles.exiting : ''}`}>
      <div className={styles.icon}>{getIcon()}</div>
      <div className={styles.content}>
        {title && <h4 className={styles.title}>{title}</h4>}
        <p className={styles.message}>{message}</p>
      </div>
      <button className={styles.closeButton} onClick={handleClose} aria-label="Fechar Notificação">
        <MaterialIcon name="close" size={16} />
      </button>
      <div className={styles.progressBar}>
        <div className={styles.progressFill} style={{ animationDuration: `${duration}ms` }} />
      </div>
    </div>
  );
}
