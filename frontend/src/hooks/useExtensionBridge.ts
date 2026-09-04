import { useState, useEffect, useCallback } from 'react';

export interface ExtensionInfo {
  version: string;
  active: boolean;
  installed: boolean;
}

export interface ExtensionDispatchResult {
  success: boolean;
  message: string;
  redirect_url?: string;
  task_id?: string;
}

export interface ExtensionSyncResult {
  success: boolean;
  message: string;
  count?: number;
}

export function useExtensionBridge() {
  const [isExtensionActive, setIsExtensionActive] = useState<boolean>(false);
  const [extensionVersion, setExtensionVersion] = useState<string | null>(null);
  const [isSendingViaExtension, setIsSendingViaExtension] = useState<boolean>(false);

  // Detecção da extensão no carregamento e via listener de custom events e handshake contínuo
  useEffect(() => {
    const checkGlobalFlag = () => {
      const globalExt = (window as any).__WORKANA_EXTENSION__;
      if (globalExt && globalExt.active) {
        setIsExtensionActive(true);
        setExtensionVersion(globalExt.version || '2.0.0');
        return true;
      }
      return false;
    };

    checkGlobalFlag();

    // Escuta evento customizado disparado pelo content_accelerator.js
    const handleDetection = (e: any) => {
      if (e.detail) {
        setIsExtensionActive(true);
        setExtensionVersion(e.detail.version || '2.0.0');
      }
    };

    window.addEventListener('workana-extension-detected', handleDetection);

    // Handshake bidirecional via postMessage
    const handleResponse = (event: MessageEvent) => {
      if (
        event.source === window &&
        event.data &&
        event.data.source === 'WORKANA_EXTENSION_BRIDGE' &&
        (event.data.type === 'CHECK_EXTENSION_RES' || event.data.requestId?.startsWith('ping_'))
      ) {
        if (event.data.success && event.data.data) {
          setIsExtensionActive(true);
          setExtensionVersion(event.data.data.version || '2.0.0');
        }
      }
    };

    window.addEventListener('message', handleResponse);

    const pingExtension = () => {
      if (checkGlobalFlag()) return;
      window.postMessage(
        {
          source: 'WORKANA_ACCELERATOR_APP',
          type: 'CHECK_EXTENSION',
          requestId: `ping_${Date.now()}`,
        },
        '*'
      );
    };

    pingExtension();
    const interval = setInterval(pingExtension, 1500);

    return () => {
      window.removeEventListener('workana-extension-detected', handleDetection);
      window.removeEventListener('message', handleResponse);
      clearInterval(interval);
    };
  }, []);

  // Envio direto via ponte com latência zero (0ms)
  const sendViaExtension = useCallback(
    async (proposalPayload: {
      project_id: string;
      budget: number;
      custom_message: string;
      deadline_days?: number;
      template_id?: any;
    }): Promise<ExtensionDispatchResult> => {
      setIsSendingViaExtension(true);
      const requestId = `dispatch_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          window.removeEventListener('message', handleMessage);
          setIsSendingViaExtension(false);
          resolve({
            success: false,
            message: 'Tempo limite excedido aguardando resposta da extensão.',
          });
        }, 45000);

        const handleMessage = (event: MessageEvent) => {
          if (
            event.source === window &&
            event.data &&
            event.data.source === 'WORKANA_EXTENSION_BRIDGE' &&
            event.data.requestId === requestId
          ) {
            clearTimeout(timeout);
            window.removeEventListener('message', handleMessage);
            setIsSendingViaExtension(false);
            const data = event.data.data || {};
            resolve({
              success: !!event.data.success && !!data.success,
              message:
                data.message || (event.data.success ? 'Proposta enviada!' : 'Falha no envio.'),
              redirect_url: data.redirect_url,
              task_id: data.task_id,
            });
          }
        };

        window.addEventListener('message', handleMessage);

        window.postMessage(
          {
            source: 'WORKANA_ACCELERATOR_APP',
            type: 'DISPATCH_PROPOSAL_INSTANT',
            requestId,
            payload: proposalPayload,
          },
          '*'
        );
      });
    },
    []
  );

  const [isSyncingCookies, setIsSyncingCookies] = useState<boolean>(false);

  // Sincronização forçada imediata de cookies via extensão (0-click bridge)
  const syncCookiesViaExtension = useCallback(async (): Promise<ExtensionSyncResult> => {
    setIsSyncingCookies(true);
    const requestId = `sync_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        window.removeEventListener('message', handleSyncResponse);
        setIsSyncingCookies(false);
        resolve({
          success: false,
          message: 'Tempo limite excedido aguardando resposta da extensão.',
        });
      }, 10000);

      const handleSyncResponse = (event: MessageEvent) => {
        if (
          event.source === window &&
          event.data &&
          event.data.source === 'WORKANA_EXTENSION_BRIDGE' &&
          event.data.requestId === requestId
        ) {
          clearTimeout(timeout);
          window.removeEventListener('message', handleSyncResponse);
          setIsSyncingCookies(false);
          const data = event.data.data || {};
          const isOk = !!event.data.success && data.success !== false;
          resolve({
            success: isOk,
            message:
              data.message ||
              (isOk ? 'Cookies sincronizados com sucesso!' : 'Falha na sincronização.'),
            count: data.count,
          });
        }
      };

      window.addEventListener('message', handleSyncResponse);

      window.postMessage(
        {
          source: 'WORKANA_ACCELERATOR_APP',
          type: 'SYNC_COOKIES_NOW',
          requestId,
        },
        '*'
      );
    });
  }, []);

  return {
    isExtensionActive,
    extensionVersion,
    isSendingViaExtension,
    sendViaExtension,
    isSyncingCookies,
    syncCookiesViaExtension,
  };
}
