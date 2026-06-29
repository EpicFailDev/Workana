import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import styles from './Auth.module.css';

export default function Auth() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const { signIn, signUp } = useAuth();
    const { toast } = useToast();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validações básicas
        if (!email.trim() || !password) {
            toast.error('Preencha todos os campos.', 'Erro de Validação');
            return;
        }

        if (!isLogin && password !== confirmPassword) {
            toast.error('As senhas não coincidem.', 'Erro de Validação');
            return;
        }

        setSubmitting(true);
        try {
            if (isLogin) {
                const { error } = await signIn(email, password);
                if (error) {
                    toast.error(error.message, 'Erro ao Entrar');
                } else {
                    toast.success('Acesso autorizado. Bem-vindo de volta!', 'Sucesso');
                    navigate('/');
                }
            } else {
                const { data, error } = await signUp(email, password);
                if (error) {
                    toast.error(error.message, 'Erro ao Registrar');
                } else {
                    // Supabase pode requerer confirmação de email dependendo das configurações.
                    if (data?.session) {
                        toast.success('Conta criada e logada com sucesso!', 'Sucesso');
                        navigate('/');
                    } else {
                        toast.success('Conta criada com sucesso! Verifique seu email para confirmação, se necessário.', 'Conta Criada');
                        setIsLogin(true);
                        setPassword('');
                        setConfirmPassword('');
                    }
                }
            }
        } catch (err: any) {
            console.error(err);
            toast.error(err?.message || 'Ocorreu um erro inesperado.', 'Erro de Sistema');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className={styles.authContainer}>
            <div className={styles.authCard}>
                {/* Logo & Header */}
                <div className={styles.logoArea}>
                    <div className={styles.logoIcon}>
                        <img 
                            src="https://media.licdn.com/dms/image/sync/v2/D4D27AQEiu3OUtuPafw/articleshare-shrink_800/B4DZmh2H6fJIAM-/0/1759356944429?e=2147483647&v=beta&t=RtaLDLIZf-4r34Z-ETQzA4mmzZRdYCEYXuV07qeXdDk" 
                            alt="Workana Logo" 
                            className={styles.officialLogo}
                        />
                        <div className={styles.pulse}></div>
                    </div>
                    <h1 className={styles.title}>Workana Accelerator</h1>
                    <span className={styles.subtitle}>SISTEMA DE AUTENTICAÇÃO</span>
                </div>

                {/* Switch Tabs */}
                <div className={styles.tabs}>
                    <button 
                        type="button"
                        className={`${styles.tabButton} ${isLogin ? styles.active : ''}`}
                        onClick={() => {
                            setIsLogin(true);
                            setPassword('');
                            setConfirmPassword('');
                        }}
                    >
                        Entrar
                    </button>
                    <button 
                        type="button"
                        className={`${styles.tabButton} ${!isLogin ? styles.active : ''}`}
                        onClick={() => {
                            setIsLogin(false);
                            setPassword('');
                            setConfirmPassword('');
                        }}
                    >
                        Registrar
                    </button>
                </div>

                {/* Form */}
                <form className={styles.form} onSubmit={handleSubmit}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>EMAIL OPERACIONAL</label>
                        <input
                            type="email"
                            className={styles.input}
                            placeholder="seu@email.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={submitting}
                            required
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>CHAVE DE ACESSO (SENHA)</label>
                        <input
                            type="password"
                            className={styles.input}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={submitting}
                            required
                        />
                    </div>

                    {!isLogin && (
                        <div className={styles.formGroup}>
                            <label className={styles.label}>CONFIRMAR CHAVE</label>
                            <input
                                type="password"
                                className={styles.input}
                                placeholder="••••••••"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                disabled={submitting}
                                required
                            />
                        </div>
                    )}

                    <button type="submit" className={styles.submitButton} disabled={submitting}>
                        {submitting ? (
                            <>
                                <div className={styles.spinner}></div>
                                <span>Processando...</span>
                            </>
                        ) : (
                            <span>{isLogin ? 'INICIAR SESSÃO' : 'CRIAR CREDENCIAIS'}</span>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
