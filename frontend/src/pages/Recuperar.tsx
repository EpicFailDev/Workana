import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { recoverySchema, RecoveryInputs, translateAuthError } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { KeyRound, Loader2, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import styles from '../components/ui/login.module.css';

export default function Recuperar() {
  const navigate = useNavigate();
  const { requestPasswordReset } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<RecoveryInputs>({
    resolver: zodResolver(recoverySchema),
    defaultValues: {
      email: '',
    }
  });

  const handleRecovery = async (data: RecoveryInputs) => {
    setLoading(true);
    try {
      const response = await requestPasswordReset(data.email);
      if (response.error) {
        toast.error(translateAuthError(response.error), 'Falha na Solicitação');
      } else {
        toast.success(
          'Se o e-mail cadastrado for válido, enviamos o código de redefinição de 6 dígitos.',
          'Código Enviado'
        );
        navigate(`/auth/verificar-otp?email=${encodeURIComponent(data.email)}`);
      }
    } catch (err: any) {
      toast.error('Erro ao conectar ao servidor de autenticação.', 'Erro');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.screen}>
      {/* Left Panel: Form */}
      <div className={styles.leftPanel}>
        <div className={styles.formShell}>
          {/* Logo Section */}
          <div className="flex flex-col items-start mb-8 text-left">
            <div className="w-14 h-14 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
              <KeyRound className="w-7 h-7 text-amber-400" />
            </div>
            <h1 className="text-[2.5rem] font-bold tracking-[-0.035em] text-white leading-[1.12]">
              Recuperar
            </h1>
            <h1 className="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-[2.6rem] font-bold leading-[1.08] tracking-[-0.035em] text-transparent">
              Senha Corporativa
            </h1>
            <p className="text-sm text-slate-400 mt-3 leading-relaxed">
              Informe seu e-mail cadastrado para enviarmos o código OTP de redefinição
            </p>
          </div>

          {/* Recovery Form */}
          <form onSubmit={handleSubmit(handleRecovery)} className="space-y-5">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block ml-1">
                Endereço de E-mail
              </label>
              <Input
                type="email"
                placeholder="seu-email@dominio.com"
                {...register('email')}
                disabled={loading}
                className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 focus:ring-amber-500/30 focus:border-amber-500"
              />
              {errors.email && (
                <p className="text-xs text-red-400 mt-1 ml-1">{errors.email.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-amber-500 to-orange-600 hover:brightness-110 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-amber-950/20 active:scale-[0.99] border-none mt-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Enviar Código OTP</>
              )}
            </Button>
          </form>

          {/* Voltar para o login */}
          <div className="mt-8 text-center">
            <button
              type="button"
              onClick={() => navigate('/auth/login')}
              disabled={loading}
              className="text-sm font-bold text-[#b7b8bf] hover:text-white transition-colors inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Voltar para o Login
            </button>
          </div>

          {/* Info notice */}
          <div className="mt-8 bg-white/5 border border-white/5 rounded-2xl p-4 text-xs text-slate-400 leading-relaxed">
            <p>
              <strong>Aviso de Segurança:</strong> Não compartilhamos se um e-mail está cadastrado ou não para proteger a privacidade de nossos usuários corporativos.
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel: Image */}
      <div className={styles.rightPanel}>
        <img
          src="/bglogin.png"
          alt="Password recovery background"
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
}
