import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import BottomNavigation from './components/BottomNavigation';
import { useAuth } from './context/AuthContext';

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
              <div className="app-layout">
                <Sidebar isOpen={false} onClose={() => {}} />

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
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default App;
