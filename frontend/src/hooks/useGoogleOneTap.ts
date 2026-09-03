import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useNavigate } from 'react-router-dom';
import { translateAuthError } from '../services/authService';

interface UseGoogleOneTapOptions {
  next?: string;
  rememberMe?: boolean;
}

export function useGoogleOneTap(options?: UseGoogleOneTapOptions) {
  const { signInWithGoogleIdToken } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const next = options?.next || '/';
  const rememberMe = options?.rememberMe ?? true;

  useEffect(() => {
    const googleClientId =
      import.meta.env.VITE_GOOGLE_CLIENT_ID ||
      '155701464959-iba50ksnc18jub8qvtn9ipp721umddch.apps.googleusercontent.com';

    if (typeof window === 'undefined') return;

    let isSubscribed = true;

    const initializeGoogleOneTap = () => {
      if (!window.google?.accounts?.id || !isSubscribed) return;

      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response) => {
            if (response.credential && isSubscribed) {
              try {
                const res = await signInWithGoogleIdToken(response.credential, rememberMe, next);
                if (res.error) {
                  toast.error(translateAuthError(res.error), 'Erro no Login com Google');
                } else {
                  toast.success('Login com Google realizado com sucesso!', 'Bem-vindo');
                  navigate(next);
                }
              } catch {
                toast.error('Falha ao autenticar com Google One Tap.', 'Erro');
              }
            }
          },
          auto_select: false,
          cancel_on_tap_outside: true,
        });

        window.google.accounts.id.prompt();
      } catch (err) {
        console.debug('Google One Tap não pôde ser inicializado:', err);
      }
    };

    if (window.google?.accounts?.id) {
      initializeGoogleOneTap();
    } else {
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          initializeGoogleOneTap();
        }
      }, 200);

      const timeout = setTimeout(() => {
        clearInterval(interval);
      }, 5000);

      return () => {
        isSubscribed = false;
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }

    return () => {
      isSubscribed = false;
    };
  }, [navigate, next, rememberMe, signInWithGoogleIdToken, toast]);
}
