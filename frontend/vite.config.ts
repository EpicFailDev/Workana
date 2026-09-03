/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react-swc';
import { fileURLToPath, URL } from 'url';

export default defineConfig(({ mode }) => {
  // Carrega as variáveis de ambiente com base no diretório atual
  const env = loadEnv(mode, process.cwd(), '');

  // Validar variáveis críticas do Supabase durante o build em produção
  const isProdBuild = mode === 'production' || process.env.NODE_ENV === 'production';
  if (isProdBuild) {
    if (!env.VITE_SUPABASE_URL) {
      throw new Error(
        '❌ ERRO NO BUILD: A variável de ambiente VITE_SUPABASE_URL não está definida!'
      );
    }
    if (!env.VITE_SUPABASE_PUBLISHABLE_KEY) {
      throw new Error(
        '❌ ERRO NO BUILD: A variável de ambiente VITE_SUPABASE_PUBLISHABLE_KEY não está definida!'
      );
    }
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      port: 8080,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (
                id.includes('react-router') ||
                id.includes('react-dom') ||
                id.includes('/react/')
              ) {
                return 'vendor-react';
              }
              if (id.includes('@supabase')) {
                return 'vendor-supabase';
              }
              if (id.includes('framer-motion')) {
                return 'vendor-motion';
              }
              if (id.includes('lucide-react')) {
                return 'vendor-icons';
              }
              if (
                id.includes('@radix-ui') ||
                id.includes('clsx') ||
                id.includes('tailwind-merge')
              ) {
                return 'vendor-ui';
              }
              return 'vendor-libs';
            }
          },
        },
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
    },
  };
});
