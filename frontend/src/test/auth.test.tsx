import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

// 1. Declare the mocks. Vitest hoists this block automatically.
vi.mock('../integrations/supabase/client', () => {
  return {
    supabase: {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: vi.fn(() => ({
          data: {
            subscription: {
              unsubscribe: vi.fn(),
            },
          },
        })),
        signInWithPassword: vi.fn().mockResolvedValue({ data: { user: {}, session: {} }, error: null }),
        signUp: vi.fn().mockResolvedValue({ data: { user: {}, session: {} }, error: null }),
        signInWithOAuth: vi.fn().mockResolvedValue({ data: { provider: 'google', url: 'https://google.com' }, error: null }),
        signOut: vi.fn().mockResolvedValue({ error: null }),
        resetPasswordForEmail: vi.fn().mockResolvedValue({ data: {}, error: null }),
        verifyOtp: vi.fn().mockResolvedValue({ data: { session: {} }, error: null }),
        updateUser: vi.fn().mockResolvedValue({ data: { user: {} }, error: null }),
        exchangeCodeForSession: vi.fn().mockResolvedValue({ data: { session: {} }, error: null }),
      },
    }
  };
});

// Import the mocked supabase client
import { supabase } from '../integrations/supabase/client';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../context/ToastContext';

// Import pages
import Login from '../pages/Login';
import Cadastro from '../pages/Cadastro';
import Recuperar from '../pages/Recuperar';
import VerificarOtp from '../pages/VerificarOtp';
import NovaSenha from '../pages/NovaSenha';
import AuthCallback from '../pages/AuthCallback';
import { calculatePasswordStrength, translateAuthError } from '../services/authService';

// Helper to render with routing, context providers and toasted notifications
const renderWithProviders = (ui: React.ReactElement, initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <ToastProvider>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </ToastProvider>
    </MemoryRouter>
  );
};

// Cast to easily type mock methods in assertions
const mockAuth = supabase.auth as any;

