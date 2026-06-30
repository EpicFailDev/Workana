import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { updatePasswordSchema, UpdatePasswordInputs, translateAuthError, calculatePasswordStrength } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Eye, EyeOff, Loader2, ShieldAlert, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import styles from '../components/ui/login.module.css';

export default function NovaSenha() {
  const navigate = useNavigate();
  const { updatePassword, signOut, session } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  // Check if session exists (the user has authenticated via OTP)
  useEffect(() => {
    if (session) {
      setIsAuthorized(true);
    } else {
      setIsAuthorized(false);
      toast.error('Acesso não autorizado. Por favor, valide o código OTP enviado ao seu e-mail.', 'Sessão Ausente');
      navigate('/auth/recuperar');
    }
  }, [session, navigate, toast]);

  const { register, handleSubmit, formState: { errors }, watch } = useForm<UpdatePasswordInputs>({
    resolver: zodResolver(updatePasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    }
  });

  const passwordValue = watch('password') || '';
  const strength = calculatePasswordStrength(passwordValue);

  const handleUpdatePassword = async (data: UpdatePasswordInputs) => {
    setLoading(true);
    try {
      const response = await updatePassword(data.password);
      if (response.error) {
        toast.error(translateAuthError(response.error), 'Falha ao Salvar');
      } else {
        toast.success('Sua senha foi redefinida com sucesso!', 'Senha Atualizada');
        await signOut();
        navigate('/auth/login');
      }
    } catch (err: any) {
      toast.error('Erro ao conectar ao servidor para atualizar a senha.', 'Erro');
    } finally {
      setLoading(false);
    }
  };

  if (isAuthorized === false) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className={styles.screen}>
      {/* Left Panel: Form */}
      <div className={styles.leftPanel}>
        <div className={styles.formShell}>
          {/* Logo Section */}
          <div className="flex flex-col items-start mb-6 text-left">
            <div className="w-14 h-14 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(99,102,241,0.2)]">
              <CheckCircle className="w-7 h-7 text-indigo-400" />
            </div>
            <h1 className="text-[2.5rem] font-bold tracking-[-0.035em] text-white leading-[1.12]">
              Nova Senha
            </h1>
            <h1 className="bg-gradient-to-r from-violet-400 to-indigo-500 bg-clip-text text-[2.6rem] font-bold leading-[1.08] tracking-[-0.035em] text-transparent">
              Corporativa
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              Insira sua nova senha corporativa segura abaixo
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(handleUpdatePassword)} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block ml-1">
                Nova Senha (Mín. 6 caracteres)
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Insira a nova senha"
                  {...register('password')}
                  disabled={loading}
                  className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 pr-12 focus:ring-indigo-500/30 focus:border-indigo-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                  aria-label={showPassword ? "Ocultar senha" : "Exibir senha"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              
              {/* Password Strength Meter */}
              {passwordValue.length > 0 && (
                <div className="pt-2 px-1">
                  <div className="flex justify-between text-2xs font-semibold mb-1">
                    <span className="text-slate-400">Força da Senha:</span>
                    <span className={`font-bold ${
                      strength.score === 1 ? 'text-red-400' :
                      strength.score === 2 ? 'text-yellow-400' :
                      strength.score === 3 ? 'text-blue-400' :
                      'text-green-400'
                    }`}>{strength.label}</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex gap-1">
                    <div className={`h-full rounded-full transition-all duration-300 ${
                      strength.score >= 1 ? (strength.score === 1 ? 'bg-red-500 w-[25%]' : '') ||
                      (strength.score === 2 ? 'bg-yellow-500 w-[50%]' : '') ||
                      (strength.score === 3 ? 'bg-blue-500 w-[75%]' : '') ||
                      (strength.score === 4 ? 'bg-green-500 w-[100%]' : '') : 'w-0'
                    }`} />
                  </div>
                </div>
              )}
              {errors.password && (
                <p className="text-xs text-red-400 mt-1 ml-1">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block ml-1">
                Confirmar Nova Senha
              </label>
              <div className="relative">
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirme a mesma senha"
                  {...register('confirmPassword')}
                  disabled={loading}
                  className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 pr-12 focus:ring-indigo-500/30 focus:border-indigo-500"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={loading}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                  aria-label={showConfirmPassword ? "Ocultar senha" : "Exibir senha"}
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-xs text-red-400 mt-1 ml-1">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Warning notice */}
            <div className="flex items-start gap-2.5 p-3 bg-red-500/5 border border-red-500/10 rounded-xl mt-2">
              <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <p className="text-2xs text-slate-400 leading-normal">
                Ao salvar, sua sessão temporária será encerrada e você precisará fazer login novamente com a nova senha corporativa.
              </p>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-violet-500 to-indigo-600 hover:brightness-110 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-950/20 active:scale-[0.99] border-none mt-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Salvar Nova Senha</>
              )}
            </Button>
          </form>
        </div>
      </div>

      {/* Right Panel: Image */}
      <div className={styles.rightPanel}>
        <img
          src="/bglogin.png"
          alt="Password reset background"
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
}
