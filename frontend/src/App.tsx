import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import BottomNavigation from './components/BottomNavigation'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import History from './pages/History'
import Settings from './pages/Settings'
const Templates = React.lazy(() => import('./pages/Templates'))
import Profile from './pages/Profile'
import Auth from './pages/Auth'
import Recuperar from './pages/Recuperar'
import VerificarOtp from './pages/VerificarOtp'
import NovaSenha from './pages/NovaSenha'
import AuthCallback from './pages/AuthCallback'
import Termos from './pages/Termos'
import Privacidade from './pages/Privacidade'
import { useAuth } from './context/AuthContext'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                width: '100vw',
                background: '#06070d',
                color: '#6366f1',
                fontFamily: 'monospace',
                gap: '16px'
            }}>
                <div style={{
                    width: '32px',
                    height: '32px',
                    border: '3px solid rgba(99, 102, 241, 0.2)',
                    borderRadius: '50%',
                    borderTopColor: '#6366f1',
                    animation: 'spin 1s linear infinite'
                }}></div>
                <style>{`
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                `}</style>
                <span>ESTABELECENDO CANAL SEGURO...</span>
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
                                <Routes>
                                    <Route path="/" element={<Dashboard />} />
                                    <Route path="/projects" element={<Projects />} />
                                    <Route path="/history" element={<History />} />
                                    <Route path="/settings" element={<Settings />} />
                                    <Route 
                                        path="/templates" 
                                        element={
                                            <React.Suspense fallback={
                                                <div style={{
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    height: '100%',
                                                    minHeight: '400px',
                                                    color: '#6366f1',
                                                    fontFamily: 'monospace',
                                                    gap: '16px'
                                                }}>
                                                    <div style={{
                                                        width: '24px',
                                                        height: '24px',
                                                        border: '2px solid rgba(99, 102, 241, 0.2)',
                                                        borderRadius: '50%',
                                                        borderTopColor: '#6366f1',
                                                        animation: 'spin 1s linear infinite'
                                                    }}></div>
                                                    <span>CARREGANDO BLUEPRINT...</span>
                                                </div>
                                            }>
                                                <Templates />
                                            </React.Suspense>
                                        } 
                                    />
                                    <Route path="/profile" element={<Profile />} />
                                    {/* Fallback */}
                                    <Route path="*" element={<Navigate to="/" replace />} />
                                </Routes>
                            </main>

                            <BottomNavigation />
                        </div>
                    </ProtectedRoute>
                }
            />
        </Routes>
    )
}

export default App