describe('Autenticação e Registro', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();

    // Reset default mock returns before each test
    mockAuth.getSession.mockResolvedValue({ data: { session: null }, error: null });
    mockAuth.signInWithPassword.mockResolvedValue({ data: { user: {}, session: {} }, error: null });
    mockAuth.signUp.mockResolvedValue({ data: { user: {}, session: {} }, error: null });
    mockAuth.signInWithOAuth.mockResolvedValue({ data: { provider: 'google', url: 'https://google.com' }, error: null });
    mockAuth.signOut.mockResolvedValue({ error: null });
    mockAuth.resetPasswordForEmail.mockResolvedValue({ data: {}, error: null });
    mockAuth.verifyOtp.mockResolvedValue({ data: { session: {} }, error: null });
    mockAuth.updateUser.mockResolvedValue({ data: { user: {} }, error: null });
    mockAuth.exchangeCodeForSession.mockResolvedValue({ data: { session: {} }, error: null });
  });

  describe('Cálculos de Força de Senha e Tratamento de Erros', () => {
    it('deve avaliar a força da senha corretamente', () => {
      // Fraca
      expect(calculatePasswordStrength('123').label).toBe('Fraca');
      expect(calculatePasswordStrength('workana').label).toBe('Fraca');
      expect(calculatePasswordStrength('aaaaaa').label).toBe('Fraca');
      
      // Razoável/Boa/Forte
      expect(calculatePasswordStrength('Aa12345').label).toBe('Razoável');
      expect(calculatePasswordStrength('Aa12345!').label).toBe('Boa');
      expect(calculatePasswordStrength('SenhaForteComplexa123!').label).toBe('Forte');
    });

    it('deve traduzir erros do Supabase de forma amigável e segura em português', () => {
      expect(translateAuthError({ message: 'Invalid login credentials' })).toContain('incorretos');
      expect(translateAuthError({ message: 'User already registered' })).toContain('enviamos uma mensagem');
      expect(translateAuthError({ message: 'rate limit exceeded' })).toContain('Muitas solicitações');
      expect(translateAuthError({ message: 'database query failed' })).toContain('Não foi possível concluir');
    });
  });

  describe('Tela de Login', () => {
    it('deve renderizar campos de login e botão Google', () => {
      renderWithProviders(<Login />, '/auth/login');
      
      expect(screen.getByPlaceholderText(/seu-email@dominio.com/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Sua senha secreta/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Entrar$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Entrar com Google/i })).toBeInTheDocument();
    });

    it('deve submeter o formulário com dados válidos e habilitar Lembrar-me', async () => {
      mockAuth.signInWithPassword.mockResolvedValue({
        data: { user: { id: 'user-123' }, session: { access_token: 'token-123' } },
        error: null,
      });

      renderWithProviders(<Login />, '/auth/login');

      const emailInput = screen.getByPlaceholderText(/seu-email@dominio.com/i);
      const passwordInput = screen.getByPlaceholderText(/Sua senha secreta/i);
      const rememberMe = screen.getByRole('checkbox', { name: /Lembrar-me/i });
      const loginButton = screen.getByRole('button', { name: /^Entrar$/i });

      fireEvent.change(emailInput, { target: { value: 'test@empresa.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      // Clica em Lembrar-me
      fireEvent.click(rememberMe);

      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(mockAuth.signInWithPassword).toHaveBeenCalledWith({
          email: 'test@empresa.com',
          password: 'password123',
        });
        expect(localStorage.getItem('auth_remember_me')).toBe('true');
      });
    });

    it('não deve bloquear senhas legadas pequenas na tela de login', async () => {
      mockAuth.signInWithPassword.mockResolvedValue({
        data: { user: { id: 'legacy-123' }, session: { access_token: 'legacy-token' } },
        error: null,
      });

      renderWithProviders(<Login />, '/auth/login');

      fireEvent.change(screen.getByPlaceholderText(/seu-email@dominio.com/i), { target: { value: 'legacy@empresa.com' } });
      fireEvent.change(screen.getByPlaceholderText(/Sua senha secreta/i), { target: { value: '123' } }); // Senha curta
      fireEvent.click(screen.getByRole('button', { name: /^Entrar$/i }));

      await waitFor(() => {
        expect(mockAuth.signInWithPassword).toHaveBeenCalledWith({
          email: 'legacy@empresa.com',
          password: '123',
        });
      });
    });
  });

  describe('Tela de Cadastro', () => {
    it('deve exibir erros de validação ao enviar formulário vazio', async () => {
      renderWithProviders(<Cadastro />, '/auth/cadastro');

      fireEvent.click(screen.getByRole('button', { name: /Criar minha Conta/i }));

      await waitFor(() => {
        expect(screen.getByText('Por favor, insira um e-mail válido.')).toBeInTheDocument();
        expect(screen.getByText('A senha deve ter no mínimo 6 caracteres.')).toBeInTheDocument();
        expect(screen.getByText('Você precisa aceitar os Termos de Serviço e Política de Privacidade.')).toBeInTheDocument();
      });
    });

    it('deve falhar se confirmação de senha for diferente', async () => {
      renderWithProviders(<Cadastro />, '/auth/cadastro');

      fireEvent.change(screen.getByPlaceholderText(/seu-email@dominio.com/i), { target: { value: 'cadastro@empresa.com' } });
      fireEvent.change(screen.getByPlaceholderText(/Crie uma senha forte/i), { target: { value: 'senha123' } });
      fireEvent.change(screen.getByPlaceholderText(/Repita a mesma senha/i), { target: { value: 'senha999' } });
      
      const acceptCheckbox = screen.getByRole('checkbox');
      fireEvent.click(acceptCheckbox);
      
      fireEvent.click(screen.getByRole('button', { name: /Criar minha Conta/i }));

      await waitFor(() => {
        expect(screen.getByText('As senhas não coincidem.')).toBeInTheDocument();
      });
    });

    it('deve realizar cadastro com sucesso e exibir tela de confirmação de e-mail pendente', async () => {
      mockAuth.signUp.mockResolvedValue({
        data: { user: { id: 'new-user', email: 'novo@empresa.com' }, session: null }, // session null significa e-mail pendente
        error: null,
      });

      renderWithProviders(<Cadastro />, '/auth/cadastro');

      fireEvent.change(screen.getByPlaceholderText(/seu-email@dominio.com/i), { target: { value: 'novo@empresa.com' } });
      fireEvent.change(screen.getByPlaceholderText(/Crie uma senha forte/i), { target: { value: 'novasenha123' } });
      fireEvent.change(screen.getByPlaceholderText(/Repita a mesma senha/i), { target: { value: 'novasenha123' } });
      
      const acceptCheckbox = screen.getByRole('checkbox');
      fireEvent.click(acceptCheckbox);
      
      fireEvent.click(screen.getByRole('button', { name: /Criar minha Conta/i }));

      await waitFor(() => {
        expect(screen.getByText(/Cadastro recebido! Enviamos um link de confirmação/i)).toBeInTheDocument();
      });
    });
  });

  describe('Fluxo de Recuperação por OTP', () => {
    it('deve solicitar código de redefinição via e-mail', async () => {
      mockAuth.resetPasswordForEmail.mockResolvedValue({ data: {}, error: null });

      renderWithProviders(<Recuperar />, '/auth/recuperar');

      fireEvent.change(screen.getByPlaceholderText(/seu-email@dominio.com/i), { target: { value: 'recupera@empresa.com' } });
      fireEvent.click(screen.getByRole('button', { name: /Enviar Código OTP/i }));

      await waitFor(() => {
        expect(mockAuth.resetPasswordForEmail).toHaveBeenCalledWith('recupera@empresa.com', {
          redirectTo: expect.stringContaining('/auth/verificar-otp'),
        });
      });
    });

    it('deve renderizar a tela de verificação de OTP e suportar preenchimento dos 6 campos', async () => {
      mockAuth.verifyOtp.mockResolvedValue({
        data: { session: { access_token: 'temp-session' } },
        error: null,
      });

      renderWithProviders(<VerificarOtp />, '/auth/verificar-otp?email=teste@empresa.com');

      const inputs = screen.getAllByRole('textbox');
      expect(inputs.length).toBe(6);

      // Digita um número em cada input
      fireEvent.change(inputs[0], { target: { value: '1' } });
      fireEvent.change(inputs[1], { target: { value: '2' } });
      fireEvent.change(inputs[2], { target: { value: '3' } });
      fireEvent.change(inputs[3], { target: { value: '4' } });
      fireEvent.change(inputs[4], { target: { value: '5' } });
      fireEvent.change(inputs[5], { target: { value: '6' } });

      await waitFor(() => {
        expect(mockAuth.verifyOtp).toHaveBeenCalledWith({
          email: 'teste@empresa.com',
          token: '123456',
          type: 'recovery',
        });
      });
    });

    it('deve suportar colagem de código de 6 dígitos no primeiro input de OTP', async () => {
      mockAuth.verifyOtp.mockResolvedValue({
        data: { session: { access_token: 'temp-session' } },
        error: null,
      });

      renderWithProviders(<VerificarOtp />, '/auth/verificar-otp?email=teste@empresa.com');

      const inputs = screen.getAllByRole('textbox');

      // Simula evento de paste
      const pasteEvent = {
        clipboardData: {
          getData: () => '987654',
        },
        preventDefault: vi.fn(),
      };

      fireEvent.paste(inputs[0], pasteEvent);

      await waitFor(() => {
        expect(mockAuth.verifyOtp).toHaveBeenCalledWith({
          email: 'teste@empresa.com',
          token: '987654',
          type: 'recovery',
        });
      });
    });
  });

  describe('Google OAuth e Callback', () => {
    it('deve iniciar login Google com redirectTo correto e PKCE implícito do Supabase', async () => {
      mockAuth.signInWithOAuth.mockResolvedValue({ data: { provider: 'google', url: 'https://google.com' }, error: null });

      renderWithProviders(<Login />, '/auth/login');
      
      fireEvent.click(screen.getByRole('button', { name: /Entrar com Google/i }));

      await waitFor(() => {
        expect(mockAuth.signInWithOAuth).toHaveBeenCalledWith({
          provider: 'google',
          options: {
            redirectTo: expect.stringContaining('/auth/callback'),
            queryParams: expect.any(Object),
          },
        });
      });
    });

    it('deve processar callback com código de autorização e realizar redirecionamento seguro', async () => {
      mockAuth.exchangeCodeForSession.mockResolvedValue({
        data: { session: { user: { id: 'google-user' } } },
        error: null,
      });

      renderWithProviders(<AuthCallback />, '/auth/callback?code=abc-auth-code');

      await waitFor(() => {
        expect(mockAuth.exchangeCodeForSession).toHaveBeenCalledWith('abc-auth-code');
      });
    });
  });
});
