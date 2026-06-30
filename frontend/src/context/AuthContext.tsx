import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, Session, AuthResponse, UserResponse } from '@supabase/supabase-js';
import { supabase } from '../integrations/supabase/client';

interface AuthContextType {
    user: User | null;
    session: Session | null;
    loading: boolean;
    signIn: (email: string, password: string, rememberMe?: boolean) => Promise<AuthResponse>;
    signUp: (email: string, password: string) => Promise<AuthResponse>;
    signInWithGoogle: (rememberMe?: boolean, next?: string) => Promise<{ data: { provider: string; url: string } | null; error: any }>;
    signOut: () => Promise<void>;
    requestPasswordReset: (email: string) => Promise<{ error: any }>;
    verifyOTP: (email: string, otp: string) => Promise<AuthResponse>;
    updatePassword: (password: string) => Promise<UserResponse>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const REMEMBER_ME_KEY = 'auth_remember_me';

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Obter sessão inicial
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        }).catch((err) => {
            console.error("Erro ao recuperar sessão Supabase:", err);
            setLoading(false);
        });

        // Observar mudanças de estado da autenticação
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);

            // Se for logout completo, limpa tudo
            if (event === 'SIGNED_OUT') {
                localStorage.removeItem(REMEMBER_ME_KEY);
                localStorage.removeItem('supabase.auth.token');
                sessionStorage.removeItem('supabase.auth.token');
            }
        });

        return () => {
            subscription.unsubscribe();
        };
    }, []);

    const signIn = async (email: string, password: string, rememberMe = false): Promise<AuthResponse> => {
        setLoading(true);
        try {
            // Define o flag de lembrar-me antes da autenticação para o CustomStorage saber
            localStorage.setItem(REMEMBER_ME_KEY, rememberMe ? 'true' : 'false');
            const response = await supabase.auth.signInWithPassword({ email, password });
            if (response.data.session) {
                setSession(response.data.session);
                setUser(response.data.session.user);
            }
            return response;
        } finally {
            setLoading(false);
        }
    };

    const signUp = async (email: string, password: string): Promise<AuthResponse> => {
        setLoading(true);
        try {
            // Durante o cadastro, guardamos o lembrar-me como falso por padrão ou herdado
            localStorage.setItem(REMEMBER_ME_KEY, 'false');
            const redirectToUrl = `${window.location.origin}/auth/callback`;
            return await supabase.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: redirectToUrl,
                }
            });
        } finally {
            setLoading(false);
        }
    };

    const signInWithGoogle = async (rememberMe = false, next = '/'): Promise<{ data: { provider: string; url: string } | null; error: any }> => {
        setLoading(true);
        try {
            localStorage.setItem(REMEMBER_ME_KEY, rememberMe ? 'true' : 'false');
            sessionStorage.setItem('auth_redirect_to', next);
            const redirectToUrl = `${window.location.origin}/auth/callback`;
            
            const response = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: redirectToUrl,
                    queryParams: {
                        access_type: 'offline',
                        prompt: 'consent',
                    },
                },
            });
            return response as any;
        } finally {
            setLoading(false);
        }
    };

    const signOut = async () => {
        setLoading(true);
        try {
            await supabase.auth.signOut();
        } finally {
            // Limpa explicitamente ambos storages
            localStorage.removeItem(REMEMBER_ME_KEY);
            localStorage.removeItem('supabase.auth.token');
            sessionStorage.removeItem('supabase.auth.token');
            // Remove qualquer token residual com prefixo sb-
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && (key.startsWith('sb-') || key.includes('auth'))) {
                    localStorage.removeItem(key);
                }
            }
            for (let i = sessionStorage.length - 1; i >= 0; i--) {
                const key = sessionStorage.key(i);
                if (key && (key.startsWith('sb-') || key.includes('auth'))) {
                    sessionStorage.removeItem(key);
                }
            }
            setSession(null);
            setUser(null);
            setLoading(false);
        }
    };

    const requestPasswordReset = async (email: string): Promise<{ error: any }> => {
        setLoading(true);
        try {
            const redirectToUrl = `${window.location.origin}/auth/verificar-otp`;
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: redirectToUrl,
            });
            return { error };
        } finally {
            setLoading(false);
        }
    };

    const verifyOTP = async (email: string, otp: string): Promise<AuthResponse> => {
        setLoading(true);
        try {
            // Para recuperação de senha, verifyOtp com tipo 'recovery'
            const response = await supabase.auth.verifyOtp({
                email,
                token: otp,
                type: 'recovery',
            });
            if (response.data.session) {
                setSession(response.data.session);
                setUser(response.data.session.user);
            }
            return response;
        } finally {
            setLoading(false);
        }
    };

    const updatePassword = async (password: string): Promise<UserResponse> => {
        setLoading(true);
        try {
            return await supabase.auth.updateUser({ password });
        } finally {
            setLoading(false);
        }
    };

    return (
        <AuthContext.Provider value={{
            user,
            session,
            loading,
            signIn,
            signUp,
            signInWithGoogle,
            signOut,
            requestPasswordReset,
            verifyOTP,
            updatePassword
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
