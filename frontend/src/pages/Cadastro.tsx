import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterInputs, translateAuthError, calculatePasswordStrength } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Eye, EyeOff, Loader2, UserPlus, Info } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';

export default function Cadastro() {
  const navigate = useNavigate();
  const { signUp } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [successInfo, setSuccessInfo] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm<RegisterInputs>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      acceptTerms: false,
    }
  });

  const passwordValue = watch('password') || '';
  const acceptTermsValue = watch('acceptTerms');
  
  // Calculate password strength
  const strength = calculatePasswordStrength(passwordValue);

  const handleRegister = async (data: RegisterInputs) => {
    setLoading(true);
    setSuccessInfo(null);
    try {
      const response = await signUp(data.email, data.password);
      if (response.error) {
        toast.error(translateAuthError(response.error), 'Falha no Cadastro');
      } else {
        // If the user object is returned but session is null, email confirmation is active
        if (response.data.user && !response.data.session) {
          setSuccessInfo(
            'Cadastro recebido! Enviamos um link de confirmação para a sua caixa de entrada. Por favor, verifique seu e-mail para ativar sua conta antes de tentar acessar.'
          );
          toast.success('Link de confirmação enviado para seu e-mail.', 'Quase lá!');
        } else {
          toast.success('Conta criada e autenticada com sucesso!', 'Bem-vindo');
          navigate('/');
        }
      }
    } catch (err: any) {
      toast.error('Erro ao conectar com o serviço de autenticação.', 'Erro');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="flex h-screen w-full items-center justify-center p-4 bg-cover bg-center overflow-hidden"
      style={{ backgroundImage: "url('/bglogin.png')" }}
    >
      <div className="w-full max-w-[460px] rounded-3xl border border-white/5 bg-[#0c0c14]/85 p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden animate-slide-up">
        {/* Decorative Top Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-teal-500 to-indigo-500" />

        {/* Logo Section */}
        <div className="flex flex-col items-center mb-6 text-center">
          <div className="w-14 h-14 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
            <UserPlus className="w-7 h-7 text-emerald-400" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            Criar Conta
          </h1>
          <p className="text-sm text-slate-400 mt-2">
            Cadastre-se para obter acesso corporativo seguro
          </p>
        </div>

        {successInfo ? (
          <div className="space-y-6 animate-fade-in text-center py-4">
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 text-slate-300 flex flex-col items-center gap-3">
              <Info className="w-10 h-10 text-emerald-400 animate-pulse" />
              <p className="text-sm leading-relaxed">{successInfo}</p>
            </div>
            <Button
              type="button"
              onClick={() => navigate('/auth/login')}
              className="w-full h-12 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-xl"
            >
              Ir para o Login
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(handleRegister)} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block ml-1">
                Endereço de E-mail
              </label>
              <Input
                type="email"
                placeholder="seu-email@dominio.com"
                {...register('email')}
                disabled={loading}
                className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 focus:ring-emerald-500/30 focus:border-emerald-500"
              />
              {errors.email && (
                <p className="text-xs text-red-400 mt-1 ml-1">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block ml-1">
                Senha de Acesso (Mín. 6 caracteres)
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Crie uma senha forte"
                  {...register('password')}
                  disabled={loading}
                  className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 pr-12 focus:ring-emerald-500/30 focus:border-emerald-500"
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
                Confirmar Senha
              </label>
              <div className="relative">
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Repita a mesma senha"
                  {...register('confirmPassword')}
                  disabled={loading}
                  className="bg-black/40 border-white/10 text-white rounded-xl py-3 px-4 pr-12 focus:ring-emerald-500/30 focus:border-emerald-500"
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

            {/* Terms and Privacy Agreement Box */}
            <div className="pt-2">
              <div className="flex items-start space-x-3 p-3 bg-white/5 border border-white/10 rounded-xl">
                <Checkbox
                  id="acceptTerms"
                  checked={acceptTermsValue}
                  onCheckedChange={(checked) => setValue('acceptTerms', checked === true)}
                  disabled={loading}
                  className="border-slate-500 mt-0.5 data-[state=checked]:bg-emerald-500 data-[state=checked]:border-emerald-500 rounded"
                />
                <div className="leading-tight">
                  <label htmlFor="acceptTerms" className="text-xs text-slate-300 cursor-pointer select-none">
                    Eu li e concordo com os{' '}
                    <button
                      type="button"
                      onClick={() => navigate('/termos')}
                      className="text-emerald-400 hover:underline inline-block font-semibold"
                    >
                      Termos de Serviço
                    </button>{' '}
                    e a{' '}
                    <button
                      type="button"
                      onClick={() => navigate('/privacidade')}
                      className="text-emerald-400 hover:underline inline-block font-semibold"
                    >
                      Política de Privacidade
                    </button>.
                  </label>
                </div>
              </div>
              {errors.acceptTerms && (
                <p className="text-xs text-red-400 mt-1.5 ml-1">{errors.acceptTerms.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-emerald-500 to-teal-600 hover:brightness-110 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/20 active:scale-[0.99] border-none mt-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Criar minha Conta</>
              )}
            </Button>
          </form>
        )}

        {/* Footer */}
        <p className="text-center text-sm text-slate-400 mt-8">
          Já possui acesso corporativo?{' '}
          <button
            type="button"
            onClick={() => navigate('/auth/login')}
            disabled={loading}
            className="font-bold text-white hover:underline transition-all"
          >
            Acesse aqui
          </button>
        </p>
      </div>
    </div>
  );
}
