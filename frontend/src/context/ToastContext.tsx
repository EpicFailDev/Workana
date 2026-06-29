import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import Toast, { ToastType } from '../components/Toast/Toast';
import styles from '../components/Toast/Toast.module.css';

interface ToastData {
    id: string;
    type: ToastType;
    title?: string;
    message: string;
    duration?: number;
}

interface ToastContextType {
    addToast: (toast: Omit<ToastData, 'id'>) => void;
    removeToast: (id: string) => void;
    // Atalhos
    toast: {
        success: (message: string, title?: string) => void;
        error: (message: string, title?: string) => void;
        warning: (message: string, title?: string) => void;
        info: (message: string, title?: string) => void;
    };
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastData[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    const addToast = useCallback(({ type, title, message, duration = 4000 }: Omit<ToastData, 'id'>) => {
        const id = Math.random().toString(36).substring(2, 9);
        setToasts((prev) => [...prev, { id, type, title, message, duration }]);
    }, []);

    const toastHelpers = {
        success: (message: string, title?: string) => addToast({ type: 'success', title, message }),
        error: (message: string, title?: string) => addToast({ type: 'error', title, message }),
        warning: (message: string, title?: string) => addToast({ type: 'warning', title, message }),
        info: (message: string, title?: string) => addToast({ type: 'info', title, message }),
    };

    return (
        <ToastContext.Provider value={{ addToast, removeToast, toast: toastHelpers }}>
            {children}
            <div className={styles.toastContainer}>
                {toasts.map((toast) => (
                    <Toast
                        key={toast.id}
                        {...toast}
                        onClose={removeToast}
                    />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (context === undefined) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}
