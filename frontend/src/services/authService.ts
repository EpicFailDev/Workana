import * as z from 'zod';

// ==================== SCHEMAS ====================

export const loginSchema = z.object({
  email: z.string().email({ message: "Por favor, insira um e-mail válido." }),
  password: z.string().min(1, { message: "A senha não pode ser vazia." }),
  rememberMe: z.boolean(),
});

export const registerSchema = z.object({
  email: z.string().email({ message: "Por favor, insira um e-mail válido." }),
  password: z.string().min(6, { message: "A senha deve ter no mínimo 6 caracteres." }),
  confirmPassword: z.string().min(6, { message: "A confirmação da senha deve ter no mínimo 6 caracteres." }),
  acceptTerms: z.boolean().refine(val => val === true, {
    message: "Você precisa aceitar os Termos de Serviço e Política de Privacidade."
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "As senhas não coincidem.",
  path: ["confirmPassword"],
});

export const recoverySchema = z.object({
  email: z.string().email({ message: "Por favor, insira um e-mail válido." }),
});

export const otpSchema = z.object({
  email: z.string().email({ message: "Por favor, insira um e-mail válido." }),
  otp: z.string().length(6, { message: "O código OTP deve ter exatamente 6 dígitos." }),
});

export const updatePasswordSchema = z.object({
  password: z.string().min(6, { message: "A senha deve ter no mínimo 6 caracteres." }),
  confirmPassword: z.string().min(6, { message: "A confirmação de senha deve ter no mínimo 6 caracteres." }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "As senhas não coincidem.",
  path: ["confirmPassword"],
});

// ==================== TYPES ====================

export type LoginInputs = z.infer<typeof loginSchema>;
export type RegisterInputs = z.infer<typeof registerSchema>;
export type RecoveryInputs = z.infer<typeof recoverySchema>;
export type OtpInputs = z.infer<typeof otpSchema>;
export type UpdatePasswordInputs = z.infer<typeof updatePasswordSchema>;

// ==================== ERROR TRANSLATION ====================

export function translateAuthError(error: any): string {
  if (!error) return "";
  const msg = error.message || error;
  if (typeof msg !== 'string') return "Ocorreu um erro inesperado na autenticação.";

  const lower = msg.toLowerCase();
  
  if (lower.includes("invalid login credentials") || lower.includes("invalid claims") || lower.includes("email not confirmed")) {
    return "E-mail ou senha incorretos, ou e-mail pendente de confirmação.";
  }
  if (lower.includes("user already registered") || lower.includes("already registered")) {
    // Evita enumeração de contas
    return "Se este e-mail for elegível para cadastro, enviamos uma mensagem de confirmação para sua caixa de entrada.";
  }
  if (lower.includes("otp") || lower.includes("token") || lower.includes("expired") || lower.includes("invalid code") || lower.includes("verifyotp")) {
    return "Código de verificação inválido, incorreto ou expirado. Solicite outro.";
  }
  if (lower.includes("rate limit") || lower.includes("too many requests") || lower.includes("limit exceeded")) {
    return "Muitas solicitações em curto período. Por favor, aguarde alguns minutos antes de tentar novamente.";
  }
  if (lower.includes("password is too short") || lower.includes("password should be at least")) {
    return "A senha deve ter no mínimo 6 caracteres.";
  }

  return "Não foi possível concluir a operação de autenticação. Tente novamente mais tarde.";
}

// ==================== PASSWORD STRENGTH ====================

export interface PasswordStrengthResult {
  score: 1 | 2 | 3 | 4;
  label: 'Fraca' | 'Razoável' | 'Boa' | 'Forte';
  color: string;
}

export function calculatePasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return { score: 1, label: 'Fraca', color: 'bg-red-500/20 text-red-400 border-red-500/30' };
  }

  let score = 0;
  
  // Critérios básicos
  if (password.length >= 6) score += 1;
  if (password.length >= 10) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  // Padrões sequenciais ou repetidos
  const isSequentialNumbers = /123|234|345|456|567|678|789|890/.test(password);
  const isRepeating = /(.)\1\1/.test(password); // ex: aaa
  
  // Lista de senhas muito comuns
  const commonPasswords = ['123456', '12345678', 'password', 'senha123', 'mudar123', 'admin123', 'workana', 'workana123'];
  const isCommon = commonPasswords.includes(password.toLowerCase());

  if (isCommon || isRepeating || (password.length < 6)) {
    return { score: 1, label: 'Fraca', color: 'bg-red-500/20 text-red-400 border-red-500/30' };
  }

  if (isSequentialNumbers && score > 2) {
    score -= 1;
  }

  // Mapeamento para 1-4
  const finalScore = Math.min(Math.max(Math.ceil(score / 1.5), 1), 4) as 1 | 2 | 3 | 4;
  
  const labels: Record<1 | 2 | 3 | 4, 'Fraca' | 'Razoável' | 'Boa' | 'Forte'> = {
    1: 'Fraca',
    2: 'Razoável',
    3: 'Boa',
    4: 'Forte'
  };

  const colors: Record<1 | 2 | 3 | 4, string> = {
    1: 'bg-red-500/20 text-red-400 border-red-500/30',
    2: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    3: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    4: 'bg-green-500/20 text-green-400 border-green-500/30'
  };

  return {
    score: finalScore,
    label: labels[finalScore],
    color: colors[finalScore]
  };
}
