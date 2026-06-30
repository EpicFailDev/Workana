import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { otpSchema, OtpInputs, translateAuthError } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { ShieldCheck, Loader2, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import styles from '../components/ui/login.module.css';

export default function VerificarOtp() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { verifyOTP, requestPasswordReset } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(60);
  const [resendLoading, setResendLoading] = useState(false);

  // OTP inputs state: 6 boxes
  const [otpValues, setOtpValues] = useState<string[]>(new Array(6).fill(''));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Get email from query parameter or state
  const emailParam = searchParams.get('email') || '';

  const { register, handleSubmit, formState: { errors }, setValue, trigger } = useForm<OtpInputs>({
    resolver: zodResolver(otpSchema),
    defaultValues: {
      email: emailParam,
      otp: '',
    }
  });

  // Keep react-hook-form's email sync'ed
  useEffect(() => {
    if (emailParam) {
      setValue('email', emailParam);
    }
  }, [emailParam, setValue]);

  // Handle countdown timer for resend button
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleChange = (val: string, index: number) => {
    const cleanedVal = val.replace(/[^0-9]/g, '');
    const lastChar = cleanedVal ? cleanedVal[cleanedVal.length - 1] : '';

    // Update DOM input value immediately to allow synchronous reading
    if (inputRefs.current[index]) {
      inputRefs.current[index]!.value = lastChar;
    }

    const newOtp = [...otpValues];
    newOtp[index] = lastChar;
    setOtpValues(newOtp);
    
    // Read directly from DOM to get true synchronous code string
    const codeString = inputRefs.current.map(input => input?.value || '').join('');
    setValue('otp', codeString);
    trigger('otp');

    // Auto focus next input
    if (index < 5 && lastChar) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto submit if complete
    if (codeString.length === 6) {
      executeVerification(emailParam || watchEmail, codeString);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Backspace') {
      const newOtp = [...otpValues];
      
      // Update DOM immediately
      if (inputRefs.current[index]) {
        if (inputRefs.current[index]!.value === '') {
          if (index > 0) {
            if (inputRefs.current[index - 1]) {
              inputRefs.current[index - 1]!.value = '';
            }
            newOtp[index - 1] = '';
            setOtpValues(newOtp);
            setValue('otp', newOtp.join(''));
            inputRefs.current[index - 1]?.focus();
          }
        } else {
          inputRefs.current[index]!.value = '';
          newOtp[index] = '';
          setOtpValues(newOtp);
          setValue('otp', newOtp.join(''));
        }
      }
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim().replace(/[^0-9]/g, '');
    if (pastedData.length === 6) {
      const digits = pastedData.split('');
      
      // Update DOM inputs immediately
      digits.forEach((digit, idx) => {
        if (inputRefs.current[idx]) {
          inputRefs.current[idx]!.value = digit;
        }
      });

      setOtpValues(digits);
      setValue('otp', pastedData);
      trigger('otp');
      inputRefs.current[5]?.focus();
      executeVerification(emailParam || watchEmail, pastedData);
    }
  };

  const watchEmail = watchEmailFunc();
  function watchEmailFunc() {
    return emailParam;
  }

  const executeVerification = async (email: string, code: string) => {
    if (!email) {
      toast.error('Informe um e-mail válido.', 'E-mail Ausente');
      return;
    }
    if (code.length !== 6) {
      toast.error('O código OTP deve ter 6 dígitos.', 'Código Incompleto');
      return;
    }

    setLoading(true);
    try {
      const response = await verifyOTP(email, code);
      if (response.error) {
        toast.error(translateAuthError(response.error), 'Falha na Validação');
      } else {
        toast.success('Código verificado! Crie sua nova senha.', 'Sucesso');
        navigate('/auth/nova-senha');
      }
    } catch (err: any) {
      toast.error('Erro de comunicação na validação do OTP.', 'Erro');
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async (data: OtpInputs) => {
    await executeVerification(data.email, data.otp);
  };

  const handleResend = async () => {
    const email = emailParam || watchEmail;
    if (!email) {
      toast.error('Preencha o e-mail para reenviar o código.', 'Aviso');
      return;
    }

    setResendLoading(true);
    try {
      const response = await requestPasswordReset(email);
      if (response.error) {
        toast.error(translateAuthError(response.error), 'Falha no Reenvio');
      } else {
        toast.success('Novo código OTP enviado com sucesso.', 'Código Reenviado');
        setResendCooldown(60);
        setOtpValues(new Array(6).fill(''));
        setValue('otp', '');
      }
    } catch (err: any) {
      toast.error('Erro ao conectar para solicitar reenvio.', 'Erro');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className={styles.screen}>
      {/* Left Panel: Form */}
      <div className={styles.leftPanel}>
        <div className={styles.formShell}>
          {/* Logo Section */}
          <div className="flex flex-col items-start mb-6 text-left">
            <div className="w-14 h-14 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl flex items-center justify-center mb-4 shadow-[0_0_20px_rgba(99,102,241,0.2)]">
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
            </div>
            <h1 className="text-[2.5rem] font-bold tracking-[-0.035em] text-white leading-[1.12]">
              Verificar
            </h1>
            <h1 className="bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-[2.6rem] font-bold leading-[1.08] tracking-[-0.035em] text-transparent">
              Código OTP
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              Insira o código de 6 dígitos enviado para{' '}
              <span className="text-white font-semibold block mt-0.5 break-all">{emailParam}</span>
            </p>
          </div>

          {/* OTP Form */}
          <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
            <input type="hidden" {...register('email')} />

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block text-center">
                Código OTP de Redefinição
              </label>
              
              <div className="flex justify-between gap-2 max-w-[320px] mx-auto pt-2">
                {otpValues.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => { inputRefs.current[idx] = el; }}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={1}
                    value={digit}
                    disabled={loading || resendLoading}
                    onChange={(e) => handleChange(e.target.value, idx)}
                    onKeyDown={(e) => handleKeyDown(e, idx)}
                    onPaste={idx === 0 ? handlePaste : undefined}
                    className="w-11 h-13 text-center bg-black/40 border border-white/10 text-white font-extrabold text-xl rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all select-all"
                    aria-label={`Dígito ${idx + 1}`}
                  />
                ))}
              </div>
              
              <input type="hidden" {...register('otp')} />
              {errors.otp && (
                <p className="text-xs text-red-400 mt-2 text-center">{errors.otp.message}</p>
              )}
            </div>

            <div className="text-center text-xs text-slate-400 leading-normal bg-white/5 border border-white/5 rounded-2xl p-4">
              <p><strong>Duração planejada:</strong> O código expira em 10 minutos.</p>
            </div>

            <Button
              type="submit"
              disabled={loading || resendLoading || otpValues.some(v => !v)}
              className="w-full h-12 bg-gradient-to-r from-blue-500 to-indigo-600 hover:brightness-110 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-950/20 active:scale-[0.99] border-none"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Validar Código OTP</>
              )}
            </Button>

            <div className="text-center pt-2">
              {resendCooldown > 0 ? (
                <p className="text-xs text-slate-500 font-medium">
                  Você poderá reenviar o código em{' '}
                  <span className="text-slate-300 font-bold">{resendCooldown}s</span>
                </p>
              ) : (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={loading || resendLoading}
                  className="text-xs text-indigo-400 hover:text-indigo-300 hover:underline font-bold transition-all flex items-center gap-1.5 mx-auto"
                >
                  {resendLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="w-3.5 h-3.5" />
                  )}
                  Reenviar código por e-mail
                </button>
              )}
            </div>
          </form>

          {/* Voltar para redefinição */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => navigate('/auth/recuperar')}
              disabled={loading || resendLoading}
              className="text-sm font-bold text-[#b7b8bf] hover:text-white transition-colors inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Alterar E-mail
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel: Image */}
      <div className={styles.rightPanel}>
        <img
          src="/bglogin.png"
          alt="OTP verification background"
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
}
