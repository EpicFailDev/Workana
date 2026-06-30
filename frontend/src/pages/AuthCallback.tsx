import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../integrations/supabase/client';
import { useToast } from '../context/ToastContext';
import { translateAuthError } from '../services/authService';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const hasExchanged = useRef(false);

  const errorCode = searchParams.get('error');
  const errorDesc = searchParams.get('error_description');
  const code = searchParams.get('code');

  useEffect(() => {
    // Avoid double trigger in React 18 StrictMode
    if (hasExchanged.current) return;

    if (errorCode || errorDesc) {
      toast.error(errorDesc || 'Login com Google cancelado ou com falha.', 'Erro OAuth');
      navigate('/auth/login');
      return;
    }

    if (code) {
      hasExchanged.current = true;
      supabase.auth.exchangeCodeForSession(code)
        .then(({ data, error }) => {
          if (error) {
            toast.error(translateAuthError(error), 'Erro de Autenticação');
            navigate('/auth/login');
          } else {
            toast.success('Login com Google realizado com sucesso!', 'Bem-vindo');
            const next = sessionStorage.getItem('auth_redirect_to') || '/';
            sessionStorage.removeItem('auth_redirect_to');
            navigate(next);
          }
        })
        .catch((err) => {
          console.error('Falha interna ao trocar o código OAuth:', err);
          toast.error('Erro de processamento interno durante o login.', 'Erro');
          navigate('/auth/login');
        });
    } else {
      // Se não houver código, verifica se já existe uma sessão ativa (caso do fluxo implícito / hash)
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
          const next = sessionStorage.getItem('auth_redirect_to') || '/';
          sessionStorage.removeItem('auth_redirect_to');
          navigate(next);
        } else {
          navigate('/auth/login');
        }
      }).catch(() => {
        navigate('/auth/login');
      });
    }
  }, [code, errorCode, errorDesc, navigate, toast]);

  return (
    <div className="flex min-height-screen w-full flex-col items-center justify-center p-4 bg-radial from-[#0f1123] to-[#06070d] py-12 gap-4">
      <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
      <span className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
        Processando resposta de login seguro...
      </span>
    </div>
  );
}
