import React, { Suspense, lazy, useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import BottomNavigation from './components/BottomNavigation';
import AppHeader from './components/AppHeader';
import CommandPalette from './components/CommandPalette';
import InvestmentCalculatorModal from './components/InvestmentCalculatorModal';
import SystemHealthModal from './components/SystemHealthModal';
import { useAuth } from './context/AuthContext';
import { useToast } from './context/ToastContext';
import { api } from './services/api';

// Lazy-loaded pages para otimização de bundle e code-splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Projects = lazy(() => import('./pages/Projects'));
const Batches = lazy(() => import('./pages/Batches'));
const History = lazy(() => import('./pages/History'));
const Settings = lazy(() => import('./pages/Settings'));
const Templates = lazy(() => import('./pages/Templates'));
const Profile = lazy(() => import('./pages/Profile'));
const Auth = lazy(() => import('./pages/Auth'));
const Recuperar = lazy(() => import('./pages/Recuperar'));
const VerificarOtp = lazy(() => import('./pages/VerificarOtp'));
const NovaSenha = lazy(() => import('./pages/NovaSenha'));
const AuthCallback = lazy(() => import('./pages/AuthCallback'));
const Termos = lazy(() => import('./pages/Termos'));
const Privacidade = lazy(() => import('./pages/Privacidade'));

function PageFallback({ label = 'CARREGANDO...' }: { label?: string }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        minHeight: '300px',
        color: '#6366f1',
        fontFamily: 'monospace',
        gap: '16px',
      }}
    >
      <div
        style={{
          width: '28px',
          height: '28px',
          border: '3px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '50%',
          borderTopColor: '#6366f1',
          animation: 'spin 0.8s linear infinite',
        }}
      ></div>
      <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
      <span style={{ fontSize: '12px', letterSpacing: '1px' }}>{label}</span>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          width: '100vw',
          background: '#06070d',
          color: '#6366f1',
          fontFamily: 'monospace',
          gap: '16px',
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            border: '3px solid rgba(99, 102, 241, 0.2)',
            borderRadius: '50%',
            borderTopColor: '#6366f1',
            animation: 'spin 1s linear infinite',
          }}
        ></div>
        <style>{`
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                `}</style>
        <span>CARREGANDO...</span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  return <>{children}</>;
}

function AppLayout() {
  const { toast } = useToast();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);
  const [isHealthOpen, setIsHealthOpen] = useState(false);
  const [isSyncingCatalog, setIsSyncingCatalog] = useState(false);

  // Atalho global Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleRefreshCatalog = useCallback(async () => {
    setIsSyncingCatalog(true);
    try {
      const res = await api.refreshCatalog();
      if (res.success) {
        toast.success(
          res.message ||
            `Catálogo sincronizado! +${res.upserted || 0} novas oportunidades coletadas.`
        );
      } else {
        toast.error(res.message || 'Falha ao sincronizar catálogo.');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao comunicar com o servidor.');
    } finally {
      setIsSyncingCatalog(false);
    }
  }, [toast]);

  const handleDownloadCsv = useCallback(async () => {
    try {
      toast.info('Iniciando download do catálogo em CSV...');
      await api.downloadCatalogCsv(false);
      toast.success('Download do catálogo concluído!');
    } catch (err: any) {
      toast.error(err?.message || 'Erro ao exportar catálogo.');
    }
  }, [toast]);

  return (
    <div className="app-layout">
      <AppHeader
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenCalculator={() => setIsCalculatorOpen(true)}
        onOpenHealth={() => setIsHealthOpen(true)}
        onRefreshCatalog={handleRefreshCatalog}
        isSyncingCatalog={isSyncingCatalog}
      />

      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onOpenSearch={() => setIsSearchOpen(true)}
      />

      <main className="main-content">
        <Suspense fallback={<PageFallback label="CARREGANDO MÓDULO..." />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/batches" element={<Batches />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/profile" element={<Profile />} />
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>

      <BottomNavigation />

      {/* Modais Globais */}
      <CommandPalette
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onOpenCalculator={() => setIsCalculatorOpen(true)}
        onOpenHealth={() => setIsHealthOpen(true)}
        onRefreshCatalog={handleRefreshCatalog}
        onDownloadCsv={handleDownloadCsv}
      />

      <InvestmentCalculatorModal
        isOpen={isCalculatorOpen}
        onClose={() => setIsCalculatorOpen(false)}
      />

      <SystemHealthModal isOpen={isHealthOpen} onClose={() => setIsHealthOpen(false)} />
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<PageFallback label="INICIANDO APLICAÇÃO..." />}>
      <Routes>
        {/* Rotas públicas de autenticação */}
        <Route path="/auth" element={<Navigate to="/auth/login" replace />} />
        <Route path="/auth/login" element={<Auth />} />
        <Route path="/auth/cadastro" element={<Auth />} />
        <Route path="/auth/recuperar" element={<Recuperar />} />
        <Route path="/auth/verificar-otp" element={<VerificarOtp />} />
        <Route path="/auth/nova-senha" element={<NovaSenha />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/termos" element={<Termos />} />
        <Route path="/privacidade" element={<Privacidade />} />

        {/* Rotas protegidas */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default App;
