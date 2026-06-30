import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { AuthFormSplitScreen } from '@/components/ui/login';

export default function Auth() {
    const location = useLocation();
    const navigate = useNavigate();
    const { signIn, signUp, signInWithGoogle } = useAuth();
    const { toast } = useToast();
    const [mode, setMode] = useState<'login' | 'register'>('login');

    useEffect(() => {
        if (location.pathname === '/auth/cadastro' || location.hash === '#register') {
            setMode('register');
        } else {
            setMode('login');
        }
    }, [location.pathname, location.hash]);

    const handleLoginSubmit = async (data: any) => {
        try {
            const response = await signIn(data.email, data.password);
            if (response.error) {
                toast.error(response.error.message, 'Erro ao Entrar');
                throw response.error;
            } else {
                toast.success('Acesso autorizado. Bem-vindo de volta!', 'Sucesso');
                navigate('/');
            }
        } catch (err: any) {
            console.error(err);
            throw err;
        }
    };

    const handleRegisterSubmit = async (data: any) => {
        try {
            const response = await signUp(data.email, data.password);
            if (response.error) {
                toast.error(response.error.message, 'Erro ao Registrar');
                throw response.error;
            } else {
                if (response.data?.session) {
                    toast.success('Conta criada e logada com sucesso!', 'Sucesso');
                    navigate('/');
                } else {
                    toast.success('Conta criada com sucesso! Verifique seu email para confirmação, se necessário.', 'Conta Criada');
                    navigate('/auth/login');
                }
            }
        } catch (err: any) {
            console.error(err);
            throw err;
        }
    };

    const handleGoogleLogin = async () => {
        try {
            const { error } = await signInWithGoogle(true);
            if (error) {
                toast.error(error.message, 'Erro Google OAuth');
            }
        } catch (err: any) {
            toast.error('Erro ao iniciar fluxo Google OAuth.', 'Erro');
        }
    };

    const isLogin = mode === 'login';

    return (
        <AuthFormSplitScreen
            logo={
                <img 
                    src="/icon.png" 
                    alt="AI Assistant Logo" 
                    className="h-[90px] w-[90px] select-none"
                    draggable="false"
                />
            }
            title={
                isLogin ? (
                    <div>
                        <h1 className="text-[2.5rem] font-medium tracking-[-0.035em] text-white leading-[1.12]">
                            Welcome to your
                        </h1>
                        <h1 className="mt-1 bg-gradient-to-r from-[#ff5a1f] via-[#d934c4] to-[#087cff] bg-clip-text text-[2.6rem] font-bold leading-[1.08] tracking-[-0.035em] text-transparent">
                            AI Assistant
                        </h1>
                    </div>
                ) : (
                    <div>
                        <h1 className="text-[2.5rem] font-medium tracking-[-0.035em] text-white leading-[1.12]">
                            Create your
                        </h1>
                        <h1 className="mt-1 bg-gradient-to-r from-[#ff5a1f] via-[#d934c4] to-[#087cff] bg-clip-text text-[2.6rem] font-bold leading-[1.08] tracking-[-0.035em] text-transparent">
                            AI Account
                        </h1>
                    </div>
                )
            }
            description={
                isLogin 
                    ? 'Your intelligent partner for freelance success.' 
                    : 'Join the future of freelance automation.'
            }
            imageSrc="/bglogin.png"
            imageAlt="Login background image"
            onSubmit={isLogin ? handleLoginSubmit : handleRegisterSubmit}
            forgotPasswordHref="/auth/recuperar"
            createAccountHref={isLogin ? '/auth/cadastro' : '/auth/login'}
            footerLabelText={isLogin ? "Don't have an account?" : 'Already have an account?'}
            footerLinkText={isLogin ? 'Create one' : 'Sign in'}
            showRememberMe={isLogin}
            onGoogleClick={handleGoogleLogin}
        />
    );
}
