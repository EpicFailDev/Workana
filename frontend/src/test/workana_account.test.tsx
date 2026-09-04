import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkanaAccountTab } from '../components/settings/WorkanaAccountTab';
import { ToastProvider } from '../context/ToastContext';
import type { CredentialsStatus, SessionHealthResponse } from '../services/api';

const defaultCredentials: CredentialsStatus = {
  configured: true,
  email: 'gui***@gmail.com',
  login_method: 'google',
  session_ready: true,
};

const defaultHealth: SessionHealthResponse = {
  valid: true,
  status: 'blocked_waf',
  message:
    'Cloudflare WAF bloqueou a sondagem HTTP direta. A automação usa o navegador Playwright com emulação humana.',
  cookies_count: 53,
  has_cloudflare_clearance: true,
  account_email: 'gui***@gmail.com',
};

const renderComponent = (props: Partial<React.ComponentProps<typeof WorkanaAccountTab>> = {}) => {
  const defaultProps = {
    credentials: defaultCredentials,
    newCredentials: { email: '', password: '' },
    setNewCredentials: vi.fn(),
    showPassword: false,
    setShowPassword: vi.fn(),
    isSaving: false,
    handleSaveCredentials: vi.fn(),
    handleGoogleLogin: vi.fn(),
    isGoogleLogging: false,
    importMode: false,
    setImportMode: vi.fn(),
    sessionJson: '',
    setSessionJson: vi.fn(),
    accountEmail: '',
    setAccountEmail: vi.fn(),
    isImporting: false,
    handleImportSession: vi.fn(),
    handleFileUpload: vi.fn(),
    handleDisconnect: vi.fn(),
    setCredentials: vi.fn(),
    sessionHealth: defaultHealth,
    handleTestSessionHealth: vi.fn(),
    isCheckingHealth: false,
    ...props,
  };

  return {
    ...render(
      <ToastProvider>
        <WorkanaAccountTab {...defaultProps} />
      </ToastProvider>
    ),
    props: defaultProps,
  };
};

describe('WorkanaAccountTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders connection telemetry and status badge when connected via Google', () => {
    renderComponent();

    // Check status badge
    expect(screen.getByText(/Conectado via Google como gui\*\*\*@gmail\.com/i)).toBeInTheDocument();

    // Check telemetry indicators
    expect(screen.getByText(/53 cookies/i)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare Clearance/i)).toBeInTheDocument();
    expect(screen.getByText(/Desafio Cloudflare \(WAF\)/i)).toBeInTheDocument();

    // Action buttons
    expect(
      screen.getByRole('button', { name: /Renovar \/ Injetar Cookies|Ocultar Atualizador/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Refazer Login Google/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Testar Conexão/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Desconectar/i })).toBeInTheDocument();
  });

  it('calls handleTestSessionHealth when clicking Testar Conexão', () => {
    const handleTestSessionHealth = vi.fn();
    renderComponent({ handleTestSessionHealth });

    const testBtn = screen.getByRole('button', { name: /Testar Conexão/i });
    fireEvent.click(testBtn);

    expect(handleTestSessionHealth).toHaveBeenCalledTimes(1);
  });

  it('toggles session updater box and displays 3 modes', () => {
    const { props } = renderComponent({
      sessionHealth: {
        ...defaultHealth,
        status: 'healthy',
      },
    });

    // Toggle updater
    const toggleBtn = screen.getByRole('button', { name: /Renovar \/ Injetar Cookies/i });
    fireEvent.click(toggleBtn);

    // Modes should be available
    expect(screen.getByText('Colar Cookies')).toBeInTheDocument();
    expect(screen.getByText('Abrir Navegador')).toBeInTheDocument();
    expect(screen.getByText('Importar Arquivo')).toBeInTheDocument();
  });

  it('handles clipboard paste action in Colar Cookies mode', async () => {
    const mockClipboardText = '[{"name":"cf_clearance","value":"xyz"}]';
    Object.assign(navigator, {
      clipboard: {
        readText: vi.fn().mockResolvedValue(mockClipboardText),
      },
    });

    const setSessionJson = vi.fn();
    renderComponent({
      importMode: true,
      setSessionJson,
    });

    const clipboardBtn = screen.getByRole('button', { name: /Colar do Clipboard/i });
    fireEvent.click(clipboardBtn);

    await waitFor(() => {
      expect(navigator.clipboard.readText).toHaveBeenCalled();
      expect(setSessionJson).toHaveBeenCalledWith(mockClipboardText);
    });
  });

  it('renders disconnected state with cookie updater and email fallback when not configured', () => {
    renderComponent({
      credentials: { configured: false, email: null },
      sessionHealth: null,
    });

    expect(screen.getByText(/● Desconectado/i)).toBeInTheDocument();
    expect(screen.getByText(/Conectar via Sessão do Navegador/i)).toBeInTheDocument();
    expect(screen.getByText(/ou conecte usando email e senha/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Conectar Conta com Senha/i })).toBeInTheDocument();
  });
});
